"""Dagelijkse taak: post maken, uploaden, plaatsen op Instagram.
   python dagelijks.py --droog   maakt de post maar plaatst niets
   python dagelijks.py --demo    gebruikt voorbeeld.json in plaats van Claude (alleen met --droog zinvol)"""
import json, os, sys
import genereer, post

MAP = os.path.dirname(os.path.abspath(__file__))


def main():
    droog, demo = "--droog" in sys.argv, "--demo" in sys.argv
    inst = post.INST
    eigen_muziek = os.path.join(MAP, "muziek") if inst["muziek"] == "eigen" else None
    p = genereer.maak_post(demo=demo, muziek_map=eigen_muziek)
    print("Gemaakt:", p["formaat"], "-", p["titel"], "->", p["map"])
    if droog:
        print("Droog: niets geplaatst."); return
    ig_id, token = post.env("IG_USER_ID"), post.env("IG_TOKEN")
    if p["formaat"] == "carrousel":
        urls = [post.upload(b, "image") for b in p["bestanden"]]
        media_id = post.post_carrousel(urls, p["caption"], ig_id, token)
    else:
        url = post.upload(p["bestanden"][0], "video")
        audio = None
        if inst["muziek"] == "instagram":
            audio = post.zoek_audio(ig_id, token, inst["audio_minimale_duur_sec"], inst["audio_zoekterm"], seed=p["datum"])
            print("Muziek:", (audio["display_artist"] + " - " + audio["title"]) if audio else "geen gevonden, Reel zonder muziek")
        media_id = post.post_reel(url, p["caption"], ig_id, token, audio_id=audio["audio_id"] if audio else None)
    genereer.schrijf_geschiedenis(p)
    print("Geplaatst, media-id:", media_id)


if __name__ == "__main__":
    main()
