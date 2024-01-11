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



def generate_oracle(plantoid: Plantony, network, audio, tID, amount):
    print("trying to get the oracle library........")
    behavior_library.testfun()
    behavior_library.generate_oracle(plantoid, network, audio, tID, amount)



def create_seed_metadata(plantoid: Plantony, network, token_Id):

    plantoid.send_serial_message("asleep") ## REMOVE
    plantoid.send_serial_message("fire") ## REMOVE

    print("trying to access the library for creating the seed ---------------------------")

    db = dict()
    db['name'] = token_Id
    db['description'] = "Plantoid #15 - Seed #" + token_Id
    db['external_url'] = "http://plantoid.org"
    db['image'] = "https://ipfs.io/ipfs/QmRcrcn4X6QfSwFnJQ1dNHn8YgW7pbmm6BjZn7t8FW7WFV" # ipfsQpng

    behavior_library.create_seed_metadata(plantoid, network, token_Id, db)

    plantoid.send_serial_message("fire") ## REMOVE
    plantoid.send_serial_message("awake") ## REMOVE
