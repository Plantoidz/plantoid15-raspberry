import lib.plantoid.web3_utils as web3_utils
from dotenv import load_dotenv
from utils.util import load_config, get_working_path, str_to_bool
import os

def main():

    load_dotenv()

    use_raspeberry = str_to_bool(os.environ.get("USE_RASPBERRY"))
    use_arduino = str_to_bool(os.environ.get("USE_ARDUINO"))
    raspberry_path = os.environ.get("RASPBERRY_PATH")
    print("raspberry_path === ", raspberry_path)

    # load config
    path = get_working_path(use_raspeberry, raspberry_path)
    config = load_config(path+'/configuration.toml')

    cfg = config['general']
    plantoid_number = str(cfg['PLANTOID']) # find out which plantoid we are working on

    plantoid_cfg = config[plantoid_number]

    eleven_voice_id = plantoid_cfg['ELEVEN_VOICE_ID'] # set up the voice of the plantoid
    max_rounds = plantoid_cfg['max_rounds'] # set up the number of rounds for the plantoid


    plantoid_goerli_cfg = plantoid_cfg["goerli"]
    plantoid_mainnet_cfg = plantoid_cfg["mainnet"]
    use_goerli = str_to_bool(plantoid_goerli_cfg["ACTIVE"])
    use_mainnet = str_to_bool(plantoid_mainnet_cfg["ACTIVE"])
    print("mainnet == ", use_mainnet, " and goerli == ", use_goerli)

   # path = cfg['PATH']

   # use_plantoid = 'plantoid_'+str(cfg['PLANTOID'])
   # use_blockchain = str_to_bool(cfg['ENABLE_BLOCKCHAIN'])
   # trigger_line = cfg['TRIGGER_LINE']
   # eleven_voice_id = cfg['ELEVEN_VOICE_ID']

   # use_goerli = str_to_bool(cfg['USE_GOERLI'])
   # use_mainnet = str_to_bool(cfg['USE_MAINNET'])

    web3_config = {
        'use_goerli': use_goerli,
        'use_mainnet': use_mainnet,
        'use_goerli_address': plantoid_goerli_cfg['BLOCKCHAIN_ADDRESS'],
        'use_mainnet_address': plantoid_mainnet_cfg['BLOCKCHAIN_ADDRESS'],
        'use_metadata_address': plantoid_mainnet_cfg['METADATA_ADDRESS'],
        'goerli_failsafe': plantoid_goerli_cfg['FAILSAFE'],
        'mainnet_failsafe': plantoid_mainnet_cfg['FAILSAFE'],
        'path': path,
        'plantoid_path': path + "/" + plantoid_number + "/",
        'plantoid_number': plantoid_number,
    }


    mainnet = web3_setup_loop_mainnet(web3_config)
    web3_utils.enable_seed_reveal(mainnet, 40)


def web3_setup_loop_mainnet(web3_config):

    connected = False

    while connected == False:

        # setup web3
        mainnet = web3_utils.setup_web3_provider_mainnet(web3_config)
        print(mainnet)

        if (mainnet is not None):
            connected = True  

    return mainnet


if __name__ == "__main__":

    # Execute main function
    main()