import os
import time
from pathlib import Path
import json
from dotenv import load_dotenv
from pinata import Pinata
import subprocess

from plantoids.plantoid import Plantony
from lib.plantoid.text_content import *
import lib.plantoid.speech as PlantoidSpeech
import lib.plantoid.eden as eden


load_dotenv()

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_JWT = os.environ.get('PINATA_JWT')

def testfun():
    print("AHAHHAHAHAHAHHAHAHAHAHAHAHAHHAHAHAHAHAHAHAHAHAHHAHAHAHAHA")

def generate_oracle(plantoid: Plantony, network, audio, tID, amount):

    plantoid.send_serial_message("thinking")
    plantoid.send_serial_message("asleep") ## REMOVE


    # get the path of the network
    path = network.plantoid_path
    print("TRANSCRIBING... in PATH ==== ", path)

    # get the path to the background music
    background_music_path = plantoid.path+"/media/ambient3.mp3"

    # play the background music
    plantoid.play_background_music(background_music_path)

    # get generated transcript
    generated_transcript = PlantoidSpeech.recognize_speech(audio)

    # print the generated transcript
    print("I heard... (oracle): " + generated_transcript)

    # if no generated transcript, use a default
    if not generated_transcript: 
        generated_transcript = get_default_sermon_transcript()

    # save the generated transcript to a file with the seed name
    path_transcripts = path + "/transcripts/"
    path_transcripts_network = path_transcripts + str(network.name)

    if not os.path.exists(path_transcripts):
        os.makedirs(path_transcripts)

    if not os.path.exists(path_transcripts_network):
        os.makedirs(path_transcripts_network)

    # save the generated response to a file with the seed name
    filename = f"{path_transcripts_network}/{tID}_transcript.txt"

    print("saving transcript as ...................................", filename)

    with open(filename, "w") as f:
        f.write(generated_transcript)

    print("transcript saved as ..... " + filename)

    # TODO: re-enable
    # calculate the length of the poem
    # one line every 0.01 ETH for mainnet, one line every 0.001 ETH for goerli
    n_lines = int(amount / network.min_amount)  
    
    if n_lines > 6: 
        n_lines = 6

    # n_lines = 4

    print("generating transcript with number of lines = " + str(n_lines))
    
    # generate the sermon prompt
    prompt = get_sermon_prompt(
        generated_transcript,
        plantoid.selected_words_string,
        n_lines
    )
    
    # get GPT response
    response = PlantoidSpeech.GPTmagic(prompt, call_type='completion')
    sermon_text = response.choices[0].text

    print('sermon text:')
    print(sermon_text)

    responses_path = path + "/responses/"
    responses_path_network = responses_path + str(network.name)

    # save the generated response to a file with the seed name
    if not os.path.exists(responses_path):
        os.makedirs(responses_path);

    # save the generated response to a file with the seed name
    if not os.path.exists(responses_path_network):
        os.makedirs(responses_path_network);
    
    # save the generated response to a file with the seed name
    filename =  f"{responses_path_network}/{tID}_response.txt"
    with open(filename, "w") as f:
        f.write(sermon_text)

    # now let's print to the LP0, with Plantoid signature
    # TODO: figure out what this is meant to do
    plantoid_sig = get_plantoid_sig(network, tID)

    # TODO: figure out what this is meant to do
    # os.system("cat " + filename + " > /dev/usb/lp0") #stdout on PC, only makes sense in the gallery
    # os.system("echo '" + plantoid_sig + "' > /dev/usb/lp0")

    # now let's read it aloud
    audiofile = PlantoidSpeech.get_text_to_speech_response(sermon_text, plantoid.eleven_voice_id)
    # stop_event.set() # stop the background noise

    sermons_path = path + "/sermons/"
    sermons_path_network = sermons_path +str(network.name)

    # save the generated sermons to a file with the seed name
    if not os.path.exists(sermons_path):
        os.makedirs(sermons_path)

    if not os.path.exists(sermons_path_network):
        os.makedirs(sermons_path_network)
    
    # save mp3 file
    # subprocess.run(["cp", audiofile, f"{path}/sermons/{tID}_sermon.mp3"])
    subprocess.run(["cp", audiofile, f"{sermons_path_network}/{tID}_sermon.mp3"])

    # stop the background music
    plantoid.stop_background_music()

    # play the oracle
    plantoid.send_serial_message("speaking")
    plantoid.send_serial_message("fire") ## REMOVE

    
    # playsound(filename)
    plantoid.play_background_music(audiofile, loops=0)
    time.sleep(1)

    print('oracle read completed!')
    plantoid.send_serial_message("fire") ## REMOVE
