import os, json, boto3
from boto3.dynamodb.conditions import Key

ddb = boto3.resource("dynamodb")
TABLE = ddb.Table(os.environ["TABLE_NAME"])
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")

def _resp(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps(body)
    }

def lambda_handler(event, context):
    # HTTP API (v2) request: query string in event.get("queryStringParameters")
    q = (event.get("queryStringParameters") or {})
    show_id = q.get("showId")
    if not show_id:
        return _resp(400, {"error":"Missing required query parameter 'showId'"})

    # Query items by partition key showId
    try:
        r = TABLE.query(
            KeyConditionExpression=Key("showId").eq(show_id)
        )
        items = r.get("Items", [])
        # Sort by episodeId if you like (optional)
        items.sort(key=lambda x: x.get("episodeId",""))
        return _resp(200, {"items": items, "count": len(items)})
    except Exception as e:
        return _resp(500, {"error": str(e)})
