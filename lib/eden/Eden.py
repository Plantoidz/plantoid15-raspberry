import requests
import time
import json
import os

from dotenv import load_dotenv


# args = https://github.com/abraham-ai/eden-api/blob/main/mongo-init.js


load_dotenv()

EDEN_API_URL = "https://api.eden.art"
EDEN_KEY = os.environ.get("EDEN_KEY")
EDEN_SECRET = os.environ.get("EDEN_SECRET")

header = {
     "x-api-key": EDEN_KEY,
     "x-api-secret": EDEN_SECRET,
}


def run_task(generator_name, config):

    # create request object
    request = {
        "generatorName": generator_name,
        "config": config
    }

    print("json ="); print(request)
    print("headers = "); print(header)

    response = requests.post(
        f'{EDEN_API_URL}/tasks/create', 
        json=request, 
        headers=header
    )

    if response.status_code == 200:

        result = response.json()
        taskId = result['taskId']

        print("TASK ID ====  " + taskId)

        response = requests.get(
            'https://api.eden.art/tasks/' + taskId,
            headers=header
        )


        if response.status_code == 200:
            
            result = response.json()

            pretty_json = json.dumps(result, indent=4)
    #        print(pretty_json)

            with open("/tmp/sample.json", "w") as outfile:
                outfile.write(pretty_json)

   #         print(len(result['docs']))
   #         task = result['docs'][-1]
   #         status = task['status']
            
            task = result['task']
            status = task['status']
            progress = task['progress']
            print(status)
            print(progress)


            if status == 'completed':
            
                # This is somewhat dubious
                if 'creation' in task:
                    return task
            
            elif status == 'failed':

                print("FAILED!")
                return None
                # TODO: throw exception

            else:

                print('Something else')
                return None
                # TODO: throw exception

        else:
            print('An Error Occurred! The EDEN API responded with', response.status_code)
            return None
            # TODO: throw exception

    else:
        print('An Error Occurred! The EDEN API responded with', response.status_code)
        return None
        # TODO: throw exception
