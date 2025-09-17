import os, json, boto3, datetime

ddb = boto3.client("dynamodb")
TABLE = os.environ["TABLE_NAME"]
NEW_DAYS = int(os.environ.get("NEW_DAYS", "7"))

def _is_new(date_str):
    try:
        rel = datetime.date.fromisoformat(date_str)  # "YYYY-MM-DD"
    except:
        return True  # treat unknown dates as new
    today = datetime.date.today()
    return (today - rel).days <= NEW_DAYS

def lambda_handler(event, context):
    for record in event.get("Records", []):
        msg = json.loads(record["body"])

        show_id    = msg.get("showId", "unknown-show")
        episode_id = msg.get("episodeId", "unknown-ep")
        title      = msg.get("title", "")
        release    = msg.get("releaseDate", "")

        is_new = _is_new(release)

        ddb.put_item(
            TableName=TABLE,
            Item={
                "showId":     {"S": show_id},
                "episodeId":  {"S": episode_id},
                "title":      {"S": title},
                "releaseDate":{"S": release},
                "isNew":      {"BOOL": is_new}
            }
        )
    return {"ok": True}