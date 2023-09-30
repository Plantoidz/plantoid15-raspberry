from web3 import Web3, EthereumTesterProvider
from eth_account import Account, messages
from oz_defender.relay import RelayClient, RelayerClient
from dotenv import load_dotenv
import os
import json

load_dotenv()

DEFENDER_API_KEY = os.environ.get("DEFENDER_API_KEY")
DEFENDER_API_SECRET = os.environ.get("DEFENDER_API_SECRET")
SIGNER_PRIVATE_KEY = os.environ.get("SIGNER_PRIVATE_KEY")

# from hexbytes import HexBytes

def get_msg_hash(ipfsHash, tokenId, plantoidAddress):


    tokenUri = 'ipfs://' + ipfsHash

    msgHash = Web3.solidity_keccak(
        ['uint256', 'string', 'address'],
        [tokenId, tokenUri, plantoidAddress],
    )

    def arrayify_bytes(hbytes):
        return [hbytes[i] for i in range(len(hbytes))]

    msgHashArrayified = arrayify_bytes(msgHash)
  
    # print('message hash: ', msgHash, msgHash.hex(), msgHashArrayified)
    # print('message hash arrayified: ', msgHashArrayified);

    print('message hash: ', msgHash.hex())
    print('message hash arrayified: ', msgHashArrayified)

    return msgHash, msgHash.hex(), msgHashArrayified

def create_signer_and_sign(msg_hash, private_key):

    # # WRONG!!
    # message = messages.encode_defunct(text=msg_hash_hex)
    # signed_message = Account.sign_message(message, private_key=private_key)
    # print('signed message: ', signed_message.signature.hex())

    # CORRECT!!
    prepared_message = messages.defunct_hash_message(primitive=msg_hash)
    hash_signed_message = Account.signHash(prepared_message, '0x' + private_key)
    sig = hash_signed_message.signature.hex()

    print('signature: ', sig)

    return sig

def encodeFunctionData(plantoid_address, token_Id, ipfs_hash, sig):

    w3 = Web3(EthereumTesterProvider())

    # Define the path to the ABI file
    abi_file_path = '../abis/plantoidMetadata'

    # Load the ABI
    with open(abi_file_path, 'r') as f:
        contract_json = json.load(f)
        abi = contract_json#['abi']

    token_Uri = 'ipfs://' + ipfs_hash

    # print(abi)

    # Get the contract utility using the ABI
    contract = w3.eth.contract(abi=abi)

    # Encode the function call
    data = contract.encodeABI(fn_name="revealMetadata", args=[plantoid_address, token_Id, token_Uri, sig])

    print('encoded function data: ', data)

    return data

def send_relayer_transaction(address, data):

    # https://github.com/franklin-systems/oz-defender/blob/trunk/oz_defender/relay/client.py
    # https://forum.openzeppelin.com/t/what-exactly-is-the-function-of-defenders-relay-when-using-metatransactions/23122/7
    relayer = RelayerClient(api_key=DEFENDER_API_KEY, api_secret=DEFENDER_API_SECRET)

    tx = {
      'to': address,
      'data': data,
      'gasLimit': '100000',
      'schedule': 'fast',
    }

    response = relayer.send_transaction(tx)
    print(response)

def test():

    # w3 = Web3(EthereumTesterProvider())

    ipfs_hash = 'QmR5oZbMUjrMJt6hrerjiCRKauhsXeVfGnmYw2ojVXiakM'
    token_Id = 1
    plantoid_address = '0x0B60EE161d7b67fa231e9565dAFF65b34553bC6F'
    plantoid_metadata_address = '0x'

    # https://www.herongyang.com/Ethereum/Etheruem-Account-Public-Private-Key-Example.html
    # private_key = '8da4ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f'

    msg_hash, msg_hash_hex, msg_hash_arrayified = get_msg_hash(ipfs_hash, token_Id, plantoid_address)

    sig = create_signer_and_sign(msg_hash, SIGNER_PRIVATE_KEY)
    function_data = encodeFunctionData(plantoid_address, token_Id, ipfs_hash, sig)

    # send_relayer_transaction(plantoid_metadata_address, function_data)

if __name__ == "__main__":
    test()
