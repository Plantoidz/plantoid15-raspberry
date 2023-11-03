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

def mock_arduino_event_listen(ser, plantony, network, trigger_line, max_rounds=4):


    # temp
    pattern = r"<(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3})>"

    try:

        while True:

            print('checking if fed...')
            plantony.check_if_fed(network)

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
                        plantony.trigger('Touched', plantony, network, max_rounds=max_rounds)

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


def web3_setup_loop(web3_config, use_goerli, use_mainnet):

    connected = False

    while connected == False:

        # setup web3
        goerli, mainnet = web3_utils.setup_web3_provider(web3_config)
        print(mainnet)
        print(goerli)

        if (goerli is not None and use_goerli) or (mainnet is not None and use_mainnet):

            connected = True

    return goerli, mainnet

def main():

    # load config
    config = load_config(os.getcwd()+'/configuration.toml')

    cfg = config['general']

    use_plantoid = 'plantoid_'+str(cfg['PLANTOID'])
    use_blockchain = str_to_bool(cfg['ENABLE_BLOCKCHAIN'])
    use_arduino = str_to_bool(cfg['ENABLE_ARDUINO'])
    max_rounds = cfg['max_rounds']
    trigger_line = cfg['TRIGGER_LINE']
    eleven_voice_id = cfg['ELEVEN_VOICE_ID']

    use_goerli = str_to_bool(cfg['USE_GOERLI'])
    use_mainnet = str_to_bool(cfg['USE_MAINNET'])

    web3_config = {
        'use_goerli': use_goerli,
        'use_mainnet': use_mainnet,
        'use_goerli_address': cfg[use_plantoid]['USE_GOERLI_ADDRESS'],
        'use_mainnet_address': cfg[use_plantoid]['USE_MAINNET_ADDRESS'],
        'use_metadata_address': cfg[use_plantoid]['USE_METADATA_ADDRESS'],
        'goerli_failsafe': cfg['GOERLI_FAILSAFE'],
        'mainnet_failsafe': cfg['MAINNET_FAILSAFE'],
    }

    # get output port from ENV
    PORT = os.environ.get('SERIAL_PORT_OUTPUT')

    # setup serial
    ser = serial_utils.setup_serial(PORT=PORT)

    # setup signals
    if use_arduino:
        serial_utils.wait_for_arduino(ser)
        serial_utils.send_to_arduino(ser, "awake")  

    goerli, mainnet = web3_setup_loop(web3_config, use_goerli, use_mainnet)

    # process previous tx
    # if mainnet is not None: web3_utils.process_previous_tx(mainnet)
    if goerli is not None: web3_utils.process_previous_tx(goerli)

    # instantiate plantony with serial
    plantony = Plantony(ser, eleven_voice_id)

    # setup plantony
    plantony.setup()

    # add listener
    plantony.add_listener('Touched', invoke_plantony)

    # check for keyboard press
    mock_arduino_event_listen(ser, plantony, goerli, trigger_line, max_rounds=max_rounds)
    # serial_listen.listen_for_keyboard_press(ser)

if __name__ == "__main__":

    # Execute main function
    main()
