import lib.plantoid.behaviors.behavior_library as behavior_library
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




def create_seed_metadata(network, token_Id):

    print('call create metadata.')


    #plantoid.send_serial_message("asleep") ## REMOVE
    #plantoid.send_serial_message("fire") ## REMOVE

    # create a pinata object
    pinata = Pinata(PINATA_API_KEY, PINATA_API_SECRET, PINATA_JWT)

    # get the path
    path = network.plantoid_path

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

    ### TODO: THIS SHOULD NOT BE HARDCODED for PLANTOID15 !!

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

    #plantoid.send_serial_message("fire") ## REMOVE
    #plantoid.send_serial_message("awake") ## REMOVE