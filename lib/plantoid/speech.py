#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class

import speech_recognition as sr
import pygame

import pyaudio
import wave
import audioop
import struct

import threading

import numpy as np

from collections import deque

from playsound import playsound

from dotenv import load_dotenv

import openai
import requests

#from elevenlabs import Voice, VoiceSettings, generate, stream, set_api_key
from elevenlabs.client import ElevenLabs
from elevenlabs import stream

import random
import os
import sys
import time

from ctypes import *
from contextlib import contextmanager

from utils.default_prompt_config import default_chat_completion_config, default_completion_config
from utils.util import load_config, str_to_bool

@contextmanager
def ignoreStderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)

    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)

# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 44100
# CHUNK = 512
# RECORD_SECONDS = 2 #seconds to listen for environmental noise
# AUDIO_FILE = "/tmp/temp_reco.wav"
# device_index = 6

# #define the silence threshold
# # THRESHOLD = 250     # Raspberry uses 150
# SILENCE_LIMIT = 4   # seconds of silence will stop the recording

# FORMAT = pyaudio.paInt16      # standard USB MIC
FORMAT = pyaudio.paInt32        # mic I2S
CHANNELS = 1
RATE = 44100
CHUNK = 512

TIMEOUT = 20
SILENCE_LIMIT = 5.0   # seconds of silence will stop the recording
THRESHOLD = 20
THRESHOLD_DB = -70
# RECORD_SECONDS = 2 #seconds to listen for environmental noise

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.environ.get("OPENAI")
eleven_labs_api_key = os.environ.get("ELEVEN")
elevenlabs = ElevenLabs(api_key=eleven_labs_api_key)


# VOICE_ID to ELEVENLABS_VOICE_ID mapping
voice_ids = {}
voice_ids["plantony"] = "o7lPjDgzlF8ZloHzVPeK"
voice_ids["trevor"] = "KRzS7KO2TLlh1BRPgHnB"
voice_ids["primavera"] = "txtf1EDouKke753vN8SL"
voice_ids["iannis"] = "ejJ1ETWS2ohLMMeCu1H3"



def play_background_music_INTERNAL(filename, loops=-1):
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play(loops)



def GPTmagic(prompt, model="gpt-4"):

    import requests as req
    
    #1. Try MacBook LLM Studio
    try:
        url = "http://100.67.155.96:1234/v1/chat/completions"
        payload =  {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 128,
        }
        resp = req.post(url, json=payload, timeout=10)
        print("trying LLM MacBook with resp.status_code = ", resp.status_code) 

        if resp.status_code == 200:
            print("LLM - using MacBook LM Studio ({model})")
            content = resp.json()["choices"][0]["message"]["content"]
            print("Trimmed content ==> ", content)
            trimmed = trim_to_sentence(content)
            return trimmed

    except Exception:
        pass

    #2. Try GLITCHBOX LLM Studio (hard-coded model: liquid)
    try:
        url = "http://100.79.41.86:1234/v1/chat/completions"
        payload =  {
            "model": "qwen3.5-2b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 128,
        } 
        resp = req.post(url, json=payload, timeout=30)
        print("trying LLM GLITCHBOX with resp.status_code = ", resp.status_code) 

        if resp.status_code == 200:
            print("LLM - using GLITCHBOX LM Studio (LIQUID IS HARDCODED)")
            content = resp.json()["choices"][0]["message"]["content"]
            print("Trimmed content ==> ", content)
            trimmed = trim_to_sentence(content)
            return trimmed

    except Exception:
        pass 

   # 3. Fallback to GPT-4
    if (model == "gpt-4"):
        print("LLM - Fallbacking to OpenAI GPT-4")
        config = default_chat_completion_config(model="gpt-4")
        response = openai.ChatCompletion.create(
          messages=[{"role": "user", "content": prompt}], **config
        )
        content = response.choices[0].message.content
        print("Trimmed content ==> ", content)
        trimmed = trim_to_sentence(content)
        return trimmed


def trim_to_sentence(text):
      # find the last sentence-ending punctuation
      for i in range(len(text) - 1, -1, -1):
          if text[i] in '.!?"':
              return text[:i+1]
      return text



def GPTmagic_old2(prompt, call_type='chat_completion', model="gpt-4"): # model: "qwen/qwen3.5-35b-a3b", "qwen/qwen3.5-27b", "liquid/lfm2.5-1.2b" 

    # default: OpenAI GPT
    if (model == "gpt-4"):
        print("Using default OpenAI GPT")
        config = default_chat_completion_config(model="gpt-4")
        response = openai.ChatCompletion.create(
          messages=[{"role": "user", "content": prompt}], **config
        )
        return response.choices[0].message.content




    else :  # use LOCAL LLM 
            # --> first try to connect on the local MacBook (100.67.155.96)
            # --> and then on the GLITCHBOX (100.79.41.86)

          import requests as req
          print("testing if Studio LLM is running on local MacBook.. ")
          print("testing if Studio LLM is running on GLITCHBOX.. ")

          url = f"http://192.168.10.130:1234/v1/chat/completions" ## hard-coded, doesn't need to be configured
          payload = {
              # "model": "qwen/qwen3.5-35b-a3b",
              # "model": "qwen/qwen3.5-27b",
              # "model": "liquid/lfm2.5-1.2b",
              "model": model,
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.7,
          }
          resp = req.post(url, json=payload, timeout=120)
          
          if resp.status_code != 200:
            print("LLM error: ", resp.status_code, resp.text)
          resp.raise_for_status()
          
          return resp.json()["choices"][0]["message"]["content"]




def GPTmagic_old(prompt, call_type='chat_completion'): 

    # allowable kwargs
    allowable_call_types = ['chat_completion', 'completion']

    assert call_type in allowable_call_types, "The provided call type is not implemented"

    if call_type == 'chat_completion':

        # Prepare the GPT magic
        config = default_chat_completion_config(model="gpt-4")
#        config = default_chat_completion_config()

        print("generating GPT magic response.............")

        try:
            # Generate the response from the GPT model
            response = openai.ChatCompletion.create(messages=[{
                "role": "user",
                "content": prompt,
            }], **config)

            messages = response.choices[0].message.content
       
        except Exception as e:
            print("Exception occured", e)

        return messages
    
    if call_type == 'completion':
        # # The GPT-3.5 model ID you want to use
        # model_id = "text-davinci-003"

        # # The maximum number of tokens to generate in the response
        # max_tokens = 1024

        config = default_completion_config()


        try:
            # Generate the response from the GPT-3.5 model
            response = openai.Completion.create(
                prompt=prompt,
                **config,
            )
        except Exception as e:
            print("Exception occured", e)

        return response


def get_text_to_speech_response(text, voice_id, callback=None):

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": eleven_labs_api_key,
    }

    #eleven_voice_id = '21m00Tcm4TlvDq8ikWAM' # Rachel
    url = "https://api.elevenlabs.io/v1/text-to-speech/"+ voice_ids[voice_id]

    # Request TTS from remote API
    response = requests.post(
        url,
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0,
                "similarity_boost": 0
            },
        },
        headers=headers,
    )

    if response.status_code == 200:
        # Save remote TTS output to a local audio file with an epoch timestamp

        print('elevenlabs response received')

        if callback is not None:
            callback()
            
        filename = f"/tmp/tonyspeak.mp3"
        with open(filename, "wb") as f:
            f.write(response.content)
        
        # playsound(filename)
        return filename
    
    else:

        raise Exception("Error: " + str(response.status_code))
    


def stream_response(agent_message, voiceid="plantony"):

    import requests as req

    def extract_pcm(data):
        out, i = bytearray(), 0
        while i < len(data):
            if i + 12 <= len(data) and data[i:i+4] == b'RIFF' and data[i+8:i+12] == b'WAVE':
                j = i + 12
                while j + 8 <= len(data):
                    if data[j:j+4] == b'data': i = j + 8; break
                    j += 8 + struct.unpack_from('<I', data, j+4)[0]
                else: i +=44
            else: out.append(data[i]); i += 1
        return out

    def play_streaming_tts(resp, default_sr=24000):
        ring, lock, done = bytearray(), threading.Lock(), False

        def cb(in_data, frames, t, status):
            n = frames * 2
            with lock:
                if len(ring) >= n:
                    out = bytes(ring[:n]); del ring[:n]; return (out, pyaudio.paContinue)
                if done and not ring: return (b'\x00' * n, pyaudio.paComplete)
                out = bytes(ring) + b'\x00' * (n - len(ring)); ring.clear()
                return (out, pyaudio.paContinue)

        with ignoreStderr():
            p = pyaudio.PyAudio()
        stream_out, sr = None, None

        for chunk in resp.iter_content(chunk_size=4096):
            if not sr:
                if len(chunk) >= 44 and chunk[:4] == b'RIFF':
                    sr = struct.unpack_from('<I', chunk, 24)[0]
                else:
                    sr = default_sr
            
            pcm = extract_pcm(chunk)
            if pcm:
                with lock: ring.extend(pcm)
            if not stream_out and sr and len(ring) >= 144000:
                stream_out = p.open(format=pyaudio.paInt16, channels=1, rate=sr,
                                    output=True, frames_per_buffer=2048, stream_callback=cb)
                stream_out.start_stream()

        if not stream_out and ring and sr:
            stream_out = p.open(format=pyaudio.paInt16, channels=1, rate=sr,
                                output=True, frames_per_buffer=2048, stream_callback=cb)
            stream_out.start_stream()

        done = True
        if stream_out:
            while stream_out.is_active(): time.sleep(0.05)
            stream_out.stop_stream(); stream_out.close()
        p.terminate()

    # 1. try MacBookPro
    try:
        ref_audio = f"/Users/ya/Desktop/PLANTOID 22/WHISPER/QwenTTS/voice-samples/{voiceid}.mp3"
        ref_text = "Hello my name is Plantoid, I am a blockchain-based lifeform. I feed off cryptocurrency in order to replicate myself."

        resp = req.post("http://100.67.155.96:8000/v1/audio/speech", json = {
            "model": "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16",
            "input": agent_message,
            "ref_audio": ref_audio, "ref_text": ref_text,
            "response_format": "wav",
            "stream": True, "streaming_interval": 2.0,
          }, timeout=10, stream=True)

        if resp.status_code == 200:
            print(f"TTS - using MacBookPro ({voiceid})")
            play_streaming_tts(resp, default_sr=24000)
            return
    except Exception as e:
        print(f"MacBookPro TTS failed: {e}")
        

    # 2. try Glitchbox
    print("option 3: trying GLITCHBOX")
    try:
        resp = req.post("http://100.79.41.86:8000/v1/audio/speech", json = {
            "model" : "qwen-tts",
            "input" : agent_message,
            "voice" : f"clone:{voiceid}",
            "response_format" : "wav",
            "stream" : True,
            "streaming_interval" : 2.0,
        }, timeout=20, stream=True)

        if resp.status_code == 200:
            print(f"TTS - using Glitchbox (clone: {voiceid})")
            play_streaming_tts(resp, default_sr=24000)
            return
    except Exception as e:
        print(f"Glitchbox TTS failed: {e}")



    # 3. fallback to Elevenlabs

    print("TTS - falling back to ElevenLabs")
    audio_stream = elevenlabs.text_to_speech.stream(
        text=agent_message,
        model_id="eleven_multilingual_v2",
        voice_id=voice_ids[voiceid],
    )
    stream(audio_stream)




def stream_response_old(agent_message, voiceid):
            audio_stream = elevenlabs.text_to_speech.stream(
                text=agent_message,
             #  model="eleven_turbo_v2",
                model_id="eleven_multilingual_v2",
                voice_id=voiceid,
            )
            stream(audio_stream)


def compute_average(fragment, sample_width=2):
    """Compute the raw average of audio samples."""
    
    # Number of samples in the fragment
    num_samples = len(fragment) // sample_width

    # Unpack the audio samples
    if sample_width == 1:
        fmt = f"{num_samples}B"  # Unsigned byte
        samples = struct.unpack(fmt, fragment)
        # Convert to signed values in the range -128 to 127
        samples = [s - 128 for s in samples]
    elif sample_width == 2:
        fmt = f"{num_samples}h"  # Short
        samples = struct.unpack(fmt, fragment)
    else:
        raise ValueError("Unsupported sample width")
    
    # Compute the average
    avg = sum(samples) / num_samples
    return avg

def compute_median(fragment, sample_width=2):
    """Compute the median of audio samples."""
    
    # Number of samples in the fragment
    num_samples = len(fragment) // sample_width

    # Unpack the audio samples
    if sample_width == 1:
        fmt = f"{num_samples}B"  # Unsigned byte
        samples = struct.unpack(fmt, fragment)
        # Convert to signed values in the range -128 to 127
        samples = [s - 128 for s in samples]
    elif sample_width == 2:
        fmt = f"{num_samples}h"  # Short
        samples = struct.unpack(fmt, fragment)
    else:
        raise ValueError("Unsupported sample width")

    # Compute the median
    sorted_samples = sorted(samples)
    mid = num_samples // 2
    if num_samples % 2 == 0:  # even number of samples
        median = (sorted_samples[mid - 1] + sorted_samples[mid]) / 2
    else:
        median = sorted_samples[mid]
    
    return median

def adjust_sound_env(stream, device_bias=0): ## important in order to adjust the THRESHOLD based on environmental noise
    
    data = []
    noisy = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)

        manual_average = abs(compute_average(data, sample_width=2))
        manual_median = abs(compute_median(data, sample_width=2))
        audioop_average = abs(audioop.avg(data, 2))

        # print("manual median", manual_median)
        # print("manual average", manual_average)
        # print("audioop average", audioop_average)
        # print("\n")

        noisy.append(audioop_average)
 
    # current_noise = sum(noisy) / len(noisy)
    current_noise = np.mean(noisy) 
    # current_noise = np.median(noisy)

    # add device bias
    current_noise = max(0, current_noise + device_bias)

    print("current noise = " + str(current_noise))

    return current_noise


def return_noise_threshold(noisy, threshold_bias=0):

    THRESHOLD = 0

    multiplier = 1.5
    # ## range should be:  if noisy is 10 = 50; if noisy = 100 = 250;
    # if(noisy < 10): THRESHOLD = 50
    # if(noisy > 10 and noisy < 20): THRESHOLD = 100 + bias 
    # if(noisy > 20 and noisy < 30): THRESHOLD = 140 + bias
    # if(noisy > 30 and noisy < 40): THRESHOLD = 160 + bias
    # if(noisy > 40 and noisy < 50): THRESHOLD = 170 + bias
    # if(noisy > 50 and noisy < 60): THRESHOLD = 200 + bias
    # if(noisy > 60 and noisy < 70): THRESHOLD = 300 + bias
    # if(noisy > 70): THRESHOLD = 350 + bias

    noise_ranges = list(np.array([0, 10, 20, 30, 40, 50, 60, 70, float('inf')]) * multiplier)
    thresholds = list(np.array([50, 100, 140, 160, 170, 200, 300, 350] ))

    # Ensure that the length of noise_ranges is one more than the length of thresholds
    if len(noise_ranges) != len(thresholds) + 1:
        raise ValueError("noise_ranges should have one more element than thresholds")

    for i in range(len(noise_ranges) - 1):

        if noise_ranges[i] <= noisy < noise_ranges[i + 1]:

            return max(0, thresholds[i] + threshold_bias)
        
    return max(0,thresholds[-1] + threshold_bias)



def listen_for_speech(): # @@@ remember to add acknowledgements afterwards

    # config = load_config(path+'/configuration.toml')

    # cfg = config['audio']

    # TEMP
    record_mode = 'continuous'

    # define the audio file path
    # TODO: pass as param
    
    # audio_file_path = path + "/tmp/temp_reco.wav"
    audio_file_path = "/tmp/temp_reco.wav"

    # audio = pyaudio.PyAudio()

    recorded = False

    while recorded == False:

        try:

            with ignoreStderr():
                audio = pyaudio.PyAudio()

            stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        # input_device_index = device_index,
                        frames_per_buffer=CHUNK)
            
            #print('quiet! checking noise threshold...')
            # noise_value = adjust_sound_env(stream, device_bias=cfg['device_bias'])
            # THRESHOLD = return_noise_threshold(noise_value, threshold_bias=cfg['threshold_bias'])

            print("THRESHOLD:", THRESHOLD)

            samples = []

            if record_mode == 'fixed':

                # this is for a fixed amount of recording seconds
                for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    samples.append(data)

            if record_mode == 'continuous':

                print('listening for speech...')

                chunks_per_second = RATE / CHUNK

                # silence_buffer = deque(maxlen=int(SILENCE_LIMIT * chunks_per_second))
                samples_buffer = deque(maxlen=int(SILENCE_LIMIT * RATE))
                silence_buffer_size = SILENCE_LIMIT * chunks_per_second

                started = False

                ### this is for continuous recording, until silence is reached
                run = 1
                timing = None

                print('preparing to record...')

                
                while(run):
                    
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        
                        # Calculate and display level
                        audio_data = np.frombuffer(data, dtype=np.int32)
                        rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
                        db = 20 * np.log10(rms / 2147483647.0) if rms > 0 else -100
                        
                        # Visual level meter
                        level_bar = "#" * int((db + 100) / 2)
                        print(f"\r[{level_bar:<50}] {db:6.1f} dB ", end='', flush=True)
                        
                        samples_buffer.append(db)
                    
                        if(db > THRESHOLD_DB):
                            
                            if not started:
                                print("recording started")
                                timing = time.time()
                                started = True
                                samples_buffer.clear();
                            
                            samples.append(data)

                    

                    # data = stream.read(CHUNK, exception_on_overflow = False)
                    # silence_buffer.append(abs(audioop.avg(data, 2)))

                    # samples_buffer.extend(data)
                    
                    
                    # # if (True in [x > THRESHOLD for x in silence_buffer]):
                    # #     print("X: ", x)
                        
                    # if max(silence_buffer) > THRESHOLD:
                    #     print("Max value in buffer:", max(silence_buffer))    
                        
                    #     if not started:
                    #         print ("recording started")
                    #         started = True
                    #         samples_buffer.clear()
                    #         timing = time.time()

                    #     samples.append(data)

                            # check for timeout
                            if(time.time() - timing > TIMEOUT):
                                    print(">>> stopping recording because of timeout")
                                    stream.stop_stream()

                                    record_wav_file(samples, audio, audio_file_path)

                                    #reset all vars
                                    started = False
                                    samples_buffer.clear()
                                    samples = []

                                    run = 0


                        elif(started == True):   ### volume went below the threshold
                            
                            samples.append(data)
                            
                            # check if we have enough silence below threshold
                            if len(samples_buffer) >= silence_buffer_size:
                                avg_db = sum(samples_buffer) / len(samples_buffer)
                                
                                silence_count = sum(1 for db_val in samples_buffer if db_val < THRESHOLD_DB)
                                silence_percentage = silence_count / len(samples_buffer)
                                
                                if avg_db < THRESHOLD_DB or silence_percentage > 0.9:
                            
                                                            
                                    print ("recording stopped")
                                    stream.stop_stream()
                                    
                                    record_wav_file(samples, audio, audio_file_path)

                                    #reset all vars
                                    started = False
                                    #silence_buffer.clear()
                                    samples_buffer.clear()
                                    samples = []

                                    run = 0

            stream.close()
            audio.terminate()

            recorded = True
        
        except OSError as error:
       
            # error_sound_path = path+"/media/say_again.mp3"
            print('OS Error encountered:', error)
            #playsound(error_sound_path)
            # play_background_music_INTERNAL(error_sound_path, loops=0)

    return audio_file_path



def record_wav_file(data, audio, audio_file_path):

    with wave.open(audio_file_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(data))
        #wf.close()



def recognize_speech(filename, lang=None):
    
    import requests as req

    # 1. Try MacBook Whisper server
    try:
        with open(filename, 'rb') as f:
            resp = req.post(
                "http://100.67.155.96:8005/v1/audio/transcriptions",
                  files={"file": f},
                  timeout=20,
            )
            print("trying ASR MacBook with resp.status_code = ", resp.status_code) 

        if resp.status_code == 200:
            text = resp.json().get("text", "").strip()
            if text:
                print("ASR - using MacBook Whisper")
                return text
            else: return ""
    except Exception:
        pass


    # 2. Try GLITBOX Whisper server
    try:
        with open(filename, 'rb') as f:
            resp = req.post(
                "http://100.79.41.86:8005/v1/audio/transcriptions",
                  files={"file": f},
                  timeout=20,
            )
            print("trying ASR GLITCHBOX with resp.status_code = ", resp.status_code) 

        if resp.status_code == 200:
            text = resp.json().get("text", "").strip()
            if text:
                print("ASR - using Glitchbox Whisper")
                return text
            else: return ""
    except Exception:
        pass


    # 3. Fallback to Google Speech Recognition
    print("ASR - falling back to Google Speech Recognition")

    with sr.AudioFile(filename) as source:

        r = sr.Recognizer()
        r.energy_threshold = 50
        r.dynamic_energy_threshold = False

        audio = r.record(source)
      
        try:
            if lang:
                return r.recognize_google(audio, language=lang) or ""
            else: 
                return r.recognize_google(audio) or ""

        except sr.UnknownValueError as e:
            print("Google ASR error: ", e)

        except sr.RequestError as e:
            print("Google ASR error: Could not request results from Google Speech Recognition service; {0}".format(e))





def recognize_speech_old(filename, lang=None):
    

    with sr.AudioFile(filename) as source:

        r = sr.Recognizer()
        r.energy_threshold = 50
        r.dynamic_energy_threshold = False

        audio = r.record(source)
        usertext = "";
        
        try:
            print("trying to recognize from ... " + filename)
            if lang:
                usertext = r.recognize_google(audio, language=lang)
            else: 
                usertext = r.recognize_google(audio)

        except sr.UnknownValueError as e:
            print("Google Speech Recognition could not understand audio: ", e)

        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

        return usertext
    



def listen_smartASR():

    # Stream audio to 1. MacBookPro or 2. GLITCHBOX for VAD + Smart Turn + ASR
    # Fall back to local recording + standard ASR failsafe system if servers are unavaible

    import asyncio, json
    import websockets

    SERVERS = [
        ("MackBook",  "ws://100.67.155.96:8200/v1/listen"),
        ("Glitchbox", "ws://100.79.41.86:8200/v1/listen"),
    ]    

    async def _stream(name, uri):
        async with websockets.connect(uri, open_timeout=5) as ws:
            with ignoreStderr():
                audio = pyaudio.PyAudio()

            mic = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=512)

            print(f"Smart ASR - streaming to {name} ...")

            try:

                while True:
                    data = mic.read(512, exception_on_overflow=False)
                    await ws.send(data)

                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=0.001)
                        event = json.loads(msg)

                        if event["event"] == "speech_start":
                            print("Speech detected")

                        elif event["event"] == "incomplete":
                            print(f"Still talking (prob={event['probability']:.2f})...")
                        
                        elif event['event'] == "transcription":
                            text = event.get("text", "").strip()
                            print(f"Heard: {text}")
                            return text
                
                    except asyncio.TimeoutError:
                        pass

            finally:
                mic.stop_stream()
                mic.close()
                audio.terminate()           

    
    for name, uri in SERVERS:
        try:
            loop = asyncio.new_event_loop
            asyncio.set_event_loop(loop)
            result = asyncio.get_event_loop().run_until_complete(_stream(name, uri))
            if result: 
                return result
        except Exception as e:
            print(f"Smart ASR - {name} failed: {e}")
    
    ## Fallback to local recording and remote ASR transcription
    # print("Smart ASR - falling back to local")
    # return listen_and_transcribe()

    ## Fallback to Deepgram cloud
    print("Smart ASR - falling back to DeepGram")

    try:
        import websocket
        import json as json_lib


        DEEPGRAM_KEY = os.environ.get("DEEPGRAM_API_KEY")
        DG_URL =  f"wss://api.deepgram.com/v1/listen?model=nova-2&language=en&smart_format=true&endpointing=1200&encoding=linear16&sample_rate=44100&channels=1"

        result = [None]
        ws = websocket.create_connection(DG_URL, header=[f"Authorization: Token {DEEPGRAM_KEY}"])
        print(f"DG connected, key starts with: {DEEPGRAM_KEY[:8]}...")

        transcripts = []

        def recv_thread():
            while result[0] is None:
                try:
                    msg = ws.recv()
                    if not msg: continue
                    print(f"DG raw: {msg}")

                    data = json_lib.loads(msg)

                    if data.get("type") == "Metadata":
                        print(f"DG connected: {data.get('request_id')}")
                        continue
                    
                    if data.get("is_final"):
                        t = data["channel"]["alternatives"][0]["transcript"] 
                        if t:
                            transcripts.append(t)
                            print(f"DG: {t}")
                        if data.get("speech_final"):
                            result[0] = " ".join(transcripts)
                except websocket.WebSocketConnectionClosedException:
                    break
                except Exception as e:
                    print(f"DG recv error: {e}")
                    break

        t = threading.Thread(target=recv_thread, daemon=True)
        t.start()

        with ignoreStderr():
            audio = pyaudio.PyAudio()
        mic = audio.open(format=pyaudio.paInt32, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        print("Mic opened -- streaming to Deepgram")

        while result[0] is None:
            data = mic.read(1024, exception_on_overflow=False)
            samples32 = np.frombuffer(data, dtype=np.int32)
            samples16 = (samples32 >> 14).clip(-32768, 32767).astype(np.int16)
            rms = np.sqrt(np.mean(samples16.astype(np.float64)**2))
            print(f"\r Audio level: {rms: 0f}\n", end='', flush=True)
            ws.send_binary(samples16.tobytes()) 

        mic.stop_stream(); mic.close(); 
        audio.terminate()
        ws.close()

        if result[0]: return result[0]

    except Exception as e:
        print(f"Deepgram failed: {e}")
        



def listen_and_transcribe():

    # Local recording into local file + separate ASR

    audiofile = listen_for_speech()
    return recognize_speech(audiofile) or ""

