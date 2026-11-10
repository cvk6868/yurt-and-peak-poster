"""Zet bestanden online (Cloudinary) en publiceert ze via de Instagram API (Facebook Login)."""
import hashlib, json, os, random, time
import requests

MAP = os.path.dirname(os.path.abspath(__file__))
INST = json.load(open(os.path.join(MAP, "instellingen.json")))
GRAPH = f"https://graph.facebook.com/{os.environ.get('GRAPH_VERSIE', INST['graph_versie'])}"


def env(naam):
    w = os.environ.get(naam)
    if not w:
        raise SystemExit(f"Ontbrekende instelling: {naam}")
    return w


def upload(pad, soort):
    """Upload naar Cloudinary; soort is 'image' of 'video'. Geeft de publieke URL."""
    cloud, key, secret = env("CLOUDINARY_CLOUD"), env("CLOUDINARY_KEY"), env("CLOUDINARY_SECRET")
    ts = str(int(time.time()))
    sig = hashlib.sha1(f"timestamp={ts}{secret}".encode()).hexdigest()
    with open(pad, "rb") as f:
        r = requests.post(f"https://api.cloudinary.com/v1_1/{cloud}/{soort}/upload",
                          data={"api_key": key, "timestamp": ts, "signature": sig}, files={"file": f}, timeout=300)
    r.raise_for_status()
    return r.json()["secure_url"]


def _ok(r):
    if r.status_code >= 400:
        raise RuntimeError(f"Instagram-fout {r.status_code}: {r.text[:500]}")
    return r.json()


def wacht_tot_klaar(container_id, token, max_min=8):
    for _ in range(max_min * 3):
        r = _ok(requests.get(f"{GRAPH}/{container_id}", params={"fields": "status_code", "access_token": token}, timeout=60))
        if r.get("status_code") == "FINISHED":
            return
        if r.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram weigert de media: {r}")
        time.sleep(20)
    raise RuntimeError("Instagram was niet op tijd klaar met verwerken.")


def zoek_audio(ig_id, token, minimale_duur_sec, zoekterm, seed=None):
    r = _ok(requests.get(f"{GRAPH}/ig_audio", params={"audio_type": "music", "user_id": ig_id, "search_query": zoekterm,
                                                       "access_token": token}, timeout=60))
    kandidaten = [a for a in r.get("audio", []) if a.get("duration_in_ms", 0) >= minimale_duur_sec * 1000]
    if not kandidaten:
        return None
    return random.Random(seed).choice(kandidaten)


def publiceer(container_id, ig_id, token):
    wacht_tot_klaar(container_id, token)
    return _ok(requests.post(f"{GRAPH}/{ig_id}/media_publish", data={"creation_id": container_id, "access_token": token}, timeout=60))["id"]


def post_reel(video_url, caption, ig_id, token, audio_id=None):
    data = {"media_type": "REELS", "video_url": video_url, "caption": caption, "access_token": token}
    if audio_id:
        data["audio_configuration"] = json.dumps({"audio_id": audio_id, "audio_volume": INST["audio_volume"],
                                                  "video_volume": INST["video_volume"]})
    cid = _ok(requests.post(f"{GRAPH}/{ig_id}/media", data=data, timeout=120))["id"]
    return publiceer(cid, ig_id, token)


def post_carrousel(image_urls, caption, ig_id, token):
    kinderen = []
    for u in image_urls:
        kinderen.append(_ok(requests.post(f"{GRAPH}/{ig_id}/media", data={"image_url": u, "is_carousel_item": "true",
                                                                          "access_token": token}, timeout=120))["id"])
    for k in kinderen:
        wacht_tot_klaar(k, token)
    cid = _ok(requests.post(f"{GRAPH}/{ig_id}/media", data={"media_type": "CAROUSEL", "children": ",".join(kinderen),
                                                            "caption": caption, "access_token": token}, timeout=120))["id"]
    return publiceer(cid, ig_id, token)
