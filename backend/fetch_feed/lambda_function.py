import os, json, boto3

s3  = boto3.client("s3")
sqs = boto3.client("sqs")

BUCKET = os.environ["BUCKET_NAME"]
KEY    = os.environ["FEED_KEY"]
QUEUE  = os.environ["QUEUE_URL"]

def lambda_handler(event, context):
    obj = s3.get_object(Bucket=BUCKET, Key=KEY)
    data = json.loads(obj["Body"].read())

    show_id = data.get("showId", "unknown-show")
    episodes = data.get("episodes", [])

    for ep in episodes:
        msg = {
            "showId": show_id,
            "episodeId": ep.get("episodeId"),
            "title": ep.get("title"),
            "releaseDate": ep.get("releaseDate")
        }
        sqs.send_message(QueueUrl=QUEUE, MessageBody=json.dumps(msg))

    return {"enqueued": len(episodes)}
