import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from database import DonationDatabase
import sqlite3
import pandas as pd

class DonationDataset(Dataset):
    def __init__(self, tokenizer, max_length=512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = self._load_training_data()
        
    def _load_training_data(self):
        # Load chat history and donation data from database
        with sqlite3.connect('donations.db') as conn:
            # Get chat history
            chat_df = pd.read_sql_query(
                'SELECT user_message, bot_response FROM chat_history',
                conn
            )
            
            # Get donation data for context
            donations_df = pd.read_sql_query(
                'SELECT donor_name, amount, category, notes FROM donations',
                conn
            )
            
        # Format data for training
        training_pairs = []
        
        # Add chat history pairs
        for _, row in chat_df.iterrows():
            training_pairs.append({
                'input': f"User: {row['user_message']}\nAssistant:",
                'output': row['bot_response']
            })
            
        # Add donation-specific examples
        for _, row in donations_df.iterrows():
            # Create contextual examples
            training_pairs.append({
                'input': f"User: How do I make a donation like {row['donor_name']}?\nAssistant:",
                'output': f"You can make a donation similar to {row['donor_name']}'s {row['category']} donation by following these steps:\n1. Go to the Donations tab\n2. Fill out the form with your details\n3. Select the {row['category']} category\n4. Enter your desired amount\n5. Add any notes\n6. Click 'Submit Donation'"
            })
            
        return training_pairs
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        # Tokenize input and output
        inputs = self.tokenizer(
            item['input'],
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        with self.tokenizer.as_target_tokenizer():
            labels = self.tokenizer(
                item['output'],
                max_length=self.max_length,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )['input_ids']
        
        return {
            'input_ids': inputs['input_ids'].squeeze(),
            'attention_mask': inputs['attention_mask'].squeeze(),
            'labels': labels.squeeze()
        }

def train_model(model_name='microsoft/DialoGPT-small', output_dir='./trained_model'):
    # Initialize tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    
    # Prepare dataset
    dataset = DonationDataset(tokenizer)
    
    # Define training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-5,
        weight_decay=0.01,
        save_strategy='epoch',
        logging_dir='./logs',
        logging_steps=10,
        fp16=torch.cuda.is_available(),
        remove_unused_columns=False
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        data_collator=lambda data: {'input_ids': torch.stack([f['input_ids'] for f in data]),
                                  'attention_mask': torch.stack([f['attention_mask'] for f in data]),
                                  'labels': torch.stack([f['labels'] for f in data])}
    )
    
    # Train the model
    trainer.train()
    
    # Save the trained model
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    return model, tokenizer

if __name__ == '__main__':
    # Train the model
    print('Starting model training...')
    model, tokenizer = train_model()
    print('Training completed successfully!')