from lib.plantoid.behaviors import behavior_library as behaviors
from lib.plantoid.text_content import default_intro_question

def ingurgitate_crypto(plantoid, network, tID, amount):

    #question = "How do you envision the relationship between humans, nature, and machines?"
    question = default_intro_question[plantoid.plantoid_number][plantoid.lang]
    user_speech = behaviors.ask_transcript(plantoid, network, tID, question)
    behaviors.poem_generation(plantoid, network, tID, amount, user_speech)


def create_seed_metadata(plantoid, network, tID):

    db = dict()
    # standard information for the record_metadata() function
    db['name'] = tID
    db['description'] = "Plantoid #17 - Seed #" + tID
    db['external_url'] = "http://plantoid.org"
    db['image'] = "https://ipfs.io/ipfs/QmePxb3kHQnD8x5jSvoMFCHBjwaNqt7vb9awaVPsL326Gh"
    # "https://ipfs.io/ipfs/bafybeihkjh6s7ofaxb2nzjcwod3hs7qvubfftixwu35m35z5ijug25wwx4"

    # behaviors.poem_metadata(plantoid, network, tID, db)
    #behaviors.generic_metadata(plantoid, network, tID, db, behaviors.poem_make_prompts, behaviors.poem_make_video )


    behaviors.generic_metadata(plantoid, network, tID, db,
        behaviors.poem_make_SDXLprompts,
        behaviors.glitchbox_build_video_journey(
            14, # prompt travelling
            network.plantoid_path + "/init_img.jpg",
            # **defaults
            lora="18", # melies
            target_frames=150,
            trigger="Vintage collage art featuring",
            strength=0.75,
            cn_scale=0.55,
            controlnet=True,
            mode="img2img",
        ),
        audio_merge=False,
    )










