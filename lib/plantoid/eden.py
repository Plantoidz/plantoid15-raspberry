import os
import json
import sys
from dotenv import load_dotenv
import time
import random
import subprocess
import openai

import re

from mutagen.mp3 import MP3

import lib.eden.Eden as Eden



# Load environment variables from .env file
load_dotenv()

# Access environment variables
openai.api_key = os.environ.get("OPENAI")

model_id = "gpt-3.5-turbo-instruct"
max_tokens = 1024



def create_prompts(path, seed, n_prompt, network_name):

    str_n_prompts = str(n_prompt)
    str_n_prompts_n = str(n_prompt - 1)

    f = open(path + "/responses/" + network_name + "/" +
             seed + "_response.txt", "r")
    
    stri = f.read()

    prompt1 = "Can you generate a short sentence that illustrates the physical environment where the poem takes place in a very graphical manner. Starting with: A scene... "
    prompt1 = prompt1 + "Here's the poem which I'd like you to litterally illustrate: " + stri

    prompt = "I need to illustrate this poem. "
    prompt = prompt + "Can you generate " + str_n_prompts_n + " sentences (not more than " + str_n_prompts_n + " sentences) that illustrate the poem, presented chronologically based on the phrasing of the poem. "
    prompt = prompt + "I don't wont a summary of the plot, I want a graphical description that illustrates the statements of the poem. "
    prompt = prompt + "These descriptions will be used to generate a video illustrating the poem. "
    prompt = prompt + "Every sentence needs to be a self-contained descriptive illustration, that does not refer to the previous or following sentences. "
    prompt = prompt + "Be highly descritive, ideally with a particular style that is reminescent of solar-punk vibes. "
    prompt = prompt + "You can mention colors but only in one of these descriptions, and no reference to colors must be present in the first sentence. "
    prompt = prompt + "Draft your answer with each line starting with the number of the line, followed by a dot, a space, and then the actual description. "
    prompt = prompt + "Here's the poem which I'd like you to litterally illustrate: " + stri

    print("PROOOOOOOOOOOOOOOOMPT: ", prompt)

    response1 = openai.Completion.create(
            engine=model_id,
            prompt=prompt1,
            max_tokens=max_tokens
    )

    response = openai.Completion.create(
        engine=model_id,
        prompt=prompt,
        max_tokens=max_tokens
    )
    
    descri1 = response1.choices[0].text
    descri = response.choices[0].text

    print(descri1)
    print(descri)

    # generate descriptions dir
    if not os.path.exists(path + "/descriptions"):
        os.makedirs(path + "/descriptions");

    # write descriton to file
    with open(path + "/descriptions/" + seed + "_description.txt", "w") as outfile:
        outfile.write(descri1)
        outfile.write(descri)

    lines = re.split("\d.", descri)
    lines.insert(0, descri1)

    prompts = []

    for ln in lines:
        line = ln.strip()
        line = line.replace("\n", "")
        print("["+line+"]")

        if (line):
            # line = "Drawing by M. C. Escher with a strong solar-punk flavor representing: " + line + ". Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration"
            line = "Drawing by M. C. Escher with a strong solar-punk flavor representing: " + line
            line = line + " Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined."
            prompts.append(line)

    print(prompts)

    return prompts




def build_API_request(path, seed, network_name, audio_file, init_image, init_strength):



    audiof = MP3(audio_file)
    audiolen = audiof.info.length  # seconds of the poem length
    print("audiolen === " + str(audiolen))

    seconds_per_prompt = 3
    n_prompt = int(audiolen / seconds_per_prompt)
    print("initial n_prompts = " + str(n_prompt))

    # calculate n_film and fps in order to ensure that the movie doesn't go over 100 frames, for the sake of speed.
    n_film = 2
    fps = 10

    frames = int(audiolen * fps / (2**n_film))

    while frames > 75 and fps > 5:
        fps = fps -1
        frames = audiolen * fps / (2**n_film)

    frames = frames + 6 # better to have a slighter longer movie than slighter shorter one :)

    print("frames = " + str(frames))
    print("fps = " + str(fps))

    # adjust the number of frames to account for rounding errors per prompts
    # frames = frames + len(prompts) # * 1 * n_film;

    # select the number of prompts based on 'audiolen' and 'fps'
    prompt_sec = 4 # if fps = 12, then we want 2 seconds per prompt
    prompt_sec = int(prompt_sec + (10 - fps)) # we decrease the seconds-per-prompt as we reduce the fps rate

    print("new prompt_factor = " + str(prompt_sec))

    n_prompt = int(audiolen / prompt_sec)
    print("new n_prompt = " + str(n_prompt))


    if n_prompt < 2:
        n_prompt = 2

    prompts = []

    while len(prompts) < 2:
        prompts = create_prompts(path, seed, n_prompt, network_name)

    images = []
    i = 0

    while i < len(prompts):
        # images.append("https://minio.aws.abraham.fun/creations-stg/c25c6b80c347d214eef34d67ee9b586f8e7de90662076667563f781c504f2877.webp");
        images.append(init_image)
          #  "https://minio.aws.abraham.fun/creations-stg/2af20071b6342bc55ce70410cff3c4846dba9e497979ad8739668365e816e8de.jpg")
          #   "https://edenartlab-prod-data.s3.us-east-1.amazonaws.com/44050c3ab6e427ca6fa851f1a66cfe7dcacd996818d05bd09395f1e3790ad91c.jpg")
        i = i+1
    

    print("n_film ====> " + str(n_film))


    config = {"interpolation_texts": prompts,
              "interpolation_init_images": images,
              "interpolation_init_images_min_strength": init_strength,
              "interpolation_init_images_max_strength": init_strength,
              "interpolation_init_images_power": 0.5,
              "n_film": n_film,
              "latent_blending_skip_f": [0.1,0.9],
              "guidance_scale": 20,
              "width": 1024,
              "height": 1024,
              "stream": False,
              "steps": 20,
              "fps": fps,
              "n_frames": int(frames)}

    # print(config)
    return config


def make_eden_API_call(config):

    s = time.time()
    task_result = Eden.run_task("real2real", config)
    e = time.time()

    if task_result is not None:

        print("Processing of Interpolation took: " +
        time.strftime("%Hh%Mm%Ss", time.gmtime(e-s)))

        # print(result['output']['files'])

        json_result = json.dumps(task_result, indent=4)

        use_output_file = os.getcwd()+"/tmp/sample2.json"

        print('using output file:', use_output_file)

        with open(use_output_file, "w") as outfile:
            outfile.write(json_result)

        # NOTE: this will be stored on replicate servers, and has to be saved locally
        output_file = task_result['output']['files'][0]

        print('output file location:', output_file)
        return output_file

    else:
        raise Exception("Eden.run_task() did not return a valid result")












# # TODO: figure out if it makes sense to have this
# if __name__ == "__main__":

#     seed = sys.argv[1]
#     path = ""

# #    outf = createVideoFromAudio(path, seed)


# #    prompts = create_prompts(seed)
    
#     config = build_API_request(path, seed)
#     outf = make_eden_API_call(config)

#     videof = None

#     if(outf):
#         videof = get_remote_video(outf)
#         print(videof)

#     else:
#         videof = fallback_video(path, outf)

#     outf = make_video(path, videof, seed)

#     print("NEW VIDEO == " + outf)

# prompts = [
#     "Drawing by M. C. Escher with a strong solar-punk flavor representing: Unmanned vehicles traverse a world bustling with skyscrapers and forests of metal and machine.. Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration",
#     "Drawing by M. C. Escher with a strong solar-punk flavor representing: A golden glow radiates from the skyline, casting a warm hue over a diverse yet homogenous population.. Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration",
#     "Drawing by M. C. Escher with a strong solar-punk flavor representing: Citizens, both robotic and plant-like, work together in a technosymbiotic harmony.. Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration",
#     "Drawing by M. C. Escher with a strong solar-punk flavor representing: Gigantic vines and flower-covered motorways create a unique urban gardenscape.. Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration",
#     "Drawing by M. C. Escher with a strong solar-punk flavor representing: Moving constructions, both metallic and organic, bridge the built environment and the mechanical ecosystem.. Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration",
#     "Drawing by M. C. Escher with a strong solar-punk flavor representing: A thriving metropolis is brightly illuminated by the energy generated from a vast network of plants.. Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration",
#     "Drawing by M. C. Escher with a strong solar-punk flavor representing: Futuristic skyscrapers erupt from the landscape, pulsating with light and spires of growth.. Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration",
#     "Drawing by M. C. Escher with a strong solar-punk flavor representing: An ever-changing mix of flora and fauna, rooted in ancient symbologies, reflect the balanced existence of humans and their machines.. Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration",
#     "Drawing by M. C. Escher with a strong solar-punk flavor representing: The inhabitants move freely, unencumbered by the society they have created; a connected, unified future of plantoid harmony.. Neat lines, extreme detailed illustration, highly detailed linework, sf, intricate artwork masterpiece, ominous, intricate, epic, vibrant, ultra high quality model, solar-punk illustration"
#   ]
