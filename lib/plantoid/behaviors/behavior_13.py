#import lib.plantoid.behaviors.behavior_library as behavior_library
from lib.plantoid.behaviors import behavior_library
#from plantoids.plantoid import Plantony
import lib.plantoid.eden as eden


import os
from dotenv import load_dotenv
from pinata import Pinata
load_dotenv()

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_JWT = os.environ.get('PINATA_JWT')



def ingurgitate_crypto(plantoid, network, tID, amount):

    print('ACTIVATING THE PLANTOID .....................................\n')
    client = udp_client.SimpleUDPClient('255.255.255.255', 9999, True)
    client.send_message('/filename', tID)
    
    ### activate the plantooid for a specific amount of time, then create the metadata for the generated seed

    seconds = int ( amount / network.min_amount) # 10 second per 0.001 eth on Sepolia, or per 0.01 eth on Mainnet
    client.send_message('/plantoid/255/255/capa/0', 1024)
    print("activated for seconds: " + str(seconds))
    time.sleep(int(seconds))
    client.send_message('/plantoid/255/255/capa/0', 1024)
    print("de-activated")
    


def create_seed_metadata(plantoid, network, token_Id):

    movie_path = None
    animurl = None

    # create the metadata information

    db = dict()
    db['name'] = token_Id
    db['description'] = "Plantoid #13 - Seed #" + token_Id
    db['external_url'] = "http://plantoid.org"
    db['image'] = "ipfs://QmcNY71soxdqjNhhwQkfLFDGRx4kaVva7ERFiNWa1ZFk5m"

    # check if a video exists for that particular token_Id

    path = network.plantoid_path
    if os.path.exists(path + "/videos/" + network.name + "/" + token_Id +"_movie.mp4"):
        movie_path = path + "/videos/" + network.name + "/" + token_Id +"_movie.mp4"

    elif os.path.isfile("/home/path/plantoidz-pi/recordings/" +  token_Id + ".wav"):

        # if movie doesn't exist, but song.mp3 exists, make a new movie based on the recorded audio:

        os.system('python3.10 ' + path + '/../lib/plantoid/behaviors/sound_visualisation.py ' + 
                  "/home/path/plantoidz-pi/recordings/" +  token_Id + ".wav" +
                  " -o " + path + "/videos/" + network.name + "/" + token_Id + "_movie.mp4 " +
                  " --size 800 --fps 24")
        
        movie_path = path + "/videos/" + network.name + "/" + token_Id +"_movie.mp4"
        
        # movie_path = behavior_library.make_video(path, movie_path, token_Id, network.name)


    animurl = behavior_library.pin_movie(movie_path)
    
    if(animurl):  ## only upload metadata if there is an associated video
        behavior_library.record_metadata(plantoid, network, token_Id, db, animurl)





