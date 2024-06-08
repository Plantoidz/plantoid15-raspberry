import os
import time
from pathlib import Path
import json
from dotenv import load_dotenv
from pinata import Pinata
import subprocess

from plantoids.plantoid import Plantony
from lib.plantoid.text_content import *
import lib.plantoid.speech as PlantoidSpeech
import lib.plantoid.eden as eden

from mutagen.mp3 import MP3
import re
import hashlib
import random

from unidecode import unidecode

load_dotenv()

PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_API_SECRET = os.environ.get("PINATA_API_SECRET")
PINATA_JWT = os.environ.get('PINATA_JWT')



def generate_oracle(plantoid: Plantony, network, audio, tID, amount):

    plantoid.send_serial_message("thinking")
    plantoid.send_serial_message("asleep") ## REMOVE


    # get the path of the network
    path = network.plantoid_path
    print("TRANSCRIBING... in PATH ==== ", path)

    # get the path to the background music
    background_music_path = plantoid.path+"/media/ambient3.mp3"

    # play the background music
    plantoid.play_background_music(background_music_path)

    # get generated transcript
    generated_transcript = PlantoidSpeech.recognize_speech(audio, plantoid.lang)

    # print the generated transcript
    print("I heard... (oracle): " + generated_transcript)

    # if no generated transcript, use a default
    if not generated_transcript: 
        generated_transcript = get_default_sermon_transcript(plantoid.lang)

    # save the generated transcript to a file with the seed name
    path_transcripts = path + "/transcripts/"
    path_transcripts_network = path_transcripts + str(network.name)

    if not os.path.exists(path_transcripts):
        os.makedirs(path_transcripts)

    if not os.path.exists(path_transcripts_network):
        os.makedirs(path_transcripts_network)

    # save the generated response to a file with the seed name
    filename = f"{path_transcripts_network}/{tID}_transcript.txt"

    print("saving transcript as ...................................", filename)

    with open(filename, "w") as f:
        f.write(generated_transcript)

    print("transcript saved as ..... " + filename)

    # TODO: re-enable
    # calculate the length of the poem
    # one line every 0.01 ETH for mainnet, one line every 0.001 ETH for goerli
    n_lines = int(amount / network.min_amount)  

    n_lines = n_lines + 2
    
    if n_lines > 6: 
        n_lines = 6

    # n_lines = 4

    print("generating transcript with number of lines = " + str(n_lines))

    # generate the sermon prompt
    prompt = get_sermon_prompt(
        generated_transcript,
        plantoid.selected_words_string,
        n_lines,
        plantoid.lang
    )
    print("PROMPTING with ..............................................", prompt)

    # get GPT response
    # response = PlantoidSpeech.GPTmagic(prompt, call_type='completion')
    # sermon_text = response.choices[0].text

    # print('sermon text 1:')
    # print(sermon_text)

    # get GPT response
    sermon_text = PlantoidSpeech.GPTmagic(prompt)

    print('sermon text: ', sermon_text)
  
    #--------

    responses_path = path + "/responses/"
    responses_path_network = responses_path + str(network.name)

    # save the generated response to a file with the seed name
    if not os.path.exists(responses_path):
        os.makedirs(responses_path);

    # save the generated response to a file with the seed name
    if not os.path.exists(responses_path_network):
        os.makedirs(responses_path_network);
    
    # save the generated response to a file with the seed name
    filename =  f"{responses_path_network}/{tID}_response.txt"
    with open(filename, "w") as f:
        f.write(sermon_text)

    plantoid.send_serial_message("awake")

    return sermon_text


def print_oracle(plantoid: Plantony, network, tID, sermon_text):

    # now let's print to the LP0, with Plantoid signature
    plantoid_sig = get_plantoid_sig(network, tID, plantoid.lang)

    print("LP0 printing sermon text = ", sermon_text)


    sermon_text = unidecode(sermon_text)

   # os.system("cat " + filename + " > /dev/usb/lp0") #stdout on PC, only makes sense in the gallery
    os.system('echo "' + sermon_text + '" > /dev/usb/lp0')
    os.system('echo "' + plantoid_sig + '" > /dev/usb/lp0')



def read_oracle(plantoid: Plantony, network, tID, sermon_text):

    path = network.plantoid_path

    # now let's read it aloud
    audiofile = PlantoidSpeech.get_text_to_speech_response(sermon_text, plantoid.eleven_voice_id)
    # stop_event.set() # stop the background noise

    sermons_path = path + "/sermons/"
    sermons_path_network = sermons_path +str(network.name)

    # save the generated sermons to a file with the seed name
    if not os.path.exists(sermons_path):
        os.makedirs(sermons_path)

    if not os.path.exists(sermons_path_network):
        os.makedirs(sermons_path_network)
    
    # save mp3 file
    # subprocess.run(["cp", audiofile, f"{path}/sermons/{tID}_sermon.mp3"])
    subprocess.run(["cp", audiofile, f"{sermons_path_network}/{tID}_sermon.mp3"])

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

        response = pinata.pin_file(movie_path)
        print('pinata response:', response)

        # TODO: this should probably check for a response code
        if(response and response.get('data')):
            ipfsQmp3 = response['data']['IpfsHash']
            print("recording the animation_url = " + ipfsQmp3)
            return ipfsQmp3
        

    

def record_metadata(plantoid: Plantony, network, token_Id, db, ipfsQmp3):


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








def create_video_from_audio(path, tID, network_name, init_img, init_strength):

    # create empty output file
    remote_output_file = None
    video_file = None

    # prompts = PlantoidEden.create_prompts(tID)

    # construct the API call to Eden (this includes the making of the prompts)
    #eden_config = eden.build_API_request(path, tID, network_name)  
    eden_config = eden.build_API_request(path, tID, network_name, path + "/sermons/" + network_name + "/" + tID + "_sermon.mp3", init_img, init_strength)

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

    audio_file_path = path +"/sermons/" + network_name + "/" + seed + "_sermon.mp3"
    output_file_path = path +"/videos/" + network_name + "/" + seed + "_movie.mp4"

    print(audio_file_path, video_file_path)

    if not os.path.isfile(audio_file_path): raise Exception('Audio file not found!')
    if not os.path.isfile(video_file_path): raise Exception('Video file not found!')

    fmpeg_interleave_av(video_file_path, audio_file_path, output_file_path)

    return output_file_path



def fallback_video(path, tID, network_name):

    audiof = MP3(path + "/sermons/" + network_name + "/" + tID + "_sermon.mp3")
    
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
