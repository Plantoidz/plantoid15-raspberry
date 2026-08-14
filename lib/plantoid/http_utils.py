# This file mirrors the web_utils.py feeding pipeline,
# but uses HTTP counter on plantoid.org instead of a blockchain

# HttpObject that mirrors the attributes of Web3Object:
# name, path, plantoid.path, min_amount, failsafe, event_filter
# so the pipeline can be reused without bringing any changes
# adding the .kind = "http" to distinguish between functions

import os
import requests

HTTP_FEED_AMOUNT =  1_000_000_000_000_000 # 0.001 ETH - so that it match the pipeline of blockchain
SERVER_URL = "https://feed.plantoid.org"

class HttpObject:
    kind = "http"
    name = "http" # namespaces files under /videos/http, /metadata/http, etc.
    plantoid_n = None
    path = None             # needed for the video/metadata path
    plantoid_path = None    # needed for the video/metadata path
    min_amount = HTTP_FEED_AMOUNT
    failsafe = 0            # needed for the ingurgitate crypto function
    event_filter = None     # needed for the ingurgitate crypto function
    server_url = SERVER_URL
    reclaim_url = None
    last_counter = None 

def setup(config):

    net = HttpObject()
    net.plantoid_n      = config["plantoid_number"]
    net.path            = config["path"]
    net.plantoid_path   = config["plantoid_path"]
    
    
    # baseline to current counter so we only react to feeds that arrive after startup
    try:
        net.last_counter = _get_counter(net)

    except Exception:
        net.last_counter = 0

    print(f"[http feed] ready, server = {net.server_url}, baseline={net.last_counter}")

    return net


def _get_counter(net):

    r = requests.get(net.server_url + "/counter.php",
                    params={"n": net.plantoid_n}, 
                    timeout=10)
    r.raise_for_status()

    body = r.text.strip()

    if not body: 
        return 0
    else: 
        return int(body)


def check_for_deposits(net):

    # return token_Id, amount if there is a new feed
    # same signature / semantics as web3_utils.check_for_deposits

    count = _get_counter(net)

    if net.last_counter is None:
        net.last_counter = count
        return None

    if count <= net.last_counter:
        return None

    net.last_counter = count # advance baseline - react to one feed
    token_Id = str(count)
    amount = HTTP_FEED_AMOUNT

    print(f"[http feed] tokenId #{token_Id} has been fed")

    return (token_Id, amount)


def publish_video(net, token_Id, movie_path):

    # post the finished video to plantoid.org, return the public URL to QR

    if not movie_path or not os.path.isfile(movie_path):
        print("[http feed] no movie to publish")
        return None

    try:
        with open(movie_path, "rb") as f:
            r = requests.post(
                net.server_url + "/video.php",
                files={"file": (f"{net.plantoid_n}-{token_Id}.mp4", f, "video/mp4")},
                data={"token_id": token_Id, "plantoid": net.plantoid_n},
                timeout=120
            )
            r.raise_for_status()

            url = r.text.strip()
            print("[http feed] published at ---> " + url)
            return url
    except Exception as e:
        print("[http feed] publish failed: " + str(e))
        return None