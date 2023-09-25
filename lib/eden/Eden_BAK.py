import requests
import time
import json
import os

from dotenv import load_dotenv


# args = https://github.com/abraham-ai/eden-api/blob/main/mongo-init.js

EDEN_API_URL = "https://api.eden.art"

load_dotenv()

EDEN_KEY = os.environ.get("EDEN_KEY")
EDEN_SECRET = os.environ.get("EDEN_SECRET")

header = {
     "x-api-key": EDEN_KEY,
     "x-api-secret": EDEN_SECRET,
}


def run_task(generatorName, config):
    request = {
        "generatorName": generatorName,
        "config": config
    }

    print("json ="); print(request)
    print("headers = "); print(header)

    response = requests.post(
        f'{EDEN_API_URL}/tasks/create', 
        json=request, 
        headers=header
    )

    if response.status_code != 200:
        print(response.text)
        return None
    
    result = response.json()
    taskId = result['taskId']

    print("TASK ID ====  " + taskId)


    while(1):
        
        try:
 

            response = requests.get(
                 'https://api.eden.art/tasks/' + taskId,
                 headers=header
            )


 #           response = requests.get(
 #               'https://api.eden.art/tasks', 
 #               json={"taskId": [taskId]},
 #               headers=header
 #           )

            if response.status_code != 200:
                print(response.text)
                return None

        except Exception as err:
            print("An exception occurred while probing the API task " + taskId)
            print(f"Unexpected {err=}, {type(err)=}")



        try:

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



            if status == 'completed' and ('creation' in task):
                    return task
            elif status == 'failed':
                        print("FAILED!")
                        return None


        except Exception as err:
            print("An exception occurred while processing the JSON")
            print(f"Unexpected {err=}, {type(err)=}")
            # time.sleep(1)



#config = {
#    "text_input": "i am a dog"
#}

#result = run_task("create", config)

#output_url = result['output'][-1]
#print(output_url)
  
