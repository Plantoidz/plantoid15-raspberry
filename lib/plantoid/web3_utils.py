from web3 import Web3
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

# API_KEY = os.getenv('API_KEY')
# API_SECRET = os.getenv('API_SECRET')
# JWT = os.getenv('JWT')

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_JWT = os.environ.get('PINATA_JWT')
INFURA_API_KEY_MAINNET = os.environ.get("INFURA_MAINNET")
INFURA_API_KEY_GOERLI = os.environ.get("INFURA_GOERLI")

def setup_web3_provider(config):

    goerli = None
    mainnet = None

    if config['use_goerli'] == True:

        # make sure that the script can listen to both events happening in mainnet and goerli, and process them accordingly !
        goerli = setup(
            'wss://goerli.infura.io/ws/v3/'+INFURA_API_KEY_GOERLI,
            config['use_goerli_address'],
            path=os.getcwd(),
            feeding_amount=1000000000000000,  # one line every 0.001 ETH
            reclaim_url="http://15goerli.plantoid.org",
            failsafe=1, # this set failsafe = 1 (meaning we should recycle movies)
        ) 

    if config['use_mainnet'] == True:

        # lorem ipsum
        mainnet = setup(
            'wss://mainnet.infura.io/ws/v3/'+INFURA_API_KEY_MAINNET,
            config['use_mainnet_address'],
            path=os.getcwd(),
            feeding_amount=10000000000000000,  # one line every 0.01 ETH)
            reclaim_url="http://15.plantoid.org",
            failsafe=0, # this set failsafe = 0 (meaning we should generate a new movie)
        ) 
    
    return goerli, mainnet

def setup(
    infura_websock,
    addr,
    path=None,
    feeding_amount=0,
    reclaim_url=None,
    failsafe=0,
):

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

def process_previous_tx(web3obj):

    processing = 0

    path = web3obj.path
    event_filter = web3obj.event_filter

    # if db doesn't exist, nothing has been minted yet

    if (not os.path.exists(path + 'minted.db')):
        print('processing is null')
        processing = 1

    # if db exists, skip to the last minted item

    else:

        with open(path + 'minted.db') as file:
            for line in file:
                pass
            last = line
            print("last line = " + last)

    # loop over all entries to process unprocessed Deposits

    for event in event_filter.get_all_entries():

        print("looping through ---: " +str(event.args.tokenId))

        if processing == 0:
            if(str(event.args.tokenId) == last.strip()):
                processing = 1;
                print('processing is true\n')
            continue;

        print('handling event...\n')
        create_metadata(web3obj, str(event.args.tokenId))

    
def check_for_deposits(web3obj):

    # get the event filter
    event_filter = web3obj.event_filter

    events = event_filter.get_new_entries()

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

def create_metadata(web3obj, tID):

    # create a pinata object
    pinata = Pinata(PINATA_API_KEY, PINATA_API_SECRET, PINATA_JWT)

    # get the path
    path = web3obj.path
    print('path is', path)

    # set variables to None
    ipfsQmp3 = None
    movie_path = None

    # check if the movie already exists
    if os.path.exists(path + "/videos/"+tID+"_movie.mp4"):

        # the movie already exists, move directly to the metadata creation
        print("skipping the production of the movie, as it already exists...");
        movie_path = path + "/videos/"+tID+"_movie.mp4"

    else:

        # the movie doesn't exist, create it
        audio = path + "/sermons/" + tID + "_sermon.mp3"
        print("creating movie for sermon file.. " + audio) 
        
        if not os.path.isfile(audio):
            print("no Sermon associated with seed: " + tID)
            return

        movie_path = eden.create_video_from_audio(path, tID, web3obj.failsafe)

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

    db['name'] = tID
    db['description'] = "Plantoid #15 - Seed #" + tID
    db['external_url'] = "http://plantoid.org"
    db['image'] = "https://ipfs.io/ipfs/QmRcrcn4X6QfSwFnJQ1dNHn8YgW7pbmm6BjZn7t8FW7WFV" # ipfsQpng

    if ipfsQmp3 is not None:
        db['animation_url'] = "ipfs://" + ipfsQmp3 # ipfsQwav

    path_meta = path + "/metadata/"

    if not os.path.exists(path_meta):
        os.makedirs(path_meta)

    with open(path_meta + tID + '.json', 'w') as outfile:
        json.dump(db, outfile)

    # TODO: what does this do?
    ### record in the database that this seed has been processed
    with open(path + "minted.db", 'a') as outfile:
        outfile.write(tID + "\n")

    ### NB: The metadata file will be pinned to IPFS via the node server

#    file_stats = os.stat(audio)

#    if(file_stats.st_size):
#        cmd_str = "xvfb-run /home/pi/PLLantoid/v5/processing/processing-java --sketch=/home/pi/PLLantoid/v6/voice2video --run " + audio
#        print(cmd_str)
#        err = subprocess.run(cmd_str, shell=True) # return 0 if works well
#        print(err)
#        if not err.check_returncode():
#            print("pinning the movie to ipfs")
#            audio = "/home/pi/PLLantoid/v5/voicevideo/voicefile2/processing-movie.mp4"