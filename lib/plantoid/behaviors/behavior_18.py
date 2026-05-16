from lib.plantoid.behaviors import behavior_library as behaviors

import lib.plantoid.speech as PlantoidSpeech

import os
import re

from dotenv import load_dotenv
from pinata import Pinata
load_dotenv()

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_JWT = os.environ.get('PINATA_JWT')



def ingurgitate_crypto(plantoid, network, tID, amount):

    question = "What is the song that you're weaving into being through your life?"
    user_speech = behaviors.ask_transcript(plantoid, network, tID, question)


    # Generate response  ..
    plantoid.send_serial_message("thinking")
    
    # calculate the credits for the response
    # one line every 0.01 ETH for mainnet, one line every 0.001 ETH for goerli
    credits = int(amount / network.min_amount)  

    lines = behaviors.get_song_prompts(plantoid, user_speech, credits)
    
    response = '\n'.join(lines)
    print('fixed response text: ', response)

    # archive the response
    behaviors.archive("text", "response", response, tID, network)

    # print response on the LP printer
    behaviors.print_response(plantoid, network, tID, response)
    
    # create a song
    style = "French chanson, vintage 1960s, deep contralto female vocal, smoky and grounded, intimate, melancholic, warm analog recording, sparse acoustic arrangement, upright bass, brushed drums, accordion, nylon string guitar, reverb-light, tape warmth"
    # audiofile = behaviors.generate_song(lines, credits)
    audiofile = behaviors.generate_song_suno(lines, style, credits)


    plantoid.send_serial_message("awake")
    
    # save and play the song
    behaviors.save_and_play_audio(plantoid, network, tID, audiofile)




def create_seed_metadata(plantoid, network, tID):


    # create the metadata information

    db = dict()
    db['name'] = tID
    db['description'] = "Plantoid #18 - Seed #" + tID
    db['external_url'] = "http://plantoid.org"
    db['image'] = "https://ipfs.io/ipfs/bafybeig3v2fag3tdlszyfgidpcgf24atvrkpwase3wekeu45jev4aourym"

    # behaviors.generic_metadata(plantoid, network, tID, db, None, behaviors.opera_make_video)

    behaviors.generic_metadata(plantoid, network, tID, db, None,
        behaviors.glitchbox_build_video_scheduler(
            lora="anglels-xl,pixel-xl",
            fps=10,
            strength=0.7,
            cn_scale=0.55,
        ),
        audio_merge=False,
    )





