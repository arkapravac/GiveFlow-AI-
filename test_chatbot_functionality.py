import sys
import time
from chatbot import ChatBot

def test_chatbot():
    print('Initializing chatbot...')
    bot = ChatBot()
    
    # Wait for model to load
    print('Waiting for model to initialize...')
    time.sleep(5)
    
    print('\nTesting basic response...')
    response = bot.get_response('How do I make a donation?')
    print(f'Response: {response}')
    
    print('\nTesting database query...')
    response = bot.get_response('What is the total donation amount?')
    print(f'Response: {response}')
    
    print('\nTesting pattern matching...')
    response = bot.get_response('What categories of donations are available?')
    print(f'Response: {response}')
    
    print('\nTesting context awareness...')
    response = bot.get_response('Yes, I would like to make a donation')
    print(f'Response: {response}')

if __name__ == '__main__':
    test_chatbot()