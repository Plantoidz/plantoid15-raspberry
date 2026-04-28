import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
key = os.environ.get('INFURA_GOERLI')
print("key prefix:", (key or 'MISSING')[:8])

w3 = Web3(Web3.HTTPProvider(f'https://sepolia.infura.io/v3/{key}'))
print("connected:", w3.is_connected())
print("current sepolia block:", w3.eth.block_number)
