# TP WORKFLOW MEDIA INGEST

### Rendu : Dimitri COPLEY 3A AVM

## Les services managés AWS

**Complétez la ligne de commande et créez un nouveau bucket S3 nommé `ingest`:**

```shell
awslocal s3api create-bucket --bucket ingest
```

**Que retourne l'API ?**

```shell
{
    "Location": "/ingest"
}
```

**Cette commande renvoie l'emplacement du bucket.**

**Reportez les commandes AWS S3 pour:**

- Ajouter un fichier
- Listez des fichiers
- Supprimer un fichier
    
```shell
    awslocal s3 cp media/audio_1.wav s3://ingest/
    awslocal s3 cp media s3://ingest/ --recursive
    awslocal s3 ls s3://ingest/
    awslocal s3 rm s3://ingest/audio_1.wav
```

Des échantillons sont disponibles dans le dossier media/audio\_(1-5).wav. Déposez les dans le bucket ingest.

--- 
**SQS**

SQS est un service d'échange de messages. (dope)

**Complétez la ligne de commande et créez une nouvelle file SQS nommée `s3-ingest-messages` avec les attributs `file://configs/sqs-retention-config.json`:**

```shell
awslocal sqs create-queue --queue-name s3-ingest-messages --attributes file://configs/sqs-retention-config.json
```

**Quel est le retour de cette commande ?**

```shell
{
    "QueueUrl": "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/s3-ingest-messages"
}
```

**Cette commande renvoie l'URL de la file SQS.**

Il faut configurer le bucket pour qu’il notifie la présence d’un nouveau fichier par cette file SQS.

**Complétez la ligne de commande et appliquez la configuration sur le bucket S3 `ingest` avec la configuration `file://configs/s3-notif-config.json`:**

```shell
awslocal s3api put-bucket-notification-configuration --bucket ingest --notification-configuration file://configs/s3-notif-config.json
```

## IV Workflow d'Ingest

**Configuration**

Créez le fichier `code/settings.py` et complétez les valeurs manquantes en avancant dans le TP.

```python
STACK_URL = "http://localhost:4566"
ASSET_URL = "http://localhost:8000"
SQS_INGEST = "s3-ingest-messages"
SQS_DELETE = ""

```

**Backend API assets**

Le service HTTP assets `code/http_assets.py` présente l'API REST des ressources assets. Ce service utilise le framework Python FastAPI et génére une documentation automatiquement.

Exécutez la commande pour lancer le serveur :

```shell
uvicorn code.http_assets:app --reload
```

Accédez à l'API REST http://localhost:8000 dans un navigateur web.

**Quelles sont les routes proposées par l'API du service ?**

**Les routes proposées par l'API sont les suivantes :
get /assets
get /assets/{asset_id}
post /assets
delete /assets/{asset_id}**

**Analisez le code source du services `code/http_assets.py`. Que faudrait il ajouter pour améliorer le fonctionnement de ce microservice ?**

**Il serait intéressant d'ajouter un service de persistance des données entre mise à jour des services d'api (un pseudo-cache)**

---

**Workflow d'analyse**

Le worker d'analayse `code/worker_probe.py` détecte un message SQS sur la file `s3-ingest-messages`. Il télécharge le fichier, l'analyse et envoie le résultat au service HTTP assets par API.

Modifiez le worker :

1/ Le worker télécharge depuis S3 le media à analyser (PART IV A).

```python
 s3.download_file(message['s3']['bucket']['name'], message['s3']['object']['key'], path)
```

2/ Ajoutez des règles de gestion dans l'analyse (PART IV B):

- Un fichier doit avoir une fréquence d'échantillonnage de `48000` hz et une quantification de `24` bits pour être valide.

3/ Le worker analyse le wav et retourne un dictionnaire. Commpletez ce dictionnaire avec des informations issues du modélè de données de wavinfo (PART IV C):

    - channel_count: int
    - frame_count: int
    - sample_rate: int
    - bits_per_sample: int
    - duration: str (calculée à partir du frame_count et du sample_rate)

**Réponse 2&3 :**

```python
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
```

4/ Cette analyse est envoyée au service HTTP assets par API (PART IV D).

```python
 requests.post(settings.ASSET_URL+"/asset",json=probe)
```

5/ Si l'analyse du fichier est invalide, le ficher est supprimé du bucket S3. Implémetez la suppression de fichier dans le bucket S3. (PART IV E)

```python
s3.delete_object(Bucket=message["s3"]["bucket"]["name"],Key=message['s3']['object']['key'])
```

Exécutez la commande pour lancer le worker :

```shell
python code/worker_probe.py
```

Ajoutez tous les fichiers du répertoire `media` dans le bucket `s3://ingest/` pour déclencher des workflows.

**Listez les fichiers valides sur le bucket `ingest` avec une commande awslocal s3.**

```bash
$ awslocal s3 ls s3://ingest
2024-05-15 13:00:46   17280102 audio_1.wav
2024-05-15 13:00:46   17280122 audio_3.wav
2024-05-15 13:00:46   17280102 audio_5.wav
```

**Récuperez sur l'API du service HTTP assets toutes les analyses enregistrées.**

```json
{
  "audio_1.wav": {
    "bucket": "ingest",
    "file": "audio_1.wav",
    "channel_count": 2,
    "frame_count": 2880000,
    "sample_rate": 48000,
    "bits_per_sample": 24,
    "duration": "60.0"
  },
  "audio_5.wav": {
    "bucket": "ingest",
    "file": "audio_5.wav",
    "channel_count": 2,
    "frame_count": 2880000,
    "sample_rate": 48000,
    "bits_per_sample": 24,
    "duration": "60.0"
  },
  "audio_3.wav": {
    "bucket": "ingest",
    "file": "audio_3.wav",
    "channel_count": 2,
    "frame_count": 2880000,
    "sample_rate": 48000,
    "bits_per_sample": 24,
    "duration": "60.0"
  }
}
```

**Quels fichiers sont invalides et pourquoi sont-ils invalides ?**

**Probe audio_2.wav est invalide car il a une fréquence d'échantillonnage de 44100 hz et une quantification de 16 bits.**

**Probe audio_4.wav est invalide car il a une fréquence d'échantillonnage de 48000 hz et une quantification de 32 bits.**

---

**Workflow de suppression de fichiers**

Créez une file SQS `s3-delete-messages` et completer le fichier settings.py avec la valeur de `SQS_DELETE`
**Complétez la ligne de commande et créez une nouvelle file SQS nommée `s3-delete-messages` avec les attributs `file://configs/sqs-retention-config.json`:**

```bash
awslocal sqs create-queue --queue-name s3-delete-messages --attributes file://configs/sqs-retention-config.json
```

Completez le code du service HTTP assets `code/http_assets.py` pour envoyer un message de suppressions sur la route `DELETE` (PART IV F).

    Il faut sérialiser le message JSON de suppression avec la fonction `commons.dict_tojson` pour l'envoyer sur la file SQS.

```python
   @app.delete("/asset/{file}")
async def delete(file: str):
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

```

Completez le code du worker de suppression de fichier `code/worker_delete.py` (PART IV G).

```python
while True:
    logger.info("Looking for messages")
    for message in queue.receive_messages():
        data = json.loads(message.body)
        print("raw \n : ", message.body)
        print("format \n : ", data)
        try:
            s3.delete_object(
                Bucket=data["bucket"],
                Key=data["file"],
            )
            logger.info(f"File deleted {data['bucket']} {data['file']}")
        except Exception as e:
            logger.error(f"File not deleted: {e}")  # Improved error logging
        message.delete()
    sleep(10)
```

(Utilisez la fonction `commons.dict_tojson` pour serialiser le MessageBody de sqs.send_messsage().)

Le message JSON d'initialisation de la suppression est de cette forme :

```json
{
  "file": {
    "bucket": "",
    "key": ""
  }
}
```

**Note : Mon JSON à la reception ne contient pas une arborescence identique à la votre j'en ai joint un exemple dans les logs du worker ci-dessous**

Ou bucket contient le nom du bucket S3; key contient le nom du fichier.

Exécutez la commande pour lancer le worker de suppression :

```shell
python code/worker_delete.py
```

Supprimez un des assets enregistrés par un appel sur l'API du service assets.

---

**Quelle route est utilisée pour supprimer un asset sur le service HTTP ? Reportez les logs du worker et du service lors d'un suppression.**

**La route empruntée par l'appel d'API de supression est "/assets/{nom_du_fichier}"**

**Logs API DELETE :**

```bash
2024-05-18 08:38:05,981 INFO: ingest - audio_1.wav
INFO:     10.240.0.10:0 - "DELETE /asset/audio_1.wav HTTP/1.1" 200 OK
```

**Logs s3-delete-messages:**

```bash
 {'bucket': 'ingest', 'file': 'audio_3.wav', 'channel_count': 2, 'frame_count': 2880000, 'sample_rate': 48000, 'bits_per_sample': 24, 'duration': '60.0'}
2024-05-18 08:55:43,348 INFO: File deleted ingest audio_3.wav
```
