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
            # TODO PART IV G s3.delete_object
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
            logger.info(f"File deleted {data['file']['bucket']} {data['file']['key']}")
        except:
            logger.error("File not deleted")
        message.delete()
    sleep(10)
