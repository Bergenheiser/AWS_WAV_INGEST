import sys

import boto3
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import commons, settings

logger = commons.log()

if settings.STACK_URL == "":
    logger.error("STACK_URL is not defined")
    sys.exit(1)

sqs = boto3.client("sqs", endpoint_url=settings.STACK_URL)


class Asset(BaseModel):
    bucket: str
    file: str
    channel_count: int
    frame_count: int
    sample_rate: int
    bits_per_sample: int
    duration: str


app = FastAPI(
    title="Assets",
    description="""Assets service""",
    docs_url="/",
)

assets = {}


@app.get("/assets")
async def list():
    return assets


@app.get("/asset/{file}")
async def get(file: str):
    if file in assets.keys():
        return assets[file]
    return JSONResponse(status_code=404, content={"message": "asset not found"})


@app.delete("/asset/{file}")
async def delete(file: str):
    # TODO PART IV F , find asset in assets, send delete order sqs.send_message and delete item from assets dictionnary
    if file in assets.keys():
        obj = assets[file]
        sqs.send_message(
            QueueUrl=commons.get_queue_url(sqs, "s3-delete-messages"),
            MessageBody=commons.dict_tojson(obj),
        )
        logger.info(f"{obj['bucket']} - {obj['file']}")
        assets.pop(file)
        return JSONResponse(
            status_code=200, content={"message": "Deleted with Success"}
        )
    else:
        return JSONResponse(status_code=404, content={"message": "File not found"})


@app.post("/asset")
async def create(data: Asset):
    asset = commons.basemodel_to_dict(data)
    if asset["file"] not in assets.keys():
        assets[asset["file"]] = asset
        return assets[asset["file"]]
    return JSONResponse(
        status_code=200, content={"message": f"asset already exists {asset['file']}"}
    )
