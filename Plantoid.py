import time
import os
import re
import lib.plantoid.serial_utils as serial_utils
import lib.plantoid.web3_utils as web3_utils
from plantoids.plantoid import Plantony
from utils.util import load_config, str_to_bool
from dotenv import load_dotenv
import regex_spm



def invoke_plantony(plantony: Plantony, network, max_rounds=4):

    print('plantony initiating...')
    plantony.welcome()

    print('Iterating on Plantony n of rounds:', len(plantony.rounds), 'max rounds:', max_rounds)

    while(len(plantony.rounds) < max_rounds):

        # create the round
        plantony.create_round()

        print('plantony rounds...')
        print(len(plantony.rounds))

        print('plantony listening...')
        audiofile = plantony.listen()

        print('plantony responding...')
        plantony.respond(audiofile)

    # TODO: sub function without speech
    print('plantony listening...')
    plantony.listen()

    print('plantony terminating...')
    plantony.terminate()

    # print('checking if fed...')
    # plantony.check_if_fed(network)

    # print('debug: plantony rounds...')
    # print(plantony.rounds)

    plantony.reset_rounds()
    plantony.reset_prompt()

def plantoid_event_listen(ser, plantony, web3config, max_rounds):


    # temp
    pattern = r"<(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3})>"

    try:

        while True:

            if(web3config["use_goerli"]):
                print('checking if fed on GOERLI...')

                is_connected = web3config["goerli"].w3.is_connected()
                print(is_connected)
                if(not is_connected ):
                    time.sleep(2)
                    web3config["goerli"] = web3_setup_loop_goerli(web3config)
                    
                plantony.check_if_fed(web3config["goerli"])
            
            if(web3config["use_mainnet"]):
                print('checking if fed on MAINNET...')
                if(not web3config["goerli"].w3.is_connected()):
                    web3config["mainnet"] = web3_setup_loop_mainnet(web3config)
                    
                plantony.check_if_fed(web3config["mainnet"])

            print('checking if button pressed...')
            print('serial wait count:', ser.in_waiting)
            if ser.in_waiting > 0:

                try:

                    line = ser.readline().decode('utf-8').strip()
                    print("line ====", line)

                    condition = bool(re.fullmatch(pattern, line))
                    print("condition", condition)

                    if condition == True:

                        # Trigger plantony interaction
                        print("Button was pressed, Invoking Plantony!")
                        plantony.trigger('Touched', plantony, web3config["goerli"], max_rounds=max_rounds)  ## FIX ME

                        # Clear the buffer after reading to ensure no old "button_pressed" events are processed.
                        ser.reset_input_buffer()

                except UnicodeDecodeError:
                    
                    print("Received a line that couldn't be decoded!")

            # only check every 5 seconds
            time.sleep(2)

    except KeyboardInterrupt:
        print("Program stopped by the user.")

    finally:
        ser.close()


def web3_setup_loop_goerli(web3_config):

    connected = False

    while connected == False:

        # setup web3
        goerli = web3_utils.setup_web3_provider_goerli(web3_config)
        print(goerli)

        if (goerli is not None):
            connected = True  

    return goerli


def web3_setup_loop_mainnet(web3_config):

    connected = False

    while connected == False:

        # setup web3
        mainnet = web3_utils.setup_web3_provider_mainnet(web3_config)
        print(mainnet)

        if (mainnet is not None):
            connected = True  

    return mainnet


def main():

    # load config
    # path = os.getcwd()
    path = "/home/pi/PLLantoid/plantoid15-raspberry/"   ## TODO: find a way to give path in the config file
    config = load_config(path+'/configuration.toml')

    cfg = config['general']
    plantoid_n = str(cfg['PLANTOID']) # find out which plantoid we are working on

    plantoid_cfg = config[plantoid_n]

    eleven_voice_id = plantoid_cfg['ELEVEN_VOICE_ID'] # set up the voice of the plantoid
    max_rounds = plantoid_cfg['max_rounds'] # set up the number of rounds for the plantoid
    use_arduino = str_to_bool(plantoid_cfg['ENABLE_ARDUINO'])


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
    }

    # get output port from ENV
    PORT = os.environ.get('SERIAL_PORT_OUTPUT')

    # setup serial
    ser = serial_utils.setup_serial(PORT=PORT)

    # setup signals
    if use_arduino:
        serial_utils.wait_for_arduino(ser)
        serial_utils.send_to_arduino(ser, "awake")  

    mainnet = None;
    goerli = None;

    if(use_goerli):
        goerli = web3_setup_loop_goerli(web3_config)
        web3_config["goerli"] = goerli
        print(goerli)
    if(use_mainnet):
        mainnet = web3_setup_loop_mainnet(web3_config)
        web3_config["mainnet"] = mainnet
        print(mainnet)

    # process previous tx
    if mainnet is not None: web3_utils.process_previous_tx(mainnet)
    if goerli is not None: web3_utils.process_previous_tx(goerli)

    # instantiate plantony with serial
    plantony = Plantony(ser, eleven_voice_id)

    # setup plantony
    plantony.setup()

    # add listener
    plantony.add_listener('Touched', invoke_plantony)

    # check for crypto-transactions and serial communications
    plantoid_event_listen(ser, plantony, web3_config, max_rounds=max_rounds)
   
    # plantoid_event_listen(ser, plantony, goerli, trigger_line, max_rounds=max_rounds)
    # serial_listen.listen_for_keyboard_press(ser)



if __name__ == "__main__":

    # Execute main function
    main()
