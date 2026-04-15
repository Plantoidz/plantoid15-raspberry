import os
import sys
import time
from pathlib import Path
import json
from dotenv import load_dotenv
import subprocess

#from plantoids.plantoid import Plantony
from lib.plantoid.text_content import *
import lib.plantoid.speech as PlantoidSpeech

import lib.plantoid.eden as eden
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "glitchbox"))
from grpc_prompt_journey_http import run_journey

from elevenlabs.client import ElevenLabs
from elevenlabs import play


from pinata import Pinata

from lib.plantoid.pin_utils import * 

from mutagen.mp3 import MP3
import re
import hashlib
import random

from unidecode import unidecode

load_dotenv()

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_SECRET_KEY")
PINATA_JWT = os.environ.get('PINATA_JWT')


def archive(type, folder, user_speech, tID, network):
   
    path = network.plantoid_path
    path_transcripts = path + "/" + folder + "s/"
    path_transcripts_network = path_transcripts + str(network.name)

    if not os.path.exists(path_transcripts):
        os.makedirs(path_transcripts)

    if not os.path.exists(path_transcripts_network):
        os.makedirs(path_transcripts_network)

    # save the generated response to a file with the seed name
    filename = f"{path_transcripts_network}/{tID}_{folder}.txt"


    match type:
        case "text":
    
            with open(filename, "w") as f:
                f.write(user_speech)


    print(f"{folder} saved as ..... " + filename)



# def save_response(response, tID, network):

#     path = network.plantoid_path
#     responses_path = path + "/responses/"
#     responses_path_network = responses_path + str(network.name)

#     if not os.path.exists(responses_path):
#         os.makedirs(responses_path);

#     if not os.path.exists(responses_path_network):
#         os.makedirs(responses_path_network);
    
#     # save the generated response to a file with the seed name
#     filename =  f"{responses_path_network}/{tID}_response.txt"

#     with open(filename, "w") as f:
#         f.write(response_text) 


# def generate_GPT_response(craft, plantoid, network, audio, tID, credits):
#     plantoid.send_serial_message("thinking")
    
#     # get the path of the network
#     path = network.plantoid_path
#     print("TRANSCRIBING... in PATH ==== ", path)
    
#     # get the path to the background music
#     background_music_path = plantoid.path+"/media/ambient3.mp3"
    
#     # play the background music
#     plantoid.play_background_music(background_music_path)
    
#     # get generated transcript
#     generated_transcript = PlantoidSpeech.recognize_speech(audio, plantoid.lang)
    
#     # print the generated transcript
#     print("I heard...: " + generated_transcript)
    
#     # if no generated transcript, use a default
#     if not generated_transcript:  
#             match craft:
#                 case "opera":
#                     generated_transcript = get_default_song_transcript(plantoid.lang)
#                 case "oracle":
#                     generated_transcript = get_default_sermon_transcript(plantoid.lang)
        
#     # save the generated transcript to a file with the seed name
#     path_transcripts = path + "/transcripts/"
#     path_transcripts_network = path_transcripts + str(network.name)
    
#     if not os.path.exists(path_transcripts):
#         os.makedirs(path_transcripts)

#     if not os.path.exists(path_transcripts_network):
#         os.makedirs(path_transcripts_network)

#     # save the generated response to a file with the seed name
#     filename = f"{path_transcripts_network}/{tID}_transcript.txt"

#     print("saving transcript as ...................................", filename)
    
#     with open(filename, "w") as f:
#         f.write(generated_transcript)

#     print("transcript saved as ..... " + filename)
    
#     ######## now generate the response ########
    
#     print("generating transcript with number of credits = " + str(credits))

#     # retieve the response prompt
#     prompt = None
#     match craft:
#                 case "opera":
#                     prompt = get_song_prompt(
#                         generated_transcript,
#                         plantoid.selected_words_string,
#                         credits,
#                         plantoid.lang
#                     )
#                 case "oracle":
#                     prompt = get_sermon_prompt(
#                         generated_transcript,
#                         plantoid.selected_words_string,
#                         credits,
#                         plantoid.lang
#                     )
    
#     print("PROMPTING with ..............................................", prompt)

#     # get GPT response
#     response_text = PlantoidSpeech.GPTmagic(prompt, model=self.llm_model)

#     print('response text: ', response_text)


#     # Validate and fix line lengths for opera
#     if craft == "opera":
        
#         # Split into individual lines and clean them
#         lines = []
        
#         for line in response_text.split('\n'):
#             line = line.strip()
#             # Remove numbering like "(1)" or "1." from the start
#             line = re.sub(r'^\(\d+\)\s*', '', line)
#             line = re.sub(r'^\d+\.\s*', '', line)
#             # Remove quotes
#             line = line.strip('"\'')

#             if line and len(line) > 0:
#                 # truncate is too long
#                 if len(line) > 200:
#                     last_space = line[:200].rfind(' ')
#                     if last_space > 0:
#                         line = line[:last_space]
#                     else:
#                         line = line[:200]
#                     print(f"Warning: Truncated long line to {len(line)} chars")
        
#                 lines.append(line)
    
#         response_lines = lines
#         response_text = '\n'.join(lines)
#         print('fixed response text: ', response_text)

  
#     #--------

#     responses_path = path + "/responses/"
#     responses_path_network = responses_path + str(network.name)

#     # save the generated response to a file with the seed name
#     if not os.path.exists(responses_path):
#         os.makedirs(responses_path);

#     # save the generated response to a file with the seed name
#     if not os.path.exists(responses_path_network):
#         os.makedirs(responses_path_network);
    
#     # save the generated response to a file with the seed name
#     filename =  f"{responses_path_network}/{tID}_response.txt"
#     with open(filename, "w") as f:
#         f.write(response_text)

#     plantoid.send_serial_message("awake")

#     if craft == "opera":
#         return response_lines
#     else:
#         return response_text
    

# this could theoretically be commented out -- use generate_response() instead !  :)
# def generate_oracle(plantoid, network, audio, tID, amount):

#     plantoid.send_serial_message("thinking")
#     plantoid.send_serial_message("asleep") ## REMOVE


#     # get the path of the network
#     path = network.plantoid_path
#     print("TRANSCRIBING... in PATH ==== ", path)

#     # get the path to the background music
#     background_music_path = plantoid.path+"/media/ambient3.mp3"

#     # play the background music
#     plantoid.play_background_music(background_music_path)

#     # get generated transcript
#     generated_transcript = PlantoidSpeech.recognize_speech(audio, plantoid.lang)

#     # print the generated transcript
#     print("I heard... (oracle): " + generated_transcript)

#     # if no generated transcript, use a default
#     if not generated_transcript: 
#         generated_transcript = get_default_sermon_transcript(plantoid.lang)

#     # save the generated transcript to a file with the seed name
#     path_transcripts = path + "/transcripts/"
#     path_transcripts_network = path_transcripts + str(network.name)

#     if not os.path.exists(path_transcripts):
#         os.makedirs(path_transcripts)

#     if not os.path.exists(path_transcripts_network):
#         os.makedirs(path_transcripts_network)

#     # save the generated response to a file with the seed name
#     filename = f"{path_transcripts_network}/{tID}_transcript.txt"

#     print("saving transcript as ...................................", filename)

#     with open(filename, "w") as f:
#         f.write(generated_transcript)

#     print("transcript saved as ..... " + filename)

#     # TODO: re-enable
#     # calculate the length of the poem
#     # one line every 0.01 ETH for mainnet, one line every 0.001 ETH for goerli
#     n_lines = int(amount / network.min_amount)  

#     n_lines = n_lines + 2
    
#     if n_lines > 6: 
#         n_lines = 6

#     # n_lines = 4

#     print("generating transcript with number of lines = " + str(n_lines))

#     # generate the sermon prompt
#     prompt = get_sermon_prompt(
#         generated_transcript,
#         plantoid.selected_words_string,
#         n_lines,
#         plantoid.lang
#     )
#     print("PROMPTING with ..............................................", prompt)

#     # get GPT response
#     # response = PlantoidSpeech.GPTmagic(prompt, call_type='completion')
#     # sermon_text = response.choices[0].text

#     # print('sermon text 1:')
#     # print(sermon_text)

#     # get GPT response
#     sermon_text = PlantoidSpeech.GPTmagic(prompt, model=self.llm_model)

#     print('sermon text: ', sermon_text)
  
#     #--------

#     responses_path = path + "/responses/"
#     responses_path_network = responses_path + str(network.name)

#     # save the generated response to a file with the seed name
#     if not os.path.exists(responses_path):
#         os.makedirs(responses_path);

#     # save the generated response to a file with the seed name
#     if not os.path.exists(responses_path_network):
#         os.makedirs(responses_path_network);
    
#     # save the generated response to a file with the seed name
#     filename =  f"{responses_path_network}/{tID}_response.txt"
#     with open(filename, "w") as f:
#         f.write(sermon_text)

#     plantoid.send_serial_message("awake")

#     return sermon_text


def print_response(plantoid, network, tID, text):

    # now let's print to the LP0, with Plantoid signature
    plantoid_sig = get_plantoid_sig(network, tID, plantoid.lang)

    # print("LP0 printing sermon text = ", sermon_text)
    
    text = unidecode(text)

    print("printing the response....")
    print_thermal_txt(text)
    print("printing the signature...")
    print_thermal_txt(plantoid_sig)

   # os.system("cat " + filename + " > /dev/usb/lp0") #stdout on PC, only makes sense in the gallery
   #  os.system('echo "' + sermon_text + '" > /dev/usb/lp0')
   #  os.system('echo "' + plantoid_sig + '" > /dev/usb/lp0')



def generate_song(text, credits): ### NB: text is an array of lyrics
    
    credits = credits + 2
    if(credits > 6): credits = 6
    
    print("generating a song with $$$$$$ CREDITS $$$$$$ =======>>>> ", credits)
    
    elevenlabs = ElevenLabs(
        api_key=os.getenv("ELEVENLABS_MUSIC_KEY")
    )

    composition_plan = {
    'positive_global_styles': ['bel canto', 'early 19th-century Italian opera', 'classical aria', 'lyrical', 'woodwinds', 'strings', 'delicate orchestration'],
    'negative_global_styles': ['electronic', 'heavy percussion', 'modern synth', 'rock'],
    'sections': [
        {
            "section_name": 'Aria', 
            'positive_local_styles': ['long lyrical vocal lines', 'soprano', 'delicate woodwinds', 'string accompaniment'], 
            'negative_local_styles': ['heavy brass', 'percussion', 'electronic sounds'], 
            'duration_ms': 10000 * credits, 
            'lines':  text 
        }
    ]
    }
    
    composition = elevenlabs.music.compose(composition_plan=composition_plan)
    
    # composition is a generator, so we are first combining it into a byte-like object
    audio_data = b"".join(composition)

    # Save to file instead of playing
    with open("/tmp/output_music.mp3", "wb") as f:
        f.write(audio_data)

    # Return the file path
    audio_file_path = "/tmp/output_music.mp3"
    return audio_file_path
    



def save_and_play_audio(plantoid, network, tID, audiofile):
    
    path = network.plantoid_path
    
    songs_path = path + "/audios/"
    songs_path_network = songs_path + str(network.name)
    
    # save the generated sermons to a file with the seed name
    if not os.path.exists(songs_path):
        os.makedirs(songs_path)

    if not os.path.exists(songs_path_network):
        os.makedirs(songs_path_network)
    
    subprocess.run(["cp", audiofile, f"{songs_path_network}/{tID}_audio.mp3"])

    # stop the background music
    plantoid.stop_background_music()

    # play the oracle
    plantoid.send_serial_message("speaking")
    plantoid.play_background_music(audiofile, loops=0)
    time.sleep(1)

    print('audio play completed!')
    plantoid.send_serial_message("awake")
    
    
    



def read_oracle(plantoid, network, tID, sermon_text): # I think it is no longer used

    path = network.plantoid_path

    # now let's read it aloud
    # audiofile = PlantoidSpeech.get_text_to_speech_response(sermon_text, plantoid.voice_id)
    audiofile = PlantoidSpeech.stream_response(sermon_text, plantoid.voice_id, save_to_file = "/tmp/tonyspeak.mp3")
    # stop_event.set() # stop the background noise

    sermons_path = path + "/audios/"
    sermons_path_network = sermons_path +str(network.name)

    # save the generated sermons to a file with the seed name
    if not os.path.exists(sermons_path):
        os.makedirs(sermons_path)

    if not os.path.exists(sermons_path_network):
        os.makedirs(sermons_path_network)
    
    # save mp3 file
    # subprocess.run(["cp", audiofile, f"{path}/sermons/{tID}_sermon.mp3"])
    subprocess.run(["cp", audiofile, f"{sermons_path_network}/{tID}_audio.mp3"])

    # stop the background music
    plantoid.stop_background_music()

    # play the oracle
    plantoid.send_serial_message("speaking")

    
    # playsound(filename)
    plantoid.play_background_music(audiofile, loops=0)
    time.sleep(1)

    print('oracle read completed!')
    plantoid.send_serial_message("awake")
    





def pin_movie(movie_path):

    # create a pinata object
    pinata = Pinata(PINATA_API_KEY, PINATA_API_SECRET, PINATA_JWT)

    # set variables to None
    ipfsQmp3 = None
  

    # # check if the movie already exists
    # if os.path.exists(path + "/videos/" + network.name + "/" + token_Id +"_movie.mp4"):

    #     # the movie already exists, move directly to the metadata creation
    #     print("skipping the production of the movie, as it already exists...");
    #     movie_path = path + "/videos/" + network.name + "/" + token_Id +"_movie.mp4"

    # else:

    #     # the movie doesn't exist, create it
    #     audio = path + "/sermons/" + network.name + "/" + token_Id + "_sermon.mp3"
    #     print("creating movie for sermon file.. " + audio) 
        
    #     if not os.path.isfile(audio):
    #         print("no Sermon audio file associated with seed: " + token_Id, 'skipping...')
    #         return 

    #     plantoid.send_serial_message("thinking")
    #     plantoid.send_serial_message("asleep") ## REMOVE
    #     plantoid.send_serial_message("fire") ## REMOVE
            
    #     movie_path = eden.create_video_from_audio(path, token_Id, network.failsafe, network.name)


    ### Pin the Video-Sermon on IPFS
    if movie_path is None:
        print("movie is null, skipping pinning to IPFS")
        return

    else:

        print("movie found, pinning to IPFS")

        try:
            response = pinata.pin_file(movie_path)
            print('pinata response:', response)

            # TODO: this should probably check for a response code
            if(response and response.get('data')):
                ipfsQmp3 = response['data']['IpfsHash']
                print("recording the animation_url = " + ipfsQmp3)

                url = "https://ipfs.io/ipfs/" + ipfsQmp3
                qrcode = create_ipfs_qr(url, output_file="/tmp/ipfs_qrcode.png", size=10)
                print_thermal_img(qrcode)

                return ipfsQmp3
            
        except Exception as e:
            print(f"Something went wrong with Pinata: {e}")

    

def record_metadata(plantoid, network, token_Id, db, ipfsQmp3):


    # get the path
    path = network.plantoid_path

    ### Create Metadata
 
    if ipfsQmp3 is not None:
        db['animation_url'] = "ipfs://" + ipfsQmp3 # ipfsQwav

    path_meta = path + "/metadata/"
    path_meta_network = path + "/metadata/"+str(network.name)+"/"

    if not os.path.exists(path_meta):
        os.makedirs(path_meta)

    if not os.path.exists(path_meta_network):
        os.makedirs(path_meta_network)

    with open(path_meta_network + token_Id + '.json', 'w') as outfile:
        json.dump(db, outfile)

    ### record in the database that this seed has been processed
    with open(path + '/minted_'+str(network.name)+'.db', 'a') as outfile:
        outfile.write(token_Id + "\n")

    
    plantoid.send_serial_message("fire") ## REMOVE
    plantoid.send_serial_message("awake") ## REMOVE




def glitchbox_video_journey(path, tID, network_name, init_img, init_strength):

    from mutagen.mp3 import MP3

    audio_file = path + "/audios/" + network_name + "/" + tID + "_audio.mp3"
    output_file = path + "/videos/" + network_name + "/" + tID + "_movie.mp4"

    # ensure video dir exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # generate prompt fromm the response text (reuse eden.create_prompts
    duration = MP3(audio_file).info.length
    n_prompt = max(2, int(duration / 3)) # 3 seconds per prompt
    prompts = eden.create_prompts(path, tID, n_prompt, network_name)

    if len(prompts) < 2:
        print("not enough prompts for Glitchbox Journey")
        return None
    
    run_journey(
        prompts = prompts,
        server_ip = "100.79.41.86", # GLITCHBOX ON TAILSCALE
        port = 7860, ## HTTP PORT
        transition_frames = 30,
        hold_frames = 15,
        fps = 20,
        output = output_file,
        loop = False,
        init_image = init_img,
        curation_index = 28, # NO LORA
        strength = init_strength
    )

    if os.path.exists(output_file):
        return output_file
    return None


def create_video_from_audio(path, tID, network_name, init_img, init_strength):

    # create empty output file
    remote_output_file = None
    video_file = None

    # prompts = PlantoidEden.create_prompts(tID)

    # construct the API call to Eden (this includes the making of the prompts)
    #eden_config = eden.build_API_request(path, tID, network_name)  
    eden_config = eden.build_API_request(path, tID, network_name, path + "/audios/" + network_name + "/" + tID + "_audio.mp3", init_img, init_strength)

    # get the output file from the eden call
    remote_output_file = eden.make_eden_API_call(eden_config)           

    if remote_output_file is not None:

        print('Remote output file location:', remote_output_file)
        video_file = get_remote_video(remote_output_file, path)

        return video_file

        # video_path = make_video(path, video_file, tID, network_name)
        # return video_path

        # else:
        #     raise Exception('Provided eden output file does not exist:', remote_output_file)


    # FAILSAFE
    # run this if failsafe == 1, or if the remote_output_file is None (see above)
    # if failsafe == 1:

    # print('using failsafe, using fallback')
    #  #print("PlantoidEden.make_eden_API_call return Null -- going to use a fallback video !")
    # video_file = fallback_video(path, tID, network_name)

    # video_path = make_video(path, video_file, tID, network_name)
    # return video_path








def fmpeg_interleave_av(video_file, audio_file, output_file):

    audio_duration = get_media_duration(audio_file)
    video_duration = get_media_duration(video_file)

    # Calculate how many times the video needs to be looped
    loop_count = int(audio_duration / video_duration) + 1

    # Combine the looped video with audio
   # cmd_combine = ["ffmpeg", "-stream_loop", str(loop_count), "-i", video_file, "-i", audio_file, "-shortest",
   #                "-c:v", "copy", "-c:a", "aac", "-strict", "experimental", output_file]
    
    cmd_combine = ["ffmpeg", "-i", video_file, "-i", audio_file, output_file]
    subprocess.run(cmd_combine)


def make_video(path, video_file_path, seed, network_name): 

    if not video_file_path: return None

    video_path = path + "/videos"
    video_network_path = path + "/videos/" + network_name

    if not os.path.exists(video_path):
        # If it doesn't exist, create it
        os.makedirs(video_path)

    if not os.path.exists(video_network_path):
        # If it doesn't exist, create it
        os.makedirs(video_network_path)

    audio_file_path = path +"/audios/" + network_name + "/" + seed + "_audio.mp3"
    output_file_path = path +"/videos/" + network_name + "/" + seed + "_movie.mp4"

    print(audio_file_path, video_file_path)

    if not os.path.isfile(audio_file_path): raise Exception('Audio file not found!')
    if not os.path.isfile(video_file_path): raise Exception('Video file not found!')

    fmpeg_interleave_av(video_file_path, audio_file_path, output_file_path)

    return output_file_path



def fallback_video(path, tID, network_name):

    audiof = MP3(path + "/audios/" + network_name + "/" + tID + "_audio.mp3")
    
    audiolen = int(audiof.info.length) + 1  # seconds of the poem length

    print("audiolen === " + str(audiolen))

    fallback_video_dir = path + "/fallback_videos/"

    if not os.path.exists(fallback_video_dir):
        # If it doesn't exist, create it and return null
        os.makedirs(fallback_video_dir)
        return None
    
    fallback_videos = sorted(os.listdir(fallback_video_dir))
    print(fallback_videos)
    if len(fallback_videos) == 0: return None
    
    Zmin = int(re.search('(\d+)', fallback_videos[0]).group(0))
    Zmax = int(re.search('(\d+)', fallback_videos[-1]).group(0))

    print("Zmin = " + str(Zmin))
    print("Zmax = " + str(Zmax))

    if audiolen < Zmin: audiolen = Zmin
    if audiolen > Zmax: audiolen = Zmax

    output_file = None

    for n in range(audiolen, Zmax+1):
    
        print("iterating through..." + str(n))
        fallback_videos_ = [v for v in fallback_videos if v.startswith(str(n))]

        if len(fallback_videos_) > 0: 

            # print(fallback_videos_)
            output_file = random.choice(fallback_videos_)
            break

    print("Given audiolen = " + str(audiolen))
    print("We found the Zvideo = " + output_file)

    # if no output file is found
    if output_file is None:
        output_file = fallback_videos[-1]

    video_path = fallback_video_dir + output_file
    return video_path




def get_remote_video(remote_output_file, path):

    print('get video(), remote_output_file is', remote_output_file)

    movie_file = path + "/out.mp4"

    # command = "wget " + outputf + " -O " + movie_file

    subprocess.run(["wget", remote_output_file, "-O", movie_file])

    # m = re.search("\w+\.mp4", outputf)
    # moviefile = m.group()

    # os.system("mv " + moviefile + " "+taskId+".mp4")

    md5sum = hashlib.md5(remote_output_file.encode('utf-8')).hexdigest()
    finalpath = path + "/fallback_videos/"

    if not os.path.exists(finalpath):
        # If it doesn't exist, create it
        os.makedirs(finalpath)


    seconds = int(get_media_duration(movie_file))
    newfilename = finalpath + str(seconds) + "_" + md5sum + ".mp4"

    os.system("mv " + movie_file + " " + newfilename)

    print('movie file is', newfilename)

    return newfilename





def get_media_duration(file_path):

    cmd = ["ffmpeg", "-i", file_path, "-hide_banner"]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    lines = result.stderr.split('\n')

    for line in lines:

        if "Duration" in line:

            duration_str = line.split(",")[0].split("Duration:")[1].strip()
            hours, minutes, seconds = duration_str.split(":")
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            return total_seconds
        
    raise ValueError(f"Could not determine duration of {file_path}.")
