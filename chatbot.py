import google.generativeai as genai
import sqlite3
import json
import os
from database import DonationDatabase
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

class ChatBot:
    def __init__(self):
        # Initialize database connection
        self.db = DonationDatabase()
        
        # Load environment variables
        load_dotenv()
        
        # Initialize Gemini model with API key from environment variable
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Initialize conversation context
        self.conversation_context = []
        self.context_window = 5
    
    def _get_database_context(self) -> str:
        """Get current database context for the model"""
        try:
            total_donations = self.db.get_total_donations()
            recent_donations = self.db.get_recent_donations(5)
            categories = self.db.get_categories()
            
            context = f"Current total donations: ${total_donations:.2f}\n"
            context += "Available categories: " + ", ".join(categories) + "\n"
            context += "Recent donations:\n"
            for donation in recent_donations:
                context += f"- {donation['donor_name']}: ${donation['amount']} ({donation['category']})\n"
            
            return context
        except Exception as e:
            return f"Error getting database context: {str(e)}"
    
    def _format_prompt(self, user_input: str) -> str:
        """Format the prompt with context and user input"""
        system_prompt = (
            "I am Eminem 1.0.0, a helpful donation management assistant created by Arkaprava Chakraborty. "
            "I was trained in Google AI Studio for exactly 1 month. I can help you manage donations, "
            "view statistics, and generate reports. You have access to the following database context:\n"
        )
        
        db_context = self._get_database_context()
        conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" 
                                        for msg in self.conversation_context[-self.context_window:]])
        
        return f"{system_prompt}\n{db_context}\n\nConversation history:\n{conversation_context}\n\nUser: {user_input}"
    
    def _execute_db_command(self, command: Dict[str, Any]) -> str:
        """Execute database commands"""
        try:
            action = command.get("action")
            if action == "add_donation":
                success = self.db.add_donation(
                    donor_name=command["donor_name"],
                    amount=command["amount"],
                    category=command["category"],
                    notes=command.get("notes"),
                    is_recurring=command.get("is_recurring", False),
                    recurring_interval=command.get("recurring_interval"),
                    next_donation_date=command.get("next_donation_date")
                )
                return "Donation added successfully" if success else "Failed to add donation"
            elif action == "update_donation":
                with sqlite3.connect('donations.db') as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if "amount" in command:
                        update_fields.append("amount = ?")
                        params.append(command["amount"])
                    if "category" in command:
                        update_fields.append("category = ?")
                        params.append(command["category"])
                    if "notes" in command:
                        update_fields.append("notes = ?")
                        params.append(command["notes"])
                    if update_fields:
                        params.append(command["donation_id"])
                        cursor.execute(f"UPDATE donations SET {', '.join(update_fields)} WHERE id = ?", params)
                        conn.commit()
                        return "Donation updated successfully" if cursor.rowcount > 0 else "Donation not found"
                    return "No fields to update"
            elif action == "get_donations":
                donations = self.db.get_recent_donations(command.get("limit", 5))
                total_count = len(donations)
                if total_count == 0:
                    return "There are currently no donations in the system."
                response = f"There are {total_count} recent donations. "
                if total_count > 0:
                    response += "Here are the details:\n"
                    for donation in donations:
                        response += f"- {donation['donor_name']} donated ${donation['amount']:.2f} for {donation['category']}\n"
                return response
            elif action == "get_donor_statistics":
                stats = self.db.get_donor_statistics()
                response = f"Total number of donors: {stats['total_donors']}\n"
                response += f"Average donation amount: ${stats['average_donation']:.2f}\n"
                if stats['top_donors']:
                    response += "\nTop donors:\n"
                    for donor in stats['top_donors']:
                        response += f"- {donor['name']}: ${donor['total_amount']:.2f} ({donor['donation_count']} donations)\n"
                return response
            elif action == "get_donor_info":
                donor_name = command.get("donor_name")
                with sqlite3.connect('donations.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT dp.*, SUM(d.amount) as total_donated
                        FROM donor_profiles dp
                        LEFT JOIN donations d ON dp.name = d.donor_name
                        WHERE dp.name = ?
                        GROUP BY dp.id
                    """, (donor_name,))
                    donor = cursor.fetchone()
                    if donor:
                        return f"Donor found: {donor[1]}, Total donations: ${donor[6]:.2f}"
                    return "Donor not found"
            elif action == "add_donor":
                with sqlite3.connect('donations.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO donor_profiles (name, email, phone, address)
                        VALUES (?, ?, ?, ?)
                    """, (command["donor_name"], command.get("email"), command.get("phone"), command.get("address")))
                    conn.commit()
                    return "Donor added successfully"
            elif action == "update_donor":
                with sqlite3.connect('donations.db') as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    for field in ["email", "phone", "address", "preferred_category", "notification_preferences"]:
                        if field in command:
                            update_fields.append(f"{field} = ?")
                            params.append(command[field])
                    if update_fields:
                        params.append(command["donor_name"])
                        cursor.execute(f"UPDATE donor_profiles SET {', '.join(update_fields)} WHERE name = ?", params)
                        conn.commit()
                        return "Donor updated successfully" if cursor.rowcount > 0 else "Donor not found"
                    return "No fields to update"
            elif action == "remove_donor":
                with sqlite3.connect('donations.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM donor_profiles WHERE name = ?", (command["donor_name"],))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return "Donor removed successfully"
                    return "Donor not found"
            return "Unknown database command"
        except Exception as e:
            return f"Error executing database command: {str(e)}"
    
    def _extract_db_command(self, response: str) -> Dict[str, Any]:
        """Extract database commands from the response"""
        try:
            if "[DB_COMMAND]" in response:
                command_start = response.index("[DB_COMMAND]")
                command_end = response.index("[/DB_COMMAND]")
                command_json = response[command_start + 12:command_end].strip()
                return json.loads(command_json)
            return None
        except Exception:
            return None

    def get_response(self, message: str) -> str:
        try:
            # Format prompt with context
            prompt = self._format_prompt(message)
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            # Extract response text and handle potential None
            response_text = response.text if response and hasattr(response, 'text') else ""
            
            if not response_text:
                return "I apologize, but I couldn't generate a response. Please try again."
            
            # Extract and execute any database commands
            db_command = self._extract_db_command(response_text)
            if db_command:
                db_result = self._execute_db_command(db_command)
                response_text = response_text.replace(
                    f"[DB_COMMAND]{json.dumps(db_command)}[/DB_COMMAND]",
                    f"\n{db_result}\n"
                )
            
            # Update conversation context
            self.conversation_context.append({"role": "user", "content": message})
            self.conversation_context.append({"role": "assistant", "content": response_text})
            
            # Trim context if needed
            if len(self.conversation_context) > self.context_window * 2:
                self.conversation_context = self.conversation_context[-self.context_window * 2:]
            
            return response_text.strip()
            
        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return "I apologize, but I'm having trouble processing that. Please try asking about donations, reports, or categories."