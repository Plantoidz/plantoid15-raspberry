import time
import os
import re
import lib.plantoid.serial_utils as serial_utils
import lib.plantoid.web3_utils as web3_utils
from plantoids.plantoid import Plantony
from utils.util import load_config, get_working_path, str_to_bool
from dotenv import load_dotenv
import regex_spm


def invoke_plantony(plantony: Plantony, network, max_rounds=12):

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

def plantoid_event_listen(
        ser,
        plantony,
        web3config,
        max_rounds=4,
        use_raspberry=False,
    ):


    pattern = serial_utils.use_serial_pattern(use_raspberry)


    counter = 0  ### TODO: this is a dirty trick i'm using in order to ensure that the loop constantly checks for arduino signals, but doesn't overload infura with web3 requests every milliseconds  


    try:

        while True:
        


            

            print('checking if button pressed...')
            print('serial wait count:', ser.in_waiting)
            if ser.in_waiting > 0:

                try:

                    line = ser.readline().decode('utf-8').strip()
                    print("line ====", line)
                    print("pattern ============= ", pattern)

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
            time.sleep(1)

            
            # increase counter and only check for deposits events every 10 seconds

            counter = counter + 1
            if(counter % 10):   continue   



            
            if(web3config["use_goerli"]):
                print('checking if fed on GOERLI...')
 
                try:
                    plantony.check_if_fed(web3config["goerli"])

                except Exception as e:
                    print("********* ERROR on websocket: ", e)
                    web3config["goerli"] = web3_setup_loop_goerli(web3config)
            
            
            if(web3config["use_mainnet"]):
                print('checking if fed on MAINNET...')

                try:
                    plantony.check_if_fed(web3config["mainnet"])

                except Exception as e:
                    print("********* ERROR on websocket: ", e)
                    web3config["mainnet"] = web3_setup_loop_mainnet(web3config)



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
    lang = plantoid_cfg['LANG'] # check if a particular language is set
    personality = plantoid_cfg['PERSONALITY'] # load the personality prompt context


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

    if use_goerli:
        goerli = web3_setup_loop_goerli(web3_config)
        web3_config["goerli"] = goerli
        print(goerli)

    if use_mainnet:
        mainnet = web3_setup_loop_mainnet(web3_config)
        web3_config["mainnet"] = mainnet
        print(mainnet)


    # instantiate plantony with serial
    plantony = Plantony(ser, eleven_voice_id, int(plantoid_number), path, lang, personality)

    # setup plantony
    plantony.setup()

    # process previous tx
    if mainnet is not None: web3_utils.process_previous_tx(plantony, mainnet)
    if goerli is not None: web3_utils.process_previous_tx(plantony, goerli)

    # invoke_plantony(plantony, goerli)

    # add listener
    plantony.add_listener('Touched', invoke_plantony)

    # check for crypto-transactions and serial communications
    plantoid_event_listen(
        ser,
        plantony,
        web3_config,
        max_rounds=max_rounds,
        use_raspberry=use_raspeberry,
    )
   
    # plantoid_event_listen(ser, plantony, goerli, trigger_line, max_rounds=max_rounds)
    # serial_listen.listen_for_keyboard_press(ser)



if __name__ == "__main__":

    # Execute main function
    main()
