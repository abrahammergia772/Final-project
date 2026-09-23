# Search YouTube for patient-education videos. No API key is required.
# The hospital API calls YouTube and returns only the fields the video pages need.
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger("mediq.youtube")

_CACHE = {}
_CACHE_TTL = 600
_BLOCK = (
    "music video", "official music", "lyrics", "gameplay", "gaming", "minecraft",
    "trailer", "prank", "karaoke", "unboxing", "highlights", "reaction video",
)

def _text(node):
    if not isinstance(node, dict):
        return ""
    if isinstance(node.get("simpleText"), str):
        return node["simpleText"]
    runs = node.get("runs") or []
    return "".join(part.get("text", "") for part in runs if isinstance(part, dict))


def _walk_videos(node, found):
    if isinstance(node, dict):
        video = node.get("videoRenderer")
        if isinstance(video, dict) and video.get("videoId"):
            found.append(video)
        for value in node.values():
            _walk_videos(value, found)
    elif isinstance(node, list):
        for value in node:
            _walk_videos(value, found)


def _health_query(query):
    text = " ".join(str(query or "").split())[:120]
    lowered = text.lower()
    hints = ("health", "medical", "patient", "disease", "symptom", "treatment", "hospital", "clinic", "medicine", "care")
    if text and not any(hint in lowered for hint in hints):
        text = text + " health education"
    return text


def _card(video, query):
    video_id = str(video.get("videoId") or "")
    if not video_id or not all(ch.isalnum() or ch in "-_" for ch in video_id):
        return None
    title = _text(video.get("title")) or "Health video"
    channel = _text(video.get("ownerText")) or _text(video.get("longBylineText")) or "YouTube"
    hay = (title + " " + channel).lower()
    if any(word in hay for word in _BLOCK):
        return None
    snippets = video.get("detailedMetadataSnippets") or []
    description = ""
    if snippets and isinstance(snippets[0], dict):
        description = _text(snippets[0].get("snippetText"))
    return {
        "id": video_id,
        "title": title,
        "channel": channel,
        "video_id": video_id,
        "url": "https://www.youtube.com/watch?v=" + video_id,
        "search": query,
        "conditions": [],
        "duration": _text(video.get("lengthText")) or "—",
        "views": _text(video.get("shortViewCountText")) or _text(video.get("viewCountText")) or "—",
        "category": "YouTube",
        "description": description or "Educational video from YouTube. Not medical advice.",
        "thumb": "https://i.ytimg.com/vi/" + video_id + "/hqdefault.jpg",
        "live": True,
        "embeddable": True,
    }


def _fetch_innertube(query):
    body = json.dumps({
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20250920.01.00",
                "hl": "en",
                "gl": "US",
            }
        },
        "query": query,
    }).encode()
    req = urllib.request.Request(
        "https://www.youtube.com/youtubei/v1/search?prettyPrint=false",
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Origin": "https://www.youtube.com",
            "Referer": "https://www.youtube.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode("utf-8", "replace"))


def search_youtube(query, max_results=12):
    cleaned = _health_query(query)
    if not cleaned:
        return []
    limit = max(1, min(int(max_results or 12), 12))
    now = time.time()
    cached = _CACHE.get(cleaned.lower())
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1][:limit]
    try:
        payload = _fetch_innertube(cleaned)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        log.warning("youtube search failed: %s", exc)
        raise
    found = []
    _walk_videos(payload, found)
    items = []
    seen = set()
    for video in found:
        card = _card(video, cleaned)
        if not card or card["video_id"] in seen:
            continue
        seen.add(card["video_id"])
        items.append(card)
        if len(items) >= 12:
            break
    _CACHE[cleaned.lower()] = (now, items)
    if len(_CACHE) > 80:
        for key, _ in sorted(_CACHE.items(), key=lambda item: item[1][0])[:40]:
            _CACHE.pop(key, None)
    return items[:limit]
