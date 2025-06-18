
import requests
import time
import json
import os
from tqdm import tqdm

#import lib.eden.Eden as Eden


from dotenv import load_dotenv


# args = https://github.com/abraham-ai/eden-api/blob/main/mongo-init.js


config = {'interpolation_texts': 
    ["Drawing by M. C. Escher with a strong solar-punk flavor representing: A scene of vibrant greens and blues, a garden where life thrives,A butterfly's delicate flutter, its energy vividly alive.A visual symphony, under the sun's watchful eye,Nature's strength and beauty reign, its power we can't deny. Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined.", 
     'Drawing by M. C. Escher with a strong solar-punk flavor representing: A garden filled with lush green foliage, a butterfly gracefully hovers above. Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined.', 
     'Drawing by M. C. Escher with a strong solar-punk flavor representing: Its wings beat with vitality, carrying life and vigor high up into the sky. Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined.', 
     'Drawing by M. C. Escher with a strong solar-punk flavor representing: The delicate creature reminds us of the vastness of existence, as it flutters with vibrance. Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined.', 
     "Drawing by M. C. Escher with a strong solar-punk flavor representing: A display of vibrant colors dances beneath the warm rays of the sun, showcasing nature's unrivaled strength and resilience. Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined.", 
     'Drawing by M. C. Escher with a strong solar-punk flavor representing: This butterfly is a symbol of hope, embodying our own aspirations and ambitions. Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined.', 
     'Drawing by M. C. Escher with a strong solar-punk flavor representing: Let us take inspiration from its flight, and strive to capture the boundless energy and vitality it possesses. Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined.', 
     'Drawing by M. C. Escher with a strong solar-punk flavor representing: The greens and blues of the Earth and sky hold endless possibilities, waiting for us to seize. Hyper realistic, detailed, intricate, best quality, hyper detailed, ultra realistic, sharp focus, delicate and refined.'], 
    
    'interpolation_init_images': ['https://edenartlab-prod-data.s3.us-east-1.amazonaws.com/44050c3ab6e427ca6fa851f1a66cfe7dcacd996818d05bd09395f1e3790ad91c.jpg', 
                                  'https://edenartlab-prod-data.s3.us-east-1.amazonaws.com/44050c3ab6e427ca6fa851f1a66cfe7dcacd996818d05bd09395f1e3790ad91c.jpg', 
                                  'https://edenartlab-prod-data.s3.us-east-1.amazonaws.com/44050c3ab6e427ca6fa851f1a66cfe7dcacd996818d05bd09395f1e3790ad91c.jpg', 
                                  'https://edenartlab-prod-data.s3.us-east-1.amazonaws.com/44050c3ab6e427ca6fa851f1a66cfe7dcacd996818d05bd09395f1e3790ad91c.jpg', 
                                  'https://edenartlab-prod-data.s3.us-east-1.amazonaws.com/44050c3ab6e427ca6fa851f1a66cfe7dcacd996818d05bd09395f1e3790ad91c.jpg', 
                                  'https://edenartlab-prod-data.s3.us-east-1.amazonaws.com/44050c3ab6e427ca6fa851f1a66cfe7dcacd996818d05bd09395f1e3790ad91c.jpg', 
                                  'https://edenartlab-prod-data.s3.us-east-1.amazonaws.com/44050c3ab6e427ca6fa851f1a66cfe7dcacd996818d05bd09395f1e3790ad91c.jpg', 
                                  'https://edenartlab-prod-data.s3.us-east-1.amazonaws.com/44050c3ab6e427ca6fa851f1a66cfe7dcacd996818d05bd09395f1e3790ad91c.jpg'], 
    
    'interpolation_init_images_min_strength': 0, 
    'interpolation_init_images_max_strength': 0, 
    'interpolation_init_images_power': 0.5, 
    'n_film': 2, 
    'latent_blending_skip_f': [0.1, 0.9], 
    'guidance_scale': 20, 
    'width': 1024, 
    'height': 1024, 
    'stream': False, 
    'steps': 20, 
    'fps': 7, 
    'n_frames': 73
    }


load_dotenv()

EDEN_API_URL = "https://api.eden.art"
EDEN_API_KEY = os.environ.get("EDEN_API_KEY")
#EDEN_API_SECRET = os.environ.get("EDEN_API_SECRET")  # @@@@

header = {
     "x-api-key": EDEN_API_KEY,
    # "x-api-secret": EDEN_API_SECRET, # @@@@
}


def make_eden_API_call(config):

    s = time.time()
    task_result = run_task("real2real", config)
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

        print("task_result!!!", task_result)
        print(task_result.keys())
        
        # NOTE: this will be stored on replicate servers, and has to be saved locally
        # output_file = task_result['output']['files'][0] 
        output_file = task_result["result"][0]['output'][0]['url'] # @@@@

        print('output file location:', output_file)
        return output_file

    else:
        raise Exception("Eden.run_task() did not return a valid result")



def run_task(generator_name, config):

    print('running eden task...')

    # create request object
    request = {
        "tool": generator_name,     # @@@
        "args": config              # @@@
    }

    # print("json ="); print(request)
    # print("headers = "); print(header)

    response = requests.post(
        f'{EDEN_API_URL}/v2/tasks/create',  # @@@
        json=request, 
        headers=header
    )

    if response.status_code == 200:

        result = response.json()
        taskId = result['task']['_id']      # @@@

        print("TASK ID ====  " + taskId)

        task_status = ''
        current_progress = 0

        use_file = os.getcwd()+"/tmp/sample.json"

        print('using output file:', use_file)

        # instantiate a progress bar
        progress_bar = tqdm(total=100, desc="Eden Video Generation Progress", unit="pct")

        while not (task_status == 'completed'):
                    
            response = requests.get(
                'https://api.eden.art/v2/tasks/' + taskId,  # @@@
                headers=header
            )

            if response.status_code == 200:

                result = response.json()

                pretty_json = json.dumps(result, indent=4)
        #        print(pretty_json)

                with open(use_file, "w") as outfile:
                    outfile.write(pretty_json)

                
                task = result['task']
                task_status = task['status']
                task_progress = task['progress']

                # print('task', task)
                # print('task status', task_status)
                # print('task progress', task_progress)
                # print('waiting to re-request...\n')
                time.sleep(10)

                # update the progress bar, round and scale values to be relative to 100
                progress_bar.update(100 * round(task_progress, 2) - current_progress)
    
                current_progress = 100 * round(task_progress, 2)

                if task_status == 'completed':
                    
                    return task
                
                    # if 'creation' in task:  @@@

                    #     print('video generation completed, returning task')
                    #     return task
                
                if task_status == 'failed':

                    raise Exception('Status failed!', task_status)

            else:
                raise Exception('An Error Occurred! The EDEN API responded with', response.status_code)

    else:
        raise Exception('An Error Occurred! The EDEN API responded with', response.status_code)
    
    
    
if __name__ == "__main__":
    make_eden_API_call(config)
