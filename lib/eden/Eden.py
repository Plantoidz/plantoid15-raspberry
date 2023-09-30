import requests
import time
import json
import os
from tqdm import tqdm

from dotenv import load_dotenv


# args = https://github.com/abraham-ai/eden-api/blob/main/mongo-init.js


load_dotenv()

EDEN_API_URL = "https://api.eden.art"
EDEN_API_KEY = os.environ.get("EDEN_API_KEY")
EDEN_API_SECRET = os.environ.get("EDEN_API_SECRET")

header = {
     "x-api-key": EDEN_API_KEY,
     "x-api-secret": EDEN_API_SECRET,
}


def run_task(generator_name, config):

    print('running eden task...')

    # create request object
    request = {
        "generatorName": generator_name,
        "config": config
    }

    # print("json ="); print(request)
    # print("headers = "); print(header)

    response = requests.post(
        f'{EDEN_API_URL}/tasks/create', 
        json=request, 
        headers=header
    )

    if response.status_code == 200:

        result = response.json()
        taskId = result['taskId']

        print("TASK ID ====  " + taskId)

        task_status = ''
        current_progress = 0

        use_file = os.getcwd()+"/tmp/sample.json"

        print('using output file:', use_file)

        # instantiate a progress bar
        progress_bar = tqdm(total=100, desc="Eden Video Generation Progress", unit="pct")

        while not (task_status == 'completed'):
                    
            response = requests.get(
                'https://api.eden.art/tasks/' + taskId,
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
                
                    if 'creation' in task:

                        print('video generation completed, returning task')
                        return task
                
                if task_status == 'failed':

                    raise Exception('Status failed!', task_status)

            else:
                raise Exception('An Error Occurred! The EDEN API responded with', response.status_code)

    else:
        raise Exception('An Error Occurred! The EDEN API responded with', response.status_code)
