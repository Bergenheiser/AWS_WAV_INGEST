import json
import sys
from time import sleep

import boto3
import commons
import settings

logger = commons.log()

if settings.STACK_URL == "":
    logger.error("STACK_URL is not defined")
    sys.exit(1)
if settings.SQS_DELETE == "":
    logger.error("SQS_DELETE is not defined")
    sys.exit(1)

sqs = boto3.resource("sqs", endpoint_url=settings.STACK_URL)
s3 = boto3.client("s3", endpoint_url=settings.STACK_URL)
queue = sqs.get_queue_by_name(QueueName=settings.SQS_DELETE)
logger.info(f"Listening on {queue.url}")

while True:
    logger.info("Looking for messages")
    for message in queue.receive_messages():
        data = json.loads(message.body)
        try:
            s3.delete_object(
                Bucket=data["bucket"],
                Key=data["file"],
            )
            logger.info(f"File deleted {data["bucket"]} {data["key"]}")
            #problèmes de lecture du format d'entrée
        except:
            logger.error("File not deleted")
        message.delete()
    sleep(10)
