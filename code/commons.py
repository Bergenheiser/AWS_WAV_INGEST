import json
import logging
import sys

from fastapi.encoders import jsonable_encoder


def basemodel_to_dict(item):
    return jsonable_encoder(item)


def dict_tojson(item):
    return json.dumps(item)


def get_queue_url(sqs, queue_name):
    return sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]


def log():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
