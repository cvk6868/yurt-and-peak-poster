"""Maakt een infopost: Claude kiest thema en foto's, render.py maakt de carrousel of Reel.
Gebruik:  python genereer.py            (vraagt Claude, vereist ANTHROPIC_API_KEY)
          python genereer.py --demo     (gebruikt voorbeeld.json, geen API nodig)
          python genereer.py --prompt   (toont alleen de opdracht aan Claude)"""
import json, os, re, sys, urllib.request, urllib.error, datetime
import render

MAP = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")


def laad():
    foto_lijst = json.load(open(os.path.join(MAP, "photos.json"), encoding="utf-8"))
    hist_pad = os.path.join(MAP, "history.json")
    hist = json.load(open(hist_pad)) if os.path.exists(hist_pad) else []
    feiten = open(os.path.join(MAP, "feiten.md"), encoding="utf-8").read()
    return foto_lijst, hist, feiten


def kies_formaat(hist):
    return "reel" if (hist[-1]["formaat"] == "carrousel" if hist else False) else "carrousel"


def bouw_prompt(foto_lijst, hist, feiten, formaat):
    foto_regels = []
    for p in foto_lijst:
        if p["mensen_zichtbaar"]:
            continue  # nooit foto's met herkenbare mensen gebruiken zonder toestemming
        plaats = p["plaats"] if p["plaats_bevestigd"] else "onbekend (noem geen plaatsnaam)"
        foto_regels.append(f'- {p["id"]}: {p["beschrijving"]} | plaats: {plaats}')
    recent = "; ".join(h["titel"] for h in hist[-20:]) or "geen"
    n = "5 tot 6" if formaat == "carrousel" else "4 tot 5"
    return f"""Je bent de social-media-redacteur van Yurt and Peak, een Nederlands reisbedrijf met rondreizen door Kirgizië.
Doelgroep: 20 tot 25 jaar, Nederland. Toon: luchtig en behulpzaam, 'je' en 'jij', nooit schreeuwerig.

TAAK: maak één korte informatiepost ("wat je moet weten") in het formaat {formaat}, met {n} slides.

REGELS:
- Gebruik UITSLUITEND feiten uit de lijst hieronder. Verzin niets en gebruik geen kennis van buiten de lijst. Is er te weinig materiaal voor een nieuw thema, geef dan {{"geen_thema": true}}.
- Noem geen plaatsnamen die niet bij de gekozen foto staan als bevestigd.
- Kies per slide een andere foto uit de fotolijst; de foto moet passen bij de tekst.
- Kop maximaal 5 woorden. Tekst maximaal 24 woorden. Titel maximaal 12 woorden.
- Herhaal geen thema uit de recente lijst.
- Eindig de caption met een uitnodiging om een DM te sturen.

FEITEN:
{feiten}

FOTO'S:
{chr(10).join(foto_regels)}

RECENTE THEMA'S: {recent}

Antwoord ALLEEN met JSON in dit formaat:
{{"titel":"...","ondertitel":"...","coverfoto":"pXX","slides":[{{"kop":"...","tekst":"...","foto":"pXX","feit":"het feit uit de lijst waarop dit gebaseerd is"}}],"ctafoto":"pXX","caption":"...","hashtags":"#yurtandpeak #kirgizie ..."}}"""


def vraag_claude(prompt):
    sleutel = os.environ.get("ANTHROPIC_API_KEY")
    if not sleutel:
        sys.exit("Zet eerst ANTHROPIC_API_KEY.")
    body = json.dumps({"model": MODEL, "max_tokens": 6000, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": sleutel, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            antwoord = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Anthropic-fout {e.code}: {e.read().decode(errors='replace')[:500]}")
    blokken = [b.get("text", "") for b in antwoord.get("content", []) if b.get("type") == "text"]
    tekst = "\n".join(blokken)
    if not tekst.strip():
        sys.exit("Geen tekst in antwoord van Claude. Antwoord (ingekort): " + json.dumps(antwoord)[:600])
    m = re.search(r"\{.*\}", tekst, re.S)
    if not m:
        raise ValueError("Geen JSON in antwoord: " + tekst[:200])
    return json.loads(m.group(0))


def controleer(c, foto_ids, formaat):
    fouten = []
    if c.get("geen_thema"):
        return ["Claude heeft geen nieuw thema meer: vul feiten.md aan."]
    for k in ("titel", "coverfoto", "slides", "ctafoto", "caption", "hashtags"):
        if not c.get(k):
            fouten.append(f"ontbreekt: {k}")
    if fouten:
        return fouten
    gebruikt = [c["coverfoto"], c["ctafoto"]] + [s.get("foto") for s in c["slides"]]
    for f in gebruikt:
        if f not in foto_ids:
            fouten.append(f"onbekende of niet toegestane foto: {f}")
    if len(set(s.get("foto") for s in c["slides"])) < len(c["slides"]):
        fouten.append("dezelfde foto meer dan eens in de slides")
    for s in c["slides"]:
        if len(s.get("kop", "").split()) > 6:
            fouten.append(f"kop te lang: {s['kop']}")
        if len(s.get("tekst", "").split()) > 28:
            fouten.append(f"tekst te lang bij: {s['kop']}")
        if not s.get("feit"):
            fouten.append(f"geen feit genoemd bij: {s['kop']}")
    return fouten


def maak_post(demo=False, muziek_map=None, nu=None):
    """Maakt de post en geeft een dict terug. Schrijft de geschiedenis NIET weg; dat doet de aanroeper na het posten."""
    foto_lijst, hist, feiten = laad()
    formaat = kies_formaat(hist)
    if demo:
        c = json.load(open(os.path.join(MAP, "voorbeeld.json"), encoding="utf-8"))
        for s in c["slides"]:
            s.setdefault("feit", "voorbeeld")
    else:
        c = vraag_claude(bouw_prompt(foto_lijst, hist, feiten, formaat))
    toegestaan = {p["id"] for p in foto_lijst if not p["mensen_zichtbaar"]}
    fouten = controleer(c, toegestaan, formaat)
    if fouten:
        raise SystemExit("Niet gerenderd:\n- " + "\n- ".join(fouten))
    fotos = {p["id"]: os.path.join(MAP, p["bestand"]) for p in foto_lijst}
    dag = nu or datetime.date.today().isoformat()
    uit = os.path.join(MAP, "uit", f"{dag}_{formaat}")
    os.makedirs(uit, exist_ok=True)
    if formaat == "carrousel":
        bestanden = render.maak_carrousel(c, fotos, uit)
    else:
        muziek = render.kies_muziek(muziek_map, seed=dag) if muziek_map else None
        bestanden = [render.maak_reel(c, fotos, os.path.join(uit, "reel.mp4"), muziek=muziek)]
    caption = c["caption"] + "\n\n" + c["hashtags"]
    open(os.path.join(uit, "caption.txt"), "w", encoding="utf-8").write(caption + "\n")
    open(os.path.join(uit, "controle.txt"), "w", encoding="utf-8").write(
        "Feiten waarop deze post is gebaseerd:\n" + "\n".join(f"- {s['kop']}: {s['feit']}" for s in c["slides"]) + "\n")
    return {"formaat": formaat, "bestanden": bestanden, "caption": caption, "titel": c["titel"], "map": uit, "datum": dag}


def schrijf_geschiedenis(post):
    pad = os.path.join(MAP, "history.json")
    hist = json.load(open(pad)) if os.path.exists(pad) else []
    hist.append({"datum": post["datum"], "titel": post["titel"], "formaat": post["formaat"]})
    json.dump(hist, open(pad, "w"), indent=1, ensure_ascii=False)


def main():
    foto_lijst, hist, feiten = laad()
    if "--prompt" in sys.argv:
        print(bouw_prompt(foto_lijst, hist, feiten, kies_formaat(hist))); return
    demo = "--demo" in sys.argv
    post = maak_post(demo=demo, muziek_map=os.path.join(MAP, "muziek"))
    if not demo:
        schrijf_geschiedenis(post)
    print("Klaar:", post["map"])


if __name__ == "__main__":
    main()
