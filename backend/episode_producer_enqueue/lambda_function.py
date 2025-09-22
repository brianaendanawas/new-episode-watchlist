import os, json, boto3

sqs = boto3.client('sqs')

QUEUE_URL = os.environ['QUEUE_URL']
# comma-separated list of show IDs you maintain in S3 under feeds/<showId>.json
SHOWS = [s.strip() for s in os.environ.get('SHOWS', 'show-wednesday').split(',') if s.strip()]

def lambda_handler(event, context):
    # one message per show; worker recomputes flags from the feed
    entries = []
    for show in SHOWS:
        entries.append({'Id': show, 'MessageBody': json.dumps({'showId': show})})
    # send in batches of 10 if needed
    for i in range(0, len(entries), 10):
        sqs.send_message_batch(QueueUrl=QUEUE_URL, Entries=entries[i:i+10])
    return {'sent': len(entries)}
