from lib.plantoid.behaviors import behavior_library as behaviors
from lib.plantoid.text_content import default_intro_question
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

    #question = "What is your deepest belief that you cherrish in your heart?"
    question = default_intro_question[plantoid.plantoid_number][plantoid.lang]
    user_speech = behaviors.ask_transcript(plantoid, network, tID, question)


    style = "Deep Tibetan Buddhist throat singing, multiphonic undertone, guttural ritual chant, low fundamental frequency,  slow drone composition, no melody, no rhythm, sustained ominous resonance, glitches"
    behaviors.song_generation(plantoid, network, tID, amount, user_speech, style)

    # Generate response  ..
    # plantoid.send_serial_message("thinking")
    
    # # calculate the credits for the response
    # # one line every 0.01 ETH for mainnet, one line every 0.001 ETH for goerli
    # credits = int(amount / network.min_amount)  

    # lines = behaviors.get_song_prompts(plantoid, user_speech, credits)
    
    # response = '\n'.join(lines)
    # print('fixed response text: ', response)

    # # archive the response
    # behaviors.archive("text", "response", response, tID, network)

    # # print response on the LP printer
    # behaviors.print_response(plantoid, network, tID, response)

    
    # # create a song with 11LABS
    # # style = {
    # #     'positive_global_styles': ['French chanson', 'vintage 1960s', 'deep contralto female vocal', 'smoky and grounded', 'warm analog recording', 'sparse acoustic arrangement', 'upright bass', 'brushed drums', 'tape warmth'],
    # #     'negative_global_styles': ['electronic', 'heavy percussion', 'modern synth', 'rock'],
    # #     'positive_local_styles': ['intimate', 'melancholic'],
    # #     'negative_local_styles': ['heavy brass', 'percussion', 'electronic sounds'],       
    # # }
    # # audiofile = behaviors.generate_song_11labs(lines, style, credits)




    # # create a song with SUNO
    # style = "French chanson, vintage 1960s, deep contralto female vocal, smoky and grounded, intimate, melancholic, warm analog recording, sparse acoustic arrangement, upright bass, brushed drums, accordion, nylon string guitar, reverb-light, tape warmth"
    # audiofile = behaviors.generate_song_suno(lines, style, credits)


    # plantoid.send_serial_message("awake")
    
    # # save and play the song
    # behaviors.save_and_play_audio(plantoid, network, tID, audiofile)




def create_seed_metadata(plantoid, network, tID):


    # create the metadata information

    db = dict()
    db['name'] = tID
    db['description'] = "Plantoid #20 - Seed #" + tID
    db['external_url'] = "http://plantoid.org"
    db['image'] = "https://ipfs.io/ipfs/bafybeid7ijkuk22zptyqr7jyjynvq2gwkjvngj5f76sghioidsv7fvzb7e"

    # behaviors.generic_metadata(plantoid, network, tID, db, None, behaviors.opera_make_video)

    behaviors.generic_metadata(plantoid, network, tID, db, None,
        behaviors.glitchbox_build_video_scheduler(
            lora="water-xl,robwood-xl",
            fps=5,
            strength=0.9,
            cn_scale=0.55,
            video_set="tribal_shutterstock",
            #audio_band="bass",
            audio_alpha_mode="excitation",
        ),
        audio_merge=False,
    )





