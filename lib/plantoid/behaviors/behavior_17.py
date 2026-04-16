from lib.plantoid.behaviors import behavior_library as behaviors


def ingurgitate_crypto(plantoid, network, tID, amount):

    question = "How do you envision the relationship between humans, nature, and machines?"

    behaviors.poem_generation(plantoid, network, tID, amount, question)


def create_seed_metadata(plantoid, network, tID):

    description = "Plantoid #17 - Seed #" + tID
    image = "https://ipfs.io/ipfs/bafybeihkjh6s7ofaxb2nzjcwod3hs7qvubfftixwu35m35z5ijug25wwx4"


    behaviors.poem_metadata(plantoid, network, tID, description, image)













