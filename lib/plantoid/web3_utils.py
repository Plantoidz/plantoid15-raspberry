from web3 import Web3, EthereumTesterProvider
from eth_account import Account, messages
from oz_defender.relay import RelayClient, RelayerClient
import subprocess
import os
import time
from pathlib import Path
import json
from dotenv import load_dotenv
from pinata import Pinata

import lib.plantoid.eden as eden

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
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_JWT = os.environ.get('PINATA_JWT')
DEFENDER_API_KEY = os.environ.get("DEFENDER_API_KEY")
DEFENDER_API_SECRET = os.environ.get("DEFENDER_API_SECRET")
SIGNER_PRIVATE_KEY = os.environ.get("SIGNER_PRIVATE_KEY")
INFURA_API_KEY_MAINNET = os.environ.get("INFURA_MAINNET")
INFURA_API_KEY_GOERLI = os.environ.get("INFURA_GOERLI")

def get_signer_private_key():

    return SIGNER_PRIVATE_KEY

def setup_web3_provider(config):

    goerli = None
    mainnet = None

    if config['use_goerli'] == True:

        # make sure that the script can listen to both events happening in mainnet and goerli, and process them accordingly !
        goerli = setup(
            'wss://goerli.infura.io/ws/v3/'+INFURA_API_KEY_GOERLI,
            config['use_goerli_address'],
            config['use_metadata_address'],
            name="goerli",
            path=os.getcwd(),
            feeding_amount=1000000000000000,  # one line every 0.001 ETH
            reclaim_url="http://15goerli.plantoid.org",
            failsafe=config['goerli_failsafe'], # this set failsafe = 1 (meaning we should recycle movies)
        ) 

    if config['use_mainnet'] == True:

        # lorem ipsum
        mainnet = setup(
            'wss://mainnet.infura.io/ws/v3/'+INFURA_API_KEY_MAINNET,
            config['use_mainnet_address'],
            config['use_metadata_address'],
            name="mainnet",
            path=os.getcwd(),
            feeding_amount=10000000000000000,  # one line every 0.01 ETH)
            reclaim_url="http://15.plantoid.org",
            failsafe=config['mainnet_failsafe'], # this set failsafe = 0 (meaning we should generate a new movie)
        ) 
    
    return goerli, mainnet

def setup(
    infura_websock,
    addr,
    metadata_address,
    name="",
    path=None,
    feeding_amount=0,
    reclaim_url=None,
    failsafe=0,
):
    
    try:

        # create a web3 object
        network = Web3Object();

        # connect to the infura node
        network.w3 = Web3(Web3.WebsocketProvider(infura_websock))

        print('w3 is', network.w3)
        print('is connected', network.w3.is_connected())

        # checksum the address
        address = Web3.to_checksum_address(addr)
        print('address is', address)

        # get the balance of the address
        eth_balance_wei = network.w3.eth.get_balance(address)
        eth_balance = network.w3.from_wei(eth_balance_wei, 'ether')

        print('eth balance:', eth_balance)

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

        # instantiate the event filter
        network.event_filter = network.plantoid_contract.events.Deposit.create_filter(fromBlock=1)
        # print('event filter:', network.event_filter)
        
        # set the path
        network.path = path

        # set the minimum amount of wei that needs to be fed to the plantoid
        network.min_amount = feeding_amount

        # set the url to reclaim the plantoid
        network.reclaim_url = reclaim_url

        # set the failsafe
        network.failsafe = failsafe

        return network  
    
    except TimeoutError:

        print('Connection unsuccessful or timed out!')
        return None

def process_previous_tx(network):

    processing = 0

    path = network.path
    event_filter = network.event_filter
    minted_db_token_ids = []

    # if db doesn't exist, nothing has been minted yet

    if (not os.path.exists(path + '/minted_'+str(network.name)+'.db')):
        print('processing is null')
        processing = 1

    # if db exists, skip to the last minted item

    else:

        with open('minted_'+str(network.name)+'.db', 'r') as file:
            # Iterate through each line in the file
            for line in file:
                # Strip the newline character and convert the string to an integer, then append to the list
                minted_db_token_ids.append(str(line.strip()))

            minted_db_token_ids = list(set(minted_db_token_ids))

    # loop over all entries to process unprocessed Deposits
    for event in event_filter.get_all_entries():

        token_Id = str(event.args.tokenId)

        print("looping through ---: " +token_Id)

        if token_Id not in minted_db_token_ids:

            print('processing metadata for token id:', token_Id)
            create_seed_metadata(network, token_Id)
            enable_seed_reveal(network, token_Id)


        # if processing == 0:

        #     if(token_Id == last.strip()):

        #         processing = 1
        #         print('processing is true\n')

        #     continue

        # print('handling event...\n')
        # create_seed_metadata(network, token_Id)
        # enable_seed_reveal(network, token_Id)
    
def check_for_deposits(web3obj):

    # get the event filter
    event_filter = web3obj.event_filter

    events = event_filter.get_new_entries()

    print('transaction events', events)

    if len(events) > 0:

        for event in events:
            print("new Deposit EVENT !! ")
            print("token id = " + str(event.args.tokenId))
            print("amount = " + str(event.args.amount))

            return (str(event.args.tokenId), int(event.args.amount))  ### @@@@ need to fix this  :)

    else:

        return None
    # except:
    #     print("failed to read new entries()\n")
    #     # TODO: check if this is correct exception handling
    #     return None

    #        #  return  str(event.args.tokenId) 

def create_seed_metadata(network, token_Id):

    print('call create metadata.')

    # create a pinata object
    pinata = Pinata(PINATA_API_KEY, PINATA_API_SECRET, PINATA_JWT)

    # get the path
    path = network.path

    # set variables to None
    ipfsQmp3 = None
    movie_path = None

    # check if the movie already exists
    if os.path.exists(path + "/videos/" + network.name + "/" + token_Id +"_movie.mp4"):

        # the movie already exists, move directly to the metadata creation
        print("skipping the production of the movie, as it already exists...");
        movie_path = path + "/videos/" + network.name + "/" + token_Id +"_movie.mp4"

    else:

        # the movie doesn't exist, create it
        audio = path + "/sermons/" + network.name + "/" + token_Id + "_sermon.mp3"
        print("creating movie for sermon file.. " + audio) 
        
        if os.path.isfile(audio):
            movie_path = eden.create_video_from_audio(path, token_Id, network.failsafe, network.name)

        else:
            print("no Sermon audio file associated with seed: " + token_Id, 'skipping...')
            return

    ### Pin the Video-Sermon on IPFS
    if movie_path is not None:

        print("movie found, pinning to IPFS")

        response = pinata.pin_file(movie_path)
        print('pinata response:', response)

        # TODO: this should probably check for a response code
        if(response and response.get('data')):
            ipfsQmp3 = response['data']['IpfsHash']
            print("recording the animation_url = " + ipfsQmp3)

    else:
        print("movie is null, skipping pinning to IPFS")

    ### Create Metadata
    db = dict()

    db['name'] = token_Id
    db['description'] = "Plantoid #15 - Seed #" + token_Id
    db['external_url'] = "http://plantoid.org"
    db['image'] = "https://ipfs.io/ipfs/QmRcrcn4X6QfSwFnJQ1dNHn8YgW7pbmm6BjZn7t8FW7WFV" # ipfsQpng

    if ipfsQmp3 is not None:
        db['animation_url'] = "ipfs://" + ipfsQmp3 # ipfsQwav

    path_meta = path + "/metadata/"
    path_meta_network = path + "/metadata/"+str(network.name)+"/"

    if not os.path.exists(path_meta):
        os.makedirs(path_meta)

    if not os.path.exists(path_meta_network):
        os.makedirs(path_meta_network)

    with open(path_meta_network + token_Id + '.json', 'w') as outfile:
        json.dump(db, outfile)

    ### record in the database that this seed has been processed
    with open(path + '/minted_'+str(network.name)+'.db', 'a') as outfile:
        outfile.write(token_Id + "\n")


def pin_metadata_to_ipfs(metadata_path):

    pinata = Pinata(PINATA_API_KEY, PINATA_API_SECRET, PINATA_JWT)

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

    msgHash = Web3.solidity_keccak(
        ['uint256', 'string', 'address'],
        [token_Id, token_uri, plantoid_address],
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
    hash_signed_message = Account.signHash(prepared_message, private_key) # '0x' + private_key
    sig = hash_signed_message.signature.hex()

    # print('signature: ', sig)

    return sig

def encode_function_data(plantoid_address, token_Id, ipfs_hash, sig):

    w3 = Web3(EthereumTesterProvider())

    # Define the path to the ABI file
    abi_file_path = './abis/plantoidMetadata'

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

    # print('encoded function data: ', data)

    return data

def send_relayer_transaction(metadata_address, data):

    # https://github.com/franklin-systems/oz-defender/blob/trunk/oz_defender/relay/client.py
    # https://forum.openzeppelin.com/t/what-exactly-is-the-function-of-defenders-relay-when-using-metatransactions/23122/7
    relayer = RelayerClient(api_key=DEFENDER_API_KEY, api_secret=DEFENDER_API_SECRET)

    tx = {
      'to': metadata_address,
      'data': data,
      'gasLimit': '100000',
      'schedule': 'fast',
    }

    response = relayer.send_transaction(tx)
    print('sent metatransaction. relayer response:', response)

def enable_seed_reveal(network, token_Id):

    print('call enable seed reveal.')

    # instantiate metadata
    metadata = None

    # get the private key of the signer
    signer_private_key = get_signer_private_key()

    # get the metadata path based on the token ID
    metadata_path = os.getcwd()+'/metadata/'+network.name+"/"+str(token_Id)+'.json'

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
    function_data = encode_function_data(
        network.plantoid_address,
        token_Id,
        ipfs_hash,
        sig,
    )

    # Send the metatransaction through OZ Defender
    send_relayer_transaction(
        network.metadata_address,
        function_data,
    )