#import lib.plantoid.behaviors.behavior_library as behavior_library
from lib.plantoid.behaviors import behavior_library
from plantoids.plantoid import Plantony

import os
from dotenv import load_dotenv
from pinata import Pinata
load_dotenv()

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_JWT = os.environ.get('PINATA_JWT')



def ingurgitate_crypto(plantoid: Plantony, network, tID, amount):
    print("trying to get the oracle library........")


    # do weaving
    plantoid.weaving()
        
    # listen for audio
    audiofile = plantoid.listen()
        
    # generate, print, and read the oracle
    oracle = behavior_library.generate_oracle(plantoid, network, audiofile, tID, amount)
    # behavior_library.print_oracle(plantoid, network, tID, oracle)
    behavior_library.read_oracle(plantoid, network, tID, oracle)



def create_seed_metadata(plantoid: Plantony, network, token_Id):

    print("trying to access the library for creating the seed ---------------------------")

    db = dict()
    db['name'] = token_Id
    db['description'] = "Plantoid #14 - Seed #" + token_Id
    db['external_url'] = "http://plantoid.org"
    db['image'] = "https://ipfs.io/ipfs/QmRcrcn4X6QfSwFnJQ1dNHn8YgW7pbmm6BjZn7t8FW7WFV" # ipfsQpng

    animurl = behavior_library.get_animation_url(plantoid, network, token_Id)
    behavior_library.record_metadata(plantoid, network, token_Id, db, animurl)
