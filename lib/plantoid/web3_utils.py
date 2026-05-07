from web3 import Web3, EthereumTesterProvider
from eth_account import Account, messages
# from oz_defender.relay import RelayClient, RelayerClient
import subprocess
import os
import time
import sys
from pathlib import Path
import json
from dotenv import load_dotenv
from pinata import Pinata

from escpos.printer import Usb
import qrcode
from PIL import Image

from lib.plantoid.indexer_client import IndexerClient, IndexerUnavailable


class Web3Object:
    infura_websock = None
    w3 = None
    plantoid_contract = None
    event_listener = None
    path = None
    min_amount = None
    failsafe = None


load_dotenv()

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_SECRET_KEY")
PINATA_JWT = os.environ.get('PINATA_JWT')
# DEFENDER_API_KEY = os.environ.get("DEFENDER_API_KEY")
# DEFENDER_API_SECRET = os.environ.get("DEFENDER_API_SECRET")
SIGNER_PRIVATE_KEY = os.environ.get("SIGNER_PRIVATE_KEY")
INFURA_API_KEY_MAINNET = os.environ.get("INFURA_MAINNET")
INFURA_API_KEY_GOERLI = os.environ.get("INFURA_GOERLI")
INDEXER_URL = os.environ.get("INDEXER_URL",  "https://plantoidz-brainz.tail98279f.ts.net")  # e.g. http://plantoidz-brainz.local:42069

print(INFURA_API_KEY_MAINNET)

def get_signer_private_key():

    return SIGNER_PRIVATE_KEY

def setup_web3_provider_goerli(config):

        goerli = setup(
            # 'wss://eth-sepolia.g.alchemy.com/v2/m7x4GJTeRCnPV5fkt636eS4OOL9AEuAM',
            # 'wss://eth-goerli.g.alchemy.com/v2/m7x4GJTeRCnPV5fkt636eS4OOL9AEuAM',
            'wss://sepolia.infura.io/ws/v3/'+INFURA_API_KEY_GOERLI,
            config['use_goerli_address'],
            config['use_metadata_address'],
            name="goerli",
            path=config['path'],   ## TODO: THIS IS GONNA FAIL WHEN RUNNING OF SYSTEMD
            plantoid_path=config['plantoid_path'],
            feeding_amount=1000000000000000,  # one line every 0.001 ETH
            reclaim_url="http://" + config['plantoid_number'] + ".plantoid.org",
            failsafe=config['goerli_failsafe'], # this set failsafe = 1 (meaning we should recycle movies)
            start_block=config.get('goerli_start_block', 1),
        ) 
        return goerli

def setup_web3_provider_mainnet(config):

        mainnet = setup(
            #'wss://eth-mainnet.g.alchemy.com/v2/m7x4GJTeRCnPV5fkt636eS4OOL9AEuAM',
            'wss://mainnet.infura.io/ws/v3/'+INFURA_API_KEY_MAINNET,
            config['use_mainnet_address'],
            config['use_metadata_address'],
            name="mainnet",
            path=config['path'],  ## TODO: THIS IS GONNA FAIL WHEN RUNNING OF SYSTEMD
            plantoid_path=config['plantoid_path'],
            feeding_amount=10000000000000000,  # one line every 0.01 ETH)
            reclaim_url="http://" + config['plantoid_number'] + ".plantoid.org",
            failsafe=config['mainnet_failsafe'], # this set failsafe = 0 (meaning we should generate a new movie)
            start_block=config.get('mainnet_start_block', 1),
        ) 
        return mainnet




def setup(
    infura_websock,
    addr,
    metadata_address,
    name="",
    path=None,
    plantoid_path = None,
    feeding_amount=0,
    reclaim_url=None,
    failsafe=0,
    start_block=1,
):
   
    print('trying to connect to name ==== ', name)

    

    # create a web3 object
    network = Web3Object();


    # connect to the infura node
    network.w3 = Web3(Web3.WebsocketProvider(
        infura_websock, 
        websocket_timeout=10000,
        websocket_kwargs={'timeout': 10000}
    ))

    
    # print("DEBUG", network.w3.manager._provider.counter)

    # for k, v in network.w3.manager.items():
    #     print("DEBUG", k, v.__dict__)

    print('w3 is', network.w3)
    print('is connected', network.w3.is_connected())

    # checksum the address
    address = Web3.to_checksum_address(addr)
    print('address is', address)

    # get the balance of the address
    # eth_balance_wei = network.w3.eth.get_balance(address)
    # eth_balance = network.w3.from_wei(eth_balance_wei, 'ether')
    # print('eth balance:', eth_balance)
    
    abifile = open(path + '/abi', 'r')
    o = abifile.read()
    abi = o.replace('\n', '')
    # print(abi)
    abifile.close()

    # network name
    network.name = name

    # instantiate the plantoid address
    network.plantoid_address = addr

    # instantiate the metadata address
    network.metadata_address = metadata_address

    # instantiate the contract
    network.plantoid_contract = network.w3.eth.contract(address=address, abi=abi)
    print('plantoid contract === ', network.plantoid_contract)

    # instantiate the event filter
    network.event_filter = network.plantoid_contract.events.Deposit.create_filter(fromBlock=start_block)
    print('event filter:', network.event_filter)
    
    # set the path
    network.path = path
    network.plantoid_path = plantoid_path

    # set the minimum amount of wei that needs to be fed to the plantoid
    network.min_amount = feeding_amount

    # set the url to reclaim the plantoid
    network.reclaim_url = reclaim_url

    # set the failsafe
    network.failsafe = failsafe

    # INDEXER 
    network.indexer = None

    if INDEXER_URL:
        minted_path = plantoid_path + '/minted_' + name + '.db'
        network.indexer = IndexerClient(
            url = INDEXER_URL,
            plantoid_address = addr,
            minted_db_path = minted_db_path,
        )
    # prime the cursor from minted.db
    if os.path.exists(minted_path):
        with open(minted_path, 'r') as f:
            ids = [int(line.strip()) for line in f if line.strip()]
            if ids:
                network.indexer.max_processed_token_id = max(ids)

    return network  
    


def process_previous_tx(plantoid, network):

    processing = 0

    path = network.plantoid_path
    event_filter = network.event_filter
    minted_db_token_ids = []

    print("NETWORK PATH = ", path)

    # if db doesn't exist, nothing has been minted yet

    if (not os.path.exists(path + '/minted_'+str(network.name)+'.db')):
        print('processing is null')
        processing = 1

    # if db exists, skip to the last minted item

    else:

        with open(path + '/minted_'+str(network.name)+'.db', 'r') as file:
            # Iterate through each line in the file
            for line in file:
                # Strip the newline character and convert the string to an integer, then append to the list
                minted_db_token_ids.append(str(line.strip()))

            minted_db_token_ids = list(set(minted_db_token_ids))

    # loop over all entries to process unprocessed Deposits


    # 1. try indexer first
    event_token_ids = None
    indexer = getattr(network, 'indexer', None)
    if indexer is not None:
        try:
            event_token_ids = indexer.fetch_all_token_ids()
            print(f"[indexer] fetched {len(event_token_ids)} historical token ids")
        except IndexerUnavailable as e:
            print(f"[indexer] unavailable, falling back to RPC: {e}")

    # 2. try the event filter if indexer has failed
    if event_token_ids is None:
        try:
            event_list = event_filter.get_all_entries()
            event_token_ids = [str(e.args.tokenId) for e in event_list]
        except Exception as err:
            print(f"process previous tx - Unexpected {err=}, {type(err)=}")
            return
    


    for token_Id in event_token_ids:

        print("looping through ---: " +token_Id)

        if token_Id not in minted_db_token_ids:

            print("calling create seed metadata with network = ", network, " and tokenId = ", token_Id)
            plantoid.create_seed_metadata(network, token_Id)

            enable_seed_reveal(network, token_Id)


   



def check_for_deposits(web3obj):

    # try indexer first
    indexer = getattr(web3obj, 'indexer', None)
    if indexer is not None:

        try:

            deposit = indexer.fetch_oldest_unprocessed_deposit()
            if deposit is None:
                return None

            indexer.advance_cursor(deposit['tokenId'])
            print(f"[indexer] new deposit: token={deposit['tokenId']} amount={deposit['amount']} tx={deposit['txHash']}")
            return (deposit['tokenId'], deposit['amount'])

        except IndexerUnavailable as e:
            print(f"[indexer] unavailable, falling back to RPC: {e}")


    # RPC fallback (old behavior)
    event_filter = web3obj.event_filter

    try:
        events = event_filter.get_new_entries()
    
    except Exception as err:
        print(f"check for depositis - Unexpected {err=}, {type(err)=}")
        # return None
        sys.exit(0)

    print('transaction events', events)

    if len(events) > 0:

        for event in events:
            print("new Deposit EVENT !! ")
            print("token id = " + str(event.args.tokenId))
            print("amount = " + str(event.args.amount))

            return (str(event.args.tokenId), int(event.args.amount))  ### @@@@ need to fix this  :)

    else:

        return None




def pin_metadata_to_ipfs(metadata_path):

    pinata = Pinata(PINATA_API_KEY, PINATA_API_SECRET, PINATA_JWT)

    print("KEY = ", PINATA_API_KEY)
    print("SECRET = ", PINATA_API_SECRET)
    print("JWT = ", PINATA_JWT)

    print('metadata is', metadata_path)

    response = pinata.pin_file(metadata_path)
    print('pinata response:', response)

    is_duplicate = False

    if response and response.get('data'):

        seed_metadata = response['data']['IpfsHash']
        # print("the metadata url is = " + seed_metadata)

        if response['data'].get('isDuplicate') is not None:

            is_duplicate = True

    return seed_metadata, is_duplicate

def get_msg_hash(plantoid_address, ipfs_hash, token_Id):

    token_uri = 'ipfs://' + ipfs_hash

    checksum_address =  Web3.to_checksum_address(plantoid_address)

    msgHash = Web3.solidity_keccak(
        ['uint256', 'string', 'address'],
        [token_Id, token_uri, checksum_address],
    )

    def arrayify_bytes(hbytes):
        return [hbytes[i] for i in range(len(hbytes))]

    msgHashArrayified = arrayify_bytes(msgHash)
  
    # print('message hash: ', msgHash.hex())
    # print('message hash arrayified: ', msgHashArrayified)

    return msgHash, msgHash.hex(), msgHashArrayified

def create_signer_and_sign(msg_hash, private_key):

    # # WRONG!!
    # message = messages.encode_defunct(text=msg_hash_hex)
    # signed_message = Account.sign_message(message, private_key=private_key)
    # print('signed message: ', signed_message.signature.hex())

    # CORRECT!!
    prepared_message = messages.defunct_hash_message(primitive=msg_hash)
    hash_signed_message = Account.unsafe_sign_hash(prepared_message, private_key) # '0x' + private_key
    sig = hash_signed_message.signature.hex()

    # print('signature: ', sig)

    return sig

def encode_function_data(plantoid_address, abi_file_path, token_Id, ipfs_hash, sig):

    w3 = Web3(EthereumTesterProvider())

    # Define the path to the ABI file
    # abi_file_path = path + './abis/plantoidMetadata'

    # Load the ABI
    with open(abi_file_path, 'r') as f:
        contract_json = json.load(f)
        abi = contract_json#['abi']

    token_Uri = 'ipfs://' + ipfs_hash

    # print(abi)

    # Get the contract utility using the ABI
    contract = w3.eth.contract(abi=abi)

    checksum_address =  Web3.to_checksum_address(plantoid_address)

    # Encode the function call
    data = contract.encodeABI(fn_name="revealMetadata", args=[checksum_address, int(token_Id), token_Uri, bytes.fromhex(sig.replace('0x', ''))])

    # print('encoded function data: ', data)

    return data

def send_relayer_transaction(metadata_address, data):

    # https://github.com/franklin-systems/oz-defender/blob/trunk/oz_defender/relay/client.py
    # https://forum.openzeppelin.com/t/what-exactly-is-the-function-of-defenders-relay-when-using-metatransactions/23122/7
    # relayer = RelayerClient(api_key=DEFENDER_API_KEY, api_secret=DEFENDER_API_SECRET)

    # connect to Polygon
    w3_polygon = Web3(Web3.HTTPProvider('https://polygon-mainnet.infura.io/v3/' + INFURA_API_KEY_MAINNET))

    signer_private_key = get_signer_private_key()
    account = Account.from_key(signer_private_key)

    # build the tx
    tx = {
      'to': Web3.to_checksum_address(metadata_address),
      'data': data,
      'chainId': 137, # Polygon
      'gas': 100000,
#      'schedule': 'fast',
      'gasPrice': w3_polygon.eth.gas_price,
      'nonce': w3_polygon.eth.get_transaction_count(account.address),
    }

    # sign and send
    signed_tx = w3_polygon.eth.account.sign_transaction(tx, signer_private_key)
    tx_hash = w3_polygon.eth.send_raw_transaction(signed_tx.raw_transaction)

    print('sent transaction on Polygon. tx hash = ', tx_hash.hex())

#    response = relayer.send_transaction(tx)
#    print('sent metatransaction. relayer response:', response)

def enable_seed_reveal(network, token_Id):

    print('call enable seed reveal.')

    # instantiate metadata
    metadata = None

    # get the private key of the signer
    signer_private_key = get_signer_private_key()

    # get the metadata path based on the token ID
    metadata_path = network.plantoid_path+'/metadata/'+network.name+"/"+str(token_Id)+'.json'

    # skip if not a file
    if not os.path.isfile(metadata_path):
        print('No metadata file found for seed ID', token_Id, 'skipping...')
        return
    
    # read the metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    print(metadata_path)

    # pin the metadata to IPFS
    ipfs_hash, is_duplicate = pin_metadata_to_ipfs(metadata_path)
    #ipfs_hash = 'QmR5oZbMUjrMJt6hrerjiCRKauhsXeVfGnmYw2ojVXiakM'

    if is_duplicate == True:
        print('Duplicate IPFS hash encountered:', ipfs_hash, 'skipping...')
        return 

    token_Id = int(metadata['name'])
    # print('ipfs hash is', ipfs_hash)
    # print('token id is', token_Id)

    # get the message hash
    msg_hash, _, _ = get_msg_hash(
        network.plantoid_address,
        ipfs_hash,
        token_Id,
    )

    # get the signature
    sig = create_signer_and_sign(
        msg_hash,
        signer_private_key,
    )

    # get the encoded function data
    abi_file_path = network.path + './abis/plantoidMetadata'
    function_data = encode_function_data(
        network.plantoid_address,
        abi_file_path,
        token_Id,
        ipfs_hash,
        sig,
    )

    # Send the metatransaction through OZ Defender
    send_relayer_transaction(
        network.metadata_address,
        function_data,
    )



