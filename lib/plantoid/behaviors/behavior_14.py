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
    db['image'] = "https://ipfs.io/ipfs/QmRcrcn4X6QfSwFnJQ1dNHn8YgW7pbmm6BjZn7t8FW7WFV"


    # behaviors.poem_metadata(plantoid, network, tID, db)
    behaviors.generic_metadata(plantoid, network, tID, db, behaviors.poem_make_prompts, behaviors.poem_make_video )














