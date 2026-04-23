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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "glitchbox"))
from grpc_prompt_journey_http import run_journey, run_scheduler

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




def glitchbox_video_journey(prompts, duration, fps, init_img, init_strength, loras):

    # video output 
    output_file = "/tmp/generated_journey_video.mp4"

    # calculate transition / hold frames to match audio duration
    total_frames = int(duration * fps)
    n = len(prompts)
    # total_frames = (n-1)*transition * n*hold
    # pick hold_frames = 15, solve for transition_frames
    hold_frames = 15
    if n > 1:
        transition_frames = max(1, (total_frames - n * hold_frames) // (n -1))
    else:
        transition_frames = max(1, total_frames - hold_frames)

    run_journey(
        prompts = prompts,
        server_ip = "100.79.41.86", # GLITCHBOX ON TAILSCALE
        port = 7860, ## HTTP PORT
        transition_frames = transition_frames,
        hold_frames = hold_frames,
        fps = fps,
        output = output_file,
        loop = False,
        init_image = init_img,
        curation_index = loras,
        strength = init_strength
    )

    if os.path.exists(output_file):
        return output_file
    return None


def glitchbox_video_scheduler(audio_file, duration, fps, init_img, init_strength, loras):
   # video output 
    output_file = "/tmp/generated_journey_video.mp4"

    run_scheduler(
        server_ip = "100.79.41.86", # GLITCHBOX ON TAILSCALE
        port = 7860, ## HTTP PORT
        fps = fps,
        output = output_file,
        init_image = init_img,
        audio_file = audio_file,
        duration_seconds = duration,
        curation_index = loras,
        strength = init_strength
    )

    if os.path.exists(output_file):
        return output_file
    return None
  

# def create_video_from_audio(path, tID, network_name, init_img, init_strength):

#     # create empty output file
#     remote_output_file = None
#     video_file = None

#     # prompts = PlantoidEden.create_prompts(tID)

#     # construct the API call to Eden (this includes the making of the prompts)
#     #eden_config = eden.build_API_request(path, tID, network_name)  
#     eden_config = eden.build_API_request(path, tID, network_name, path + "/audios/" + network_name + "/" + tID + "_audio.mp3", init_img, init_strength)

#     # get the output file from the eden call
#     remote_output_file = eden.make_eden_API_call(eden_config)           

#     if remote_output_file is not None:

#         print('Remote output file location:', remote_output_file)
#         video_file = get_remote_video(remote_output_file, path)

#         return video_file

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


def save_video_with_audio(path, video_file_path, seed, network_name): 

    if not video_file_path: return None

    video_path = path + "/videos"
    video_network_path = path + "/videos/" + network_name

    if not os.path.exists(video_path):
        # If it doesn't exist, create it
        os.makedirs(video_path)

    if not os.path.exists(video_network_path):
        # If it doesn't exist, create it
        os.makedirs(video_network_path)

    plantoid_num = os.path.basename(os.path.normpath(path))
    movie_name = f"{plantoid_num}_{network_name}_{seed}_movie.mp4"

    audio_file_path = path +"/audios/" + network_name + "/" + seed + "_audio.mp3"
    output_file_path = path +"/videos/" + network_name + "/" + movie_name

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


def save_video_fallback(path, movie_file):

    md5sum = hashlib.md5(movie_file.encode('utf-8')).hexdigest() 
    finalpath = path + "/fallback_videos/" 

    if not os.path.exists(finalpath):
        os.makedirs(finalpath)

    seconds = int(get_media_duration(movie_file))
    newfilename = finalpath + str(seconds) + "_" + md5sum + ".mp4"
    
    os.system("cp " + movie_file + " " + newfilename) 
    print('fallback movie file is', newfilename)
    
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



def ask_transcript(plantoid, network, tID, question):

    # ask an initial question
    plantoid.weaving(question)

    # listen for audio and obtain the transcript
    user_speech = plantoid.listen() or get_default_transcript(plantoid)

    print("I heard.. ", user_speech)
    archive("text", "transcript", user_speech, tID, network)

    return user_speech



def poem_generation(plantoid, network, tID, amount, question):


    # ask an initial question
    # plantoid.weaving(question)

    # listen for audio and obtain the transcript
    #user_speech = plantoid.listen() or get_default_transcript(plantoid)

    #print("I heard ..", user_speech)
    #archive("text", "transcript", user_speech, tID, network)

    user_speech = ask_transcript(plantoid, network, tID, question)
    


    # Generate response
    plantoid.send_serial_message("thinking")

    credits = int(amount / network.min_amount)
    
    prompt = make_prompt(plantoid, user_speech, credits)
    response_text = PlantoidSpeech.GPTmagic(prompt, model=plantoid.llm_model)
    print("Response text: ", response_text)

    archive("text", "response", response_text, tID, network)

    # print oracle on the LP printer
    print_response(plantoid, network, tID, response_text)

    # generate audio file
    audiofile = PlantoidSpeech.stream_response(plantoid, response_text, plantoid.voice_id, save_to_file=f"/tmp/output_oracle{plantoid.plantoid_number}.wav")
    # convert to MP#
    mp3_file = f"/tmp/output_oracle{plantoid.plantoid_number}.mp3"
    subprocess.run(["ffmpeg", "-y", "-i", audiofile, mp3_file])
    audiofile = mp3_file
    # save and play the oracle
    save_and_play_audio(plantoid, network, tID, audiofile)

    plantoid.send_serial_message("awake")




def generic_metadata(plantoid, network, tID, db, callback_prompt, callback_video):
    movie_path = None
    animurl = None

    # check if movie exist for that particular token ID
    path = network.plantoid_path
    plantoid_num = os.path.basename(os.path.normpath(path))
    video_file = path + "/videos/" + network.name + "/" + f"{plantoid_num}_{network.name}_{tID}_movie.mp4"
    audio_file = path + "/audios/" + network.name + "/" + tID + "_audio.mp3" 
 
    if os.path.exists(video_file):
        movie_path = video_file

    elif os.path.isfile(audio_file):
        plantoid.send_serial_message("thinking")

        # retrieve the generated text to include in the movie
        with open(path + "/responses/" + network.name + "/" + tID + "_response.txt", "r") as f:
            sermon = f.read() 


        if(network.failsafe == 0): # IF NO FAILSAFE, CALL THE CALLBACK
            
            prompts = None

            if(callback_prompt):
                prompts = callback_prompt(plantoid, sermon, audio_file)
                archive("text", "description", "\n".join(prompts), tID, network)

            movie_path = callback_video(path, sermon, audio_file, prompts)
            save_video_fallback(path, movie_path)


        elif(network.failsafe == 1 or movie_path == None):  # FAILSAFE
            print("Failsafe: using fallback video")
            movie_path = fallback_video(path, tID, network.name)
        
        # Add audio to the video
        movie_path = save_video_with_audio(path, movie_path, tID, network.name)

    # PIN movie to IPFS
    animurl = pin_movie(movie_path)
    if(animurl):
        record_metadata(plantoid, network, tID, db, animurl)

    plantoid.send_serial_message("awake") 





def poem_make_prompts(plantoid, sermon, audio_file):

    from mutagen.mp3 import MP3
    
    # generate prompt from the response text 
    duration = MP3(audio_file).info.length
    fps = 20
    n_prompt = max(2, int(duration / 3)) # 3 seconds per prompt

    prompt = get_video_prompt(sermon, n_prompt)
    response = PlantoidSpeech.GPTmagic(prompt, trim=False)
    prompts = process_video_prompts(plantoid, response)
    return prompts



def poem_make_video(path, sermon, audio_file, prompts):
    
    from mutagen.mp3 import MP3
    duration = MP3(audio_file).info.length

    print("Generative NEW video with Glitchbox for --> POEM")

    init_img = path + "./init_img.jpg"
    init_strength = 0.75
    fps = 20
    loras = 28 # NO LORA
    return glitchbox_video_journey(prompts, duration, fps, init_img, init_strength, loras)


def opera_make_video(path, sermon, audio_file, prompts):

    from mutagen.mp3 import MP3
    duration = MP3(audio_file).info.length

    print("Generative NEW video with Glitchbox for --> OPERA")

    init_img = path + '/../lib/plantoid/behaviors/glitchbox/' + 'input2.jpg'
    init_strength = 0.9
    fps = "15"
    loras = "21" # twisted bodies & water

    return glitchbox_video_scheduler(audio_file, duration, fps, init_img, init_strength, loras)
    # os.system('python3.10 ' + glitchbox_path + f"grpc_prompt_journey.py --server {glitchbox_server} --scheduler --fps {fps} --init-image {init_img} --audio {audio_mp3} --duration {duration} --curation {loras} --output {movie_path}" )


# def poem_metadata(plantoid, network, tID, db, prompts):

#     movie_path = None
#     animurl = None

#     # check if movie exist for that particular token ID
#     path = network.plantoid_path
#     if os.path.exists(path + "/videos/" + network.name + "/" + tID + "_movie.mp4"):
#         movie_path = path + "/videos/" + network.name + "/" + tID + "_movie.mp4"

#     # check if audio exists to create movie
#     elif os.path.isfile(path + "/audios/" + network.name + "/" + tID + "_audio.mp3"):
#         plantoid.send_serial_message("thinking")

#         if(network.failsafe == 0):
#             print("Generative NEW video with Glitchbox")
#             init_img = path + "./init_img.jpg"
#             init_strength = 0.7
#             movie_path = glitchbox_video_journey(path, tID, network, init_img, init_strength)
#             save_video_fallback(path, movie_path)

#         elif(network.failsafe == 1 or movie_path == None):
#             print("Failsafe: using fallback video")
#             movie_path = fallback_video(path, tID, network.name)
        
#         # Add audio to the video
#         movie_path = save_video_with_audio(path, movie_path, tID, network.name)

#     # PIN movie to IPFS
#     animurl = pin_movie(movie_path)
#     if(animurl):
#         record_metadata(plantoid, network, tID, db, animurl)

#     plantoid.send_serial_message("awake")