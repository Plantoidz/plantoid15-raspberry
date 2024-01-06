import os
import time
from pathlib import Path
import json
from dotenv import load_dotenv
from pinata import Pinata

import lib.plantoid.eden as eden

load_dotenv()

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_JWT = os.environ.get('PINATA_JWT')

# TODO: refactor this and add inputs
# def generate_oracle(self, network, audio, tID, amount):

#     self.send_serial_message("thinking")

#     # get the path of the network
#     path = network.path

#     # get the path to the background music
#     background_music_path = self.path+"/media/ambient3.mp3"

#     # play the background music
#     self.play_background_music(background_music_path)

#     # get generated transcript
#     generated_transcript = PlantoidSpeech.recognize_speech(audio)

#     # print the generated transcript
#     print("I heard... (oracle): " + generated_transcript)

#     # if no generated transcript, use a default
#     if not generated_transcript: 
#         generated_transcript = get_default_sermon_transcript()

#     # save the generated transcript to a file with the seed name
#     path_transcripts = path + "/transcripts"
#     path_transcripts_network = path + "/transcripts/" + str(network.name)

#     if not os.path.exists(path_transcripts):
#         os.makedirs(path_transcripts)

#     if not os.path.exists(path_transcripts_network):
#         os.makedirs(path_transcripts_network)

#     # save the generated response to a file with the seed name
#     filename = path + f"/transcripts/{network.name}/{tID}_transcript.txt"

#     with open(filename, "w") as f:
#         f.write(generated_transcript)

#     print("transcript saved as ..... " + filename)

#     # TODO: re-enable
#     # calculate the length of the poem
#     # one line every 0.01 ETH for mainnet, one line every 0.001 ETH for goerli
#     n_lines = int(amount / network.min_amount)  
    
#     if n_lines > 6: 
#         n_lines = 6

#     # n_lines = 4

#     print("generating transcript with number of lines = " + str(n_lines))
    
#     # generate the sermon prompt
#     prompt = get_sermon_prompt(
#         generated_transcript,
#         self.selected_words_string,
#         n_lines
#     )
    
#     # get GPT response
#     response = PlantoidSpeech.GPTmagic(prompt, call_type='completion')
#     sermon_text = response.choices[0].text

#     print('sermon text:')
#     print(sermon_text)

#     responses_path = path + "/responses"
#     responses_path_network = path + "/responses/" + str(network.name)

#     # save the generated response to a file with the seed name
#     if not os.path.exists(responses_path):
#         os.makedirs(responses_path);

#     # save the generated response to a file with the seed name
#     if not os.path.exists(responses_path_network):
#         os.makedirs(responses_path_network);
    
#     # save the generated response to a file with the seed name
#     filename = path + f"/responses/{network.name}/{tID}_response.txt"
#     with open(filename, "w") as f:
#         f.write(sermon_text)

#     # now let's print to the LP0, with Plantoid signature
#     # TODO: figure out what this is meant to do
#     plantoid_sig = get_plantoid_sig(network, tID)

#     # TODO: figure out what this is meant to do
#     # os.system("cat " + filename + " > /dev/usb/lp0") #stdout on PC, only makes sense in the gallery
#     # os.system("echo '" + plantoid_sig + "' > /dev/usb/lp0")

#     # now let's read it aloud
#     audiofile = PlantoidSpeech.get_text_to_speech_response(sermon_text, self.eleven_voice_id)
#     # stop_event.set() # stop the background noise

#     sermons_path = path + "/sermons"
#     sermons_path_network = path + "/sermons/"+str(network.name)

#     # save the generated sermons to a file with the seed name
#     if not os.path.exists(sermons_path):
#         os.makedirs(sermons_path)

#     if not os.path.exists(sermons_path_network):
#         os.makedirs(sermons_path_network)
    
#     # save mp3 file
#     # subprocess.run(["cp", audiofile, f"{path}/sermons/{tID}_sermon.mp3"])
#     subprocess.run(["cp", audiofile, f"{sermons_path_network}/{tID}_sermon.mp3"])

#     # stop the background music
#     self.stop_background_music()

#     # play the oracle
#     self.send_serial_message("speaking")
    
#     # playsound(filename)
#     self.play_background_music(filename, loops=0)
#     time.sleep(1)

#     print('oracle read completed!')


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