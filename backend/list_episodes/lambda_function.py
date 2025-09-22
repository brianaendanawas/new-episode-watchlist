import os, json, boto3, datetime

s3 = boto3.client('s3')

BUCKET = os.environ['BUCKET']
FEEDS_PREFIX = os.environ.get('FEEDS_PREFIX', 'feeds/')
FLAGS_PREFIX = os.environ.get('FLAGS_PREFIX', 'flags/')
NEW_WINDOW_DAYS = int(os.environ.get('NEW_WINDOW_DAYS', '14'))
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', '*')
# Optional alias map:
# Set ALIASES='{"show-wednesday":"show1"}'  (JSON) or 'show-wednesday=show1,foo=bar'
ALIASES_RAW = os.environ.get('ALIASES', '')

def _parse_aliases(s):
    s = (s or '').strip()
    if not s: return {}
    try:
        d = json.loads(s)
        return {str(k).strip(): str(v).strip() for k, v in d.items()}
    except Exception:
        out = {}
        for pair in s.split(','):
            if '=' in pair:
                a, b = pair.split('=', 1)
                out[a.strip()] = b.strip()
        return out

ALIASES = _parse_aliases(ALIASES_RAW)

def _resp(status, body, event_headers=None):
    req_headers = event_headers or {}
    req_origin = req_headers.get('origin') or req_headers.get('Origin') or ''
    cors = ALLOWED_ORIGIN if req_origin == '' else (req_origin if req_origin == ALLOWED_ORIGIN else ALLOWED_ORIGIN)
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": cors,
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body)
    }

def _load_feed_items(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = json.loads(obj['Body'].read())
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ('items', 'episodes', 'data', 'results'):
            v = data.get(k)
            if isinstance(v, list):
                return v
    return []

def lambda_handler(event, context):
    params = event.get('queryStringParameters') or {}
    req_show = (params.get('showId') or 'show1').strip()
    show_id = ALIASES.get(req_show, req_show)  # map friendly -> filename if needed

    # 1) Load feed (try alias first, then original as fallback)
    tried = []
    for candidate in (show_id, req_show):
        key = f"{FEEDS_PREFIX}{candidate}.json"
        tried.append(key)
        try:
            print("Loading feed:", BUCKET, key)
            items = _load_feed_items(BUCKET, key)
            break
        except Exception as e:
            last_err = repr(e)
            items = None
    if items is None:
        print("FEED_LOAD_ERROR for keys:", tried, "last_err:", last_err)
        # Return 200 with empty items so UI doesn't crash
        return _resp(200, {"count": 0, "items": [], "note": "feed not found" }, event.get('headers'))

    # 2) Load flags (optional)
    flagged_ids = set()
    try:
        flags_key = f"{FLAGS_PREFIX}{show_id}.json"
        print("Loading flags:", BUCKET, flags_key)
        flags_obj = s3.get_object(Bucket=BUCKET, Key=flags_key)
        flagged_ids = set(json.loads(flags_obj['Body'].read()))
    except Exception as e:
        print("FLAGS_LOAD_WARN:", repr(e))

    today = datetime.datetime.utcnow().date()
    out = []
    for ep in items:
        if not isinstance(ep, dict): 
            continue
        eid = ep.get('episodeId') or ep.get('id')
        is_new = bool(eid in flagged_ids)
        if not is_new:
            rd = (ep.get('releaseDate') or '')[:10]
            try:
                d = datetime.date.fromisoformat(rd)
                is_new = (today - d).days <= NEW_WINDOW_DAYS
            except Exception:
                pass
        ep['isNew'] = bool(is_new)
        out.append(ep)

    return _resp(200, {"count": len(out), "items": out}, event.get('headers'))
