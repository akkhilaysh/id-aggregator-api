from fastapi import FastAPI
import os
import logging
import time
import threading
import requests

import redis
import pika


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s : %(levelname)s : %(message)s",
    filename="unique_id_capture.log",  
)

app = FastAPI()

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Redis DB key for storing unique ids
IDS_KEY = "unique_ids_for_current_minute"
ENDPOINTS_KEY = "endpoints_for_current_minute"

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", "5672"))
RABBIT_QUEUE = os.getenv("RABBIT_QUEUE", "counts_queue")
# So that pika logs don't flood the log file
logging.getLogger("pika").setLevel(logging.WARNING) 

connection = None
channel = None

def setup_rabbitmq():
    global connection, channel
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                port=RABBIT_PORT
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue=RABBIT_QUEUE, durable=True)
        logging.debug("[rabbitmq] Connected and queue declared. Will be posting to rabbitmq instead of the log file.")
    except Exception as e:
        logging.error(f"[rabbitmq] Connection failed: {e}")


def aggregate_ids():
    while True:
        time.sleep(60)
        try:
            count = redis_client.scard(IDS_KEY)

            endpoints = redis_client.smembers(ENDPOINTS_KEY)
            # clean endpoint strings
            endpoints = [ep.decode("utf-8") for ep in endpoints]

            # Publish to rabbitmq
            if channel:
                message = f"{count}"
                channel.basic_publish(
                    exchange="",
                    routing_key=RABBIT_QUEUE,
                    body=message.encode("utf-8"),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                logging.debug(f"[aggregate_ids] Published to rabbitmq: {message}")
            else:                
                # Instead write to the log file since no distributed streaming service 
                # if (rabbitmq) is not setup
                logging.info(f"Unique ID count for the last minute: {count}")

            # POST to any endpoints recieved within the last minute
            send_post_requests(endpoints, count)

            # Flush the sets in the central Redis DB
            redis_client.delete(IDS_KEY)
            redis_client.delete(ENDPOINTS_KEY)

        except Exception as e:
            logging.error(f"[aggregate_ids] Error in interval of aggregator run: {e}")

"""
Startup Event:
- Start the aggregator thread that runs every 60 seconds
- Setup rabbitmq to publish to a distributed streaming service
"""
@app.on_event("startup")
def startup_event():
    setup_rabbitmq()
    t = threading.Thread(target=aggregate_ids, daemon=True)
    t.start()

# Helper function to send POST requests to the endpoints
def send_post_requests(endpoints, count):
    for url in endpoints:
        try:
            resp = requests.post(f"{url}?count={count}")
            logging.info(f"POST[{url}] returned {resp.status_code}")
        except Exception as e:
            logging.error(f"Failed to POST to {url}: {e}")


@app.get("/api/verve/accept")
def accept(id: int, endpoint: str = None):
    try:
        # Add the ID to the Redis set (centralised db)
        redis_client.sadd(IDS_KEY, id)

        # check if endpoint is provided and add it to the endpoints set
        # we will send POST requests to these endpoints in the aggregator
        if endpoint:
            redis_client.sadd(ENDPOINTS_KEY, endpoint)

        return "ok"
    except Exception as e:
        return "failed"