import os, json, boto3, datetime

s3 = boto3.client('s3')

BUCKET = os.environ['BUCKET']
FEEDS_PREFIX = os.environ.get('FEEDS_PREFIX', 'feeds/')
FLAGS_PREFIX = os.environ.get('FLAGS_PREFIX', 'flags/')
NEW_WINDOW_DAYS = int(os.environ.get('NEW_WINDOW_DAYS', '14'))

def _iso_to_date(s):
    try:
        return datetime.date.fromisoformat(s[:10])
    except Exception:
        return None

def lambda_handler(event, context):
    failures = []
    for rec in event.get('Records', []):
        msg_id = rec['messageId']
        try:
            body = json.loads(rec['body'])
            show_id = body['showId']

            # 1) Load feed: feeds/<showId>.json
            feed_key = f"{FEEDS_PREFIX}{show_id}.json"
            obj = s3.get_object(Bucket=BUCKET, Key=feed_key)
            data = json.loads(obj['Body'].read())
            items = data.get('items', data)  # supports plain array or {items:[...]}

            # 2) Compute "new" within N days
            today = datetime.datetime.utcnow().date()
            new_ids = []
            for ep in items:
                eid = ep.get('episodeId') or ep.get('id')
                rd = ep.get('releaseDate') or ''
                d = _iso_to_date(rd)
                if eid and d and (today - d).days <= NEW_WINDOW_DAYS:
                    new_ids.append(eid)

            # 3) Write flags/<showId>.json (public; frontend/API will read)
            out_key = f"{FLAGS_PREFIX}{show_id}.json"
            s3.put_object(
                Bucket=BUCKET,
                Key=out_key,
                Body=json.dumps(sorted(set(new_ids))),
                ContentType='application/json'
            )
        except Exception as e:
            # mark this message as failed so SQS can retry or DLQ it
            failures.append({'itemIdentifier': msg_id})

    # SQS partial batch response
    return {'batchItemFailures': failures}
