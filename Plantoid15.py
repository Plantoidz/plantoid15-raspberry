import lib.plantoid.serial_utils as serial_utils
# import lib.plantoid.speech as speech
import lib.plantoid.web3_utils as web3_utils
# from lib.plantoid.core import *

from plantoids.plantoid import Plantony

from utils.util import load_config, str_to_bool

from dotenv import load_dotenv

import regex_spm
import time
import os

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
    # awake = 0

def mock_arduino_event_listen(ser, plantony, network, max_rounds=4):

    try:
        
        while True:

            print('checking if fed...')
            plantony.check_if_fed(network)

            print('checking if button pressed...')
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line == "button_pressed":

                    print("Button was pressed, Invoking Plantony!")
                    plantony.trigger('Touched', plantony, network, max_rounds=max_rounds)

            # only check every 10 seconds
            time.sleep(10)

    except KeyboardInterrupt:
        print("Program stopped by the user.")
        ser.close()

def main():

    # load config
    config = load_config('./configuration.toml')

    cfg = config['general']

    use_blockchain = str_to_bool(cfg['ENABLE_BLOCKCHAIN'])
    use_arduino = str_to_bool(cfg['ENABLE_ARDUINO'])
    max_rounds = cfg['max_rounds']

    web3_config = {
        'use_goerli': str_to_bool(cfg['USE_GOERLI']),
        'use_mainnet': str_to_bool(cfg['USE_MAINNET']),
        'use_goerli_address': cfg['USE_GOERLI_ADDRESS'],
        'use_mainnet_address': cfg['USE_MAINNET_ADDRESS'],
        'goerli_failsafe': cfg['GOERLI_FAILSAFE'],
        'mainnet_failsafe': cfg['MAINNET_FAILSAFE'],
    }

    # get output port from ENV
    PORT = os.environ.get('SERIAL_PORT_OUTPUT')

    # setup serial
    ser = serial_utils.setup_serial(PORT=PORT)

    # setup web3
    goerli, mainnet = web3_utils.setup_web3_provider(web3_config)

    print('goerli', goerli)
    print('mainnet', mainnet)

    # # process previous tx
    # if mainnet is not None: web3.process_previous_tx(mainnet)
    # if goerli is not None: web3.process_previous_tx(goerli)

    # instantiate plantony
    plantony = Plantony()

    # setup plantony
    plantony.setup()

    # add listener
    plantony.add_listener('Touched', invoke_plantony)

    # process previous tx
    web3_utils.process_previous_tx(goerli)

    # check for keyboard press
    mock_arduino_event_listen(ser, plantony, goerli, max_rounds=max_rounds)
    # serial_listen.listen_for_keyboard_press(ser)



    # trigger plantony
    # NOTE: this is a mocked event
    # plantony.trigger('Touched', plantony, max_rounds=max_rounds)

    # invoke plantony
    # invoke_plantony(plantony, max_rounds=max_rounds)

    # if use_blockchain and use_arduino: 

    #     serial_setup.setupSerial(serialPortName=serial_port_name)

    #     serial_setup.sendToArduino("thinking")

    #     goerli, mainnet = web3.setup_web3_provider()

    #     web3.process_previous_tx(mainnet)
    #     web3.process_previous_tx(goerli)

    #     serial_setup.sendToArduino("asleep")


    # while True:

    #     # check for a message from Arduino
    #     if use_arduino:
            
    #         arduinoReply = serial_setup.recvLikeArduino()
        
    #         if not (arduinoReply == 'XXX'):
    #             print("received... " + arduinoReply);

    #             match regex_spm.fullmatch_in(arduinoReply):
                
    #                 case r"Touched" as m:

    #                     if awake == 1:
    #                         awake = 0
    #                         serial_setup.sendToArduino("asleep")
                    
    #                     else:
    #                         awake = 1
    #                         serial_setup.sendToArduino("awake")

    #                         invoke_plantony(plantony, max_rounds=max_rounds)
    #                         awake = 0

            
    #     else:

    #         print('skipping arduino usage')
    #         invoke_plantony(plantony, max_rounds=max_rounds)

    #     # check for a message from the blockchain
    #     if use_blockchain:

    #         # check for a new Deposit event
    #         for network in (mainnet, goerli):

    #             mylist  = web3.check_for_deposits(network) ### this returns the token ID and the amount of wei that plantoid has been fed with

    #             if(mylist != None):  # Plantoid has been fed
                
    #                 (tID, amount) = mylist

    #                 print("got amount " + str(amount) + " for id = " + tID);

    #                 plantony.weaving()
                
    #                 audiofile = plantony.listen()
                
    #                 plantony.oracle(network, audiofile, network, tID, amount)

    #                 serial_setup.sendToArduino("thinking")
                
    #                 web3.create_metadata(network, tID)

    #                 serial_setup.sendToArduino("asleep")


                
if __name__ == "__main__":

    # seed = sys.argv[1]
    # path = "/home/pi/PLLantoid/v6/GOERLI/"

    # Execute main function
    main()




