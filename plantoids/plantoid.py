import random
import pygame
from playsound import playsound
import os
import threading
import time

from lib.plantoid.text_content import *
import lib.plantoid.speech as PlantoidSpeech
import lib.plantoid.serial_utils as PlantoidSerial
import lib.plantoid.web3_utils as web3_utils

class Plantony:

    def __init__(self):

        # user and agent names
        self.USER = "Human"
        self.AGENT = "Plantoid"

        # a list of events
        self._events = {}

        # whether to use the Arduino or not
        self.use_arduino = False

        # lines for the opening and closing
        self.opening = ""
        self.closing = ""
        self.prompt_text = ""

        # a round will contain a series of turns
        self.rounds = [[]]

        # # a turn will contain a series of interactions
        # self.turns = []

        # load the text content
        self.opening_lines, self.closing_lines, self.word_categories = get_text_content()

        # Load the sounds
        self.acknowledgements = [
            os.getcwd()+"/media/hmm1.mp3",
            os.getcwd()+"/media/hmm2.mp3",
        ];

        # Load the sounds
        self.introduction = os.getcwd()+"/samples/intro1.mp3"
        self.outroduction = os.getcwd()+"/samples/outro1.mp3"
        self.reflection = os.getcwd()+"/media/initiation.mp3"
        self.cleanse = os.getcwd()+"/media/cleanse.mp3"

    # def ambient_background(self, music, stop_event):

    #     while not stop_event.is_set():
    #         playsound(music)

    def add_listener(self, event_name, callback):

        # add the callback to the list of listeners
        if event_name not in self._events:
            self._events[event_name] = []
        
        # add the callback to the list of listeners
        self._events[event_name].append(callback)

    def remove_listener(self, event_name, callback):

        # remove the callback from the list of listeners
        if event_name in self._events:
            self._events[event_name].remove(callback)

    def trigger(self, event_name, *args, **kwargs):

        # trigger the event
        if event_name in self._events:
            for listener in self._events[event_name]:
                listener(*args, **kwargs)

    def setup(self):

        # load the personality of Plantony
        self.prompt_text = open(os.getcwd()+"/prompt_context/plantony_context.txt").read().strip()

        # select a random opening and closing line
        self.opening = random.choice(self.opening_lines)
        self.closing = random.choice(self.closing_lines) 

        # create a round
        self.append_turn_to_round(self.AGENT, self.opening)

        # for Plantony oracle
        self.selected_words = []

        # select one item from each category
        for category in self.word_categories:
            self.selected_words.append(random.choice(category['items']))

        # join the selected words into a comma-delimited string
        self.selected_words_string = ', '.join(self.selected_words)

        # print the result
        print("Plantony is setting up. His seed words are: " + self.selected_words_string)

    def play_background_music(self, filename):
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play(-1)  # Play on loop

    def stop_background_music(self):
        print('stop background music')
        pygame.mixer.music.stop()

    def welcome(self):

        print('Plantony Welcome!')
        print(self.introduction)

        if self.use_arduino:
            PlantoidSerial.sendToArduino("speaking")

        playsound(self.introduction)
        
        audiofile = PlantoidSpeech.get_text_to_speech_response(self.opening)
        print('plantony opening', self.opening)
        print("welcome plantony... opening = " + audiofile)
    
        playsound(audiofile)

    def terminate(self):

        if self.use_arduino:
            PlantoidSerial.sendToArduino("speaking")

        print('plantony closing', self.closing)
        playsound(PlantoidSpeech.get_text_to_speech_response(self.closing)) 
        playsound(self.outroduction)

        if self.use_arduino:
            PlantoidSerial.sendToArduino("asleep")

    def listen(self):

        if self.use_arduino:
            PlantoidSerial.sendToArduino("listening")

        audiofile = PlantoidSpeech.listen_for_speech()

        playsound(self.acknowledge())
        print("Plantony listen is returning the audiofile as:  " + audiofile)

        return audiofile

    def respond(self, audio):

        def prompt_agent_and_respond(audio, callback):
            
            # user text received from speech recognition
            user_message = PlantoidSpeech.recognize_speech(audio)

            print("I heard... " + user_message)

            if len(user_message) == 0:
                print('no text heard, using default text')
                user_message = "Hmmmmm..."

            # append the user's turn to the latest round
            self.append_turn_to_round(self.USER, user_message)

            agent_prompt = self.update_prompt()

            # print("new prompt = " + new_prompt)

            # generate the response from the GPT model
            agent_message = PlantoidSpeech.GPTmagic(agent_prompt, call_type='chat_completion')

            # append the agent's turn to the latest round
            self.append_turn_to_round(self.AGENT, agent_message)

            audio_file = PlantoidSpeech.get_text_to_speech_response(agent_message, callback=callback)
            # shared_response_container["audio_file"] = audio_file
            playsound(audio_file)

            # TODO: figure out if this goes here or above
            if self.use_arduino:
                PlantoidSerial.sendToArduino("speaking")

        if self.use_arduino:
            PlantoidSerial.sendToArduino("thinking")

        print("Plantony respond is receiving the audiofile as : " + audio)

        # get the path to the background music
        background_music_path = os.getcwd()+"/media/ambient3.mp3"

        # play the background music
        self.play_background_music(background_music_path)

        # prompt agent and respond
        prompt_agent_and_respond(audio, self.stop_background_music)

        # create a thread to call the API
        # thread = threading.Thread(target=prompt_agent_and_respond, args=(
        #     audio,
        #     after_elevenlabs_response,
        #     shared_response_container,
        # ))

        # # start the thread
        # thread.start()

        # # The script will continue to run while waiting for the API response
        # thread.join()  # This line ensures the script waits for the API thread to complete before proceeding

    def acknowledge(self):

        return random.choice(self.acknowledgements)

    def append_turn_to_round(self, agent, text):

        # initialize turn data
        turn_data = { "speaker": agent, "text": text }

        # append turn data to latest round
        self.rounds[-1].append(turn_data)

    def create_round(self):
        
        # create a new round
        self.rounds.append([])

    def reset_rounds(self):

        # reset the rounds
        self.rounds = []

    def update_prompt(self):

        # create a transcript from the rounds
        lines = []
        transcript = ""

        # iterate through the rounds
        for turns in self.rounds:

            # iterate through the turns
            for turn in turns:

                text = turn["text"]
                speaker = turn["speaker"]
                lines.append(speaker + ": " + text)

        # join the lines into a single string
        transcript = "\n".join(lines)

        return self.prompt_text.replace("{{transcript}}", transcript)
    
    def get_prompt(self):
        
        return self.prompt_text

    def reset_prompt(self):

        # load the personality of Plantony
        self.prompt_text = open(os.getcwd()+"/prompt_context/plantony_context.txt").read().strip()

        
    def weaving(self):
        
        if self.use_arduino:
            PlantoidSerial.sendToArduino("speaking")

        playsound(self.reflection)

    def generate_oracle(self, network, audio, tID, amount):

        if self.use_arduino:
            PlantoidSerial.sendToArduino("thinking")

        # get the path of the network
        path = network.path

        # get the path to the background music
        background_music_path = os.getcwd()+"/media/ambient3.mp3"

        # play the background music
        self.play_background_music(background_music_path)

        # get generated transcript
        generated_transcript = PlantoidSpeech.recognize_speech(audio)

        # print the generated transcript
        print("I heard... (oracle): " + generated_transcript)

        # if no generated transcript, use a default
        if not generated_transcript: 
            generated_transcript = get_default_sermon_transcript()

        # save the generated transcript to a file with the seed name
        if not os.path.exists(path + "/transcripts"):
            os.makedirs(path + "/transcripts");

        # save the generated response to a file with the seed name
        filename = path + f"/transcripts/{tID}_transcript.txt"
        with open(filename, "w") as f:
            f.write(generated_transcript)

        print("transcript saved as ..... " + filename)

        # TODO: re-enable
        # calculate the length of the poem
        # one line every 0.01 ETH for mainnet, one line every 0.001 ETH for goerli
        # n_lines = int(amount / web3obj.min_amount)  
        
        # if n_lines > 7: 
        #     n_lines = 7

        n_lines = 4

        print("generating transcript with number of lines = " + str(n_lines))
        
        # generate the sermon prompt
        prompt = get_sermon_prompt(
            generated_transcript,
            self.selected_words_string,
            n_lines
        )
        
        # get GPT response
        response = PlantoidSpeech.GPTmagic(prompt, call_type='completion')
        sermon_text = response.choices[0].text

        print('sermon text:')
        print(sermon_text)

        # save the generated response to a file with the seed name
        if not os.path.exists(path + "/responses"):
            os.makedirs(path + "/responses");

        # save the generated response to a file with the seed name
        filename = path + f"/responses/{tID}_response.txt"
        with open(filename, "w") as f:
            f.write(sermon_text)

        # now let's print to the LP0, with Plantoid signature
        # TODO: figure out what this is meant to do
        plantoid_sig = get_plantoid_sig(network, tID)

        # TODO: figure out what this is meant to do
        # os.system("cat " + filename + " > /dev/usb/lp0")
        # os.system("echo '" + plantoid_sig + "' > /dev/usb/lp0")

        # now let's read it aloud
        audiofile = PlantoidSpeech.get_text_to_speech_response(sermon_text)
        # stop_event.set() # stop the background noise

        # save the generated sermons to a file with the seed name
        if not os.path.exists(path + "/sermons"):
            os.makedirs(path + "/sermons");
        
        # save mp3 file
        os.system("cp " + audiofile + " " + path + f"/sermons/{tID}_sermon.mp3")

        # stop the background music
        self.stop_background_music()

        # play the oracle
        self.read_oracle(audiofile)


    def read_oracle(self, filename):

        if self.use_arduino:
            PlantoidSerial.sendToArduino("speaking");
        
        playsound(filename)
        time.sleep(1)
        
        if self.use_arduino:
            PlantoidSerial.sendToArduino("asleep");
        
        playsound(self.cleanse)

        print('oracle read completed!')

    def check_if_fed(self, network):

        ### this returns the token ID and the amount of wei that plantoid has been fed with
        latest_deposit  = web3_utils.check_for_deposits(network) 

        # If Plantoid has been fed
        if latest_deposit is not None:  

            print('deposit found!')
        
            # get the token ID and the amount of wei that plantoid has been fed with
            (tID, amount) = latest_deposit

            print("got amount " + str(amount) + " for id = " + tID);

            self.weaving()
        
            # listen for audio
            audiofile = self.listen()

            print('Early termination of check if fed.')
        
            # # generate the oracle
            # self.generate_oracle(network, audiofile, tID, amount)

            # if self.use_arduino:
            #     PlantoidSerial.sendToArduino("thinking")
        
            # # create the metadata
            # web3.create_metadata(network, tID)

            # if self.use_arduino:
            #     PlantoidSerial.sendToArduino("asleep")

        else:

            print("no deposits detected. DEBUG: proceeding with oracle generation")

            # listen for audio
            audiofile = self.listen()
            tID = '0xABC'
            amount = 0.001

            # generate the oracle
            self.generate_oracle(network, audiofile, tID, amount)

            # create the metadata
            web3_utils.create_metadata(network, tID)
