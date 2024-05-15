import json
import logging
import os
import sys
from pathlib import Path
from time import sleep

import boto3
import commons
import requests
import settings
from wavinfo import WavInfoReader

logger = commons.log()

if settings.STACK_URL == "":
    logger.error("STACK_URL is not defined")
    sys.exit(1)
if settings.SQS_INGEST == "":
    logger.error("SQS_INGEST is not defined")
    sys.exit(1)

sqs = boto3.resource("sqs", endpoint_url=settings.STACK_URL)
s3 = boto3.client("s3", endpoint_url=settings.STACK_URL)

queue = sqs.get_queue_by_name(QueueName=settings.SQS_INGEST)
logger.info(f"Listening on {queue.url}")


def probe_wave(file, bucket):
    file_path = Path(file)
    if file_path.suffix == ".wav":
        try:
            probe = WavInfoReader(file)
        except Exception as e:
            logger.error(e)
            return
        logger.info(f"Probe {file_path.name} {probe}")
        # TODO PART IV B test probe.sample_rate and probe.bits_per_sample else return none
        if probe.fmt.sample_rate == 48000 and probe.fmt.bits_per_sample == 24:
            return {
                "file": file_path.name,
                "bucket": bucket,
                "channel_count": int(probe.fmt.channel_count),
                "frame_count": int(probe.data.frame_count),
                "sample_rate": int(probe.fmt.sample_rate),
                "bits_per_sample": int(probe.fmt.bits_per_sample),
                "duration": f"{probe.data.frame_count / probe.fmt.sample_rate}",
            }
        else:
            print(
                "sample rate: ",
                int(probe.fmt.sample_rate),
                " bitsPerSample: ",
                int(probe.fmt.bits_per_sample),
            )


while True:
    logger.info("Looking for messages")
    for messages in queue.receive_messages():
        data = json.loads(messages.body)
        if "Records" in data.keys():
            for message in data["Records"]:
                if "s3" in message.keys():
                    logger.info(
                        f"New file {message['s3']['bucket']['name']}/{message['s3']['object']['key']}"
                    )
                    path = f"tmp/{message['s3']['object']['key']}"
                    try:
                        s3.download_file(
                            message["s3"]["bucket"]["name"],
                            message["s3"]["object"]["key"],
                            path,
                        )
                        logger.info(
                            f"{message['s3']['bucket']['name']} - {message['s3']['object']['key']} - {path}"
                        )
                    except Exception as e:
                        logger.error(f"{e} File not downloaded")
                        path = None
                    if path:
                        probe = probe_wave(path, message["s3"]["bucket"]["name"])
                        if probe:
                            # probe is valid
                            # TODO PART IV D POST probe to asset API
                            requests.post(settings.ASSET_URL + "/asset", json=probe)
                            # https://www.w3schools.com/python/module_requests.asp
                            logger.info(f"{settings.ASSET_URL}/asset - {probe}")
                        else:
                            # probe is not valid
                            # TODO PART IV E s3.delete_object
                            s3.delete_object(
                                Bucket=message["s3"]["bucket"]["name"],
                                Key=message["s3"]["object"]["key"],
                            )
                            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
                            logger.error("Probe failed, file skipped")
                        # always remove file on /tmp
                        os.remove(path)
        messages.delete()
    sleep(10)
