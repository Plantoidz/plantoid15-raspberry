from web3 import Web3, EthereumTesterProvider
from eth_account import Account, messages
from oz_defender.relay import RelayClient, RelayerClient
from dotenv import load_dotenv
import os
import json
from pinata import Pinata

from lib.plantoid.web3_utils import *

load_dotenv()

DEFENDER_API_KEY = os.environ.get("DEFENDER_API_KEY")
DEFENDER_API_SECRET = os.environ.get("DEFENDER_API_SECRET")
SIGNER_PRIVATE_KEY = os.environ.get("SIGNER_PRIVATE_KEY")
PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_JWT = os.environ.get('PINATA_JWT')

def test():

    metadata = None

    metadata_path = os.getcwd()+'/metadata/168.json'

    with open(metadata_path, 'r') as metadata_file:
        metadata = json.load(metadata_file)

    print(metadata_path)

    ipfs_hash = pin_metadata_to_ipfs(metadata_path)
    #ipfs_hash = 'QmR5oZbMUjrMJt6hrerjiCRKauhsXeVfGnmYw2ojVXiakM'

    token_Id = int(metadata['name'])
    plantoid_address = '0x0B60EE161d7b67fa231e9565dAFF65b34553bC6F'
    plantoid_metadata_address = '0x580fdc17a820e3c0d17fbcd1137483c5332fceb6'

    print('ipfs hash is', ipfs_hash)
    print('token id is', token_Id)

    # https://www.herongyang.com/Ethereum/Etheruem-Account-Public-Private-Key-Example.html
    # private_key = '8da4ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f'

    msg_hash, msg_hash_hex, msg_hash_arrayified = get_msg_hash(ipfs_hash, token_Id, plantoid_address)

    sig = create_signer_and_sign(msg_hash, SIGNER_PRIVATE_KEY)
    function_data = encode_function_data(plantoid_address, token_Id, ipfs_hash, sig)

    send_relayer_transaction(plantoid_metadata_address, function_data)

if __name__ == "__main__":
    test()
