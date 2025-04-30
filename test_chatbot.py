import os
import sys
sys.path.append(os.getcwd())

from chatbot import ChatBot
import time

def test_chatbot():
    bot = ChatBot()
    
    # Wait for model to load
    print('Waiting for model to initialize...')
    time.sleep(5)
    
    # Test cases
    test_inputs = [
        'How much in total donations?',
        'How do I make a donation?',
        'What categories can I donate to?',
        'Show me recent donations',
        'How do I generate a report?',
        'Can you help me?'
    ]
    
    print('\nTesting ChatBot responses...')
    print('-' * 50)
    
    for input_text in test_inputs:
        print(f'\nInput: {input_text}')
        response = bot.get_response(input_text)
        print(f'Response: {response}')
        print('-' * 50)
        time.sleep(1)  # Add delay between requests

if __name__ == '__main__':
    test_chatbot()