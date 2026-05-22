from lib.plantoid.behaviors import behavior_library as behaviors


def ingurgitate_crypto(plantoid, network, tID, amount):

    question = "If your spirit had a mission to manifest in this world, what would it be?"

    behaviors.poem_generation(plantoid, network, tID, amount, question)


def create_seed_metadata(plantoid, network, tID):

    db = dict()
    # standard information for the record_metadata() function
    db['name'] = tID
    db['description'] = "Plantoid #19 - Seed #" + tID
    db['external_url'] = "http://plantoid.org"
    db['image'] = "https://ipfs.io/ipfs/bafybeig3v2fag3tdlszyfgidpcgf24atvrkpwase3wekeu45jev4aourym"
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
            strength=0.85,
            cn_scale=0.45,
            controlnet=True,
            mode="img2img",
        ),
        audio_merge=False,
    )










