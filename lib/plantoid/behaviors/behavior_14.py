from lib.plantoid.behaviors import behavior_library as behaviors


def ingurgitate_crypto(plantoid, network, tID, amount):

    question = "What is the future you're dreaming of?"

    behaviors.poem_generation(plantoid, network, tID, amount, question)


def create_seed_metadata(plantoid, network, tID):

    db = dict()
    # standard information for the record_metadata() function
    db['name'] = tID
    db['description'] = "Plantoid #14 - Seed #" + tID
    db['external_url'] = "http://plantoid.org"
    db['image'] = "https://ipfs.io/ipfs/QmWeAE8pLiLdSdwHVtvDBWtw49WDY4huH7XhCLedHvjSjp"
    # "https://ipfs.io/ipfs/QmRcrcn4X6QfSwFnJQ1dNHn8YgW7pbmm6BjZn7t8FW7WFV"


    # behaviors.poem_metadata(plantoid, network, tID, db)
    
    # OLD APPROVED BEHAVIOR
    #behaviors.generic_metadata(plantoid, network, tID, db, behaviors.poem_make_prompts, behaviors.poem_make_video )
    
    behaviors.generic_metadata(plantoid, network, tID, db,
        behaviors.poem_make_SDXLprompts,
        behaviors.glitchbox_build_video_journey(
            14,
            network.plantoid_path + "/init_img.jpg",
            # **defaults
            lora="18",
            trigger="Vintage collage art featuring",
            target_frames=200,
            strength=0.7,
            cn_scale=0.55,
            controlnet=True,
            mode="img2img",
        ),
        audio_merge=False,
    )













