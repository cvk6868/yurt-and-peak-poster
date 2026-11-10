"""Rendert infoposts (carrousel en Reel) uit foto's en tekst. Geen AI nodig."""
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

BASE = os.path.dirname(os.path.abspath(__file__))
FONT_B = os.path.join(BASE, "fonts", "DejaVuSans-Bold.ttf")
FONT_R = os.path.join(BASE, "fonts", "DejaVuSans.ttf")
GROEN = (47, 93, 80)
WIT = (255, 255, 255)
ACCENT = (255, 196, 87)


def font(pad, size):
    return ImageFont.truetype(pad, size)


def wrap(draw, tekst, fnt, max_w):
    regels, huidig = [], ""
    for woord in tekst.split():
        test = (huidig + " " + woord).strip()
        if draw.textlength(test, font=fnt) <= max_w:
            huidig = test
        else:
            if huidig:
                regels.append(huidig)
            huidig = woord
    if huidig:
        regels.append(huidig)
    return regels


def achtergrond(foto_pad, w, h):
    """Foto als achtergrond. Is de foto te klein om te vullen, dan staat hij
    ongerekt in het midden op een vervaagde versie van zichzelf."""
    im = ImageOps.exif_transpose(Image.open(foto_pad)).convert("RGB")
    schaal_vul = max(w / im.width, h / im.height)
    if schaal_vul <= 1.6:  # vullen mag, zonder te veel te vergroten
        im2 = im.resize((round(im.width * schaal_vul), round(im.height * schaal_vul)), Image.LANCZOS)
        x, y = (im2.width - w) // 2, (im2.height - h) // 2
        return im2.crop((x, y, x + w, y + h)), "vullend"
    bg = im.resize((round(im.width * schaal_vul), round(im.height * schaal_vul)), Image.LANCZOS)
    x, y = (bg.width - w) // 2, (bg.height - h) // 2
    bg = bg.crop((x, y, x + w, y + h)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (w, h), (0, 0, 0)), 0.25)
    sc = min(w / im.width, 1.6, 0.58 * h / im.height)
    fg = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    bg.paste(fg, ((w - fg.width) // 2, int(h * 0.09)))
    return bg, "gecentreerd"


def verloop(im, van_y, tot_y, sterkte=215):
    w, h = im.size
    lag = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lag)
    for y in range(van_y, tot_y):
        a = int(sterkte * (y - van_y) / max(1, (tot_y - van_y)))
        d.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    return Image.alpha_composite(im.convert("RGBA"), lag).convert("RGB")


def merk(draw, w, y, klein=False):
    f = font(FONT_B, 30 if klein else 36)
    tekst = "YURT AND PEAK"
    draw.text((62, y + 2), tekst, font=f, fill=(0, 0, 0))
    draw.text((60, y), tekst, font=f, fill=ACCENT)


def slide(foto_pad, kop, tekst, nummer, totaal, w=1080, h=1350, cover=False, cta=False):
    im, _ = achtergrond(foto_pad, w, h)
    im = verloop(im, int(h * 0.38), h, 235)
    # donkere rand bovenin, zodat het merk ook op lichte lucht leesbaar blijft
    top = Image.new("RGBA", (w, 200), (0, 0, 0, 0)); td = ImageDraw.Draw(top)
    for yy in range(200):
        td.line([(0, yy), (w, yy)], fill=(0, 0, 0, int(150 * (1 - yy / 200))))
    im = im.convert("RGBA"); im.alpha_composite(top, (0, 0)); im = im.convert("RGB")
    d = ImageDraw.Draw(im)
    marge = 60
    max_w = w - 2 * marge
    onder = h - 90
    # tekstblok van onderen opbouwen
    f_kop = font(FONT_B, 84 if cover else 62)
    f_txt = font(FONT_R, 44)
    kop_regels = wrap(d, kop, f_kop, max_w)
    txt_regels = wrap(d, tekst, f_txt, max_w) if tekst else []
    hoogte_kop = len(kop_regels) * int(f_kop.size * 1.18)
    hoogte_txt = len(txt_regels) * int(f_txt.size * 1.38)
    blok = hoogte_kop + (hoogte_txt + 30 if txt_regels else 0)
    y = onder - blok
    if not cover and not cta:
        badge = f"{nummer}/{totaal - 2}" if False else f"{nummer}"
        d.ellipse([marge, y - 110, marge + 80, y - 30], fill=ACCENT)
        bw = d.textlength(badge, font=font(FONT_B, 44))
        d.text((marge + 40 - bw / 2, y - 98), badge, font=font(FONT_B, 44), fill=(30, 30, 30))
    for r in kop_regels:
        d.text((marge, y), r, font=f_kop, fill=WIT)
        y += int(f_kop.size * 1.18)
    if txt_regels:
        y += 30
        for r in txt_regels:
            d.text((marge, y), r, font=f_txt, fill=(240, 240, 240))
            y += int(f_txt.size * 1.38)
    merk(d, w, 60)
    if cover:
        t = "Swipe  →"
        d.text((w - marge - d.textlength(t, font=font(FONT_B, 40)), h - 70), t, font=font(FONT_B, 40), fill=ACCENT)
    return im


def maak_carrousel(content, fotos, uitmap):
    """content: {'titel','slides':[{'kop','tekst','foto'}],'cta'}; fotos: id -> pad"""
    os.makedirs(uitmap, exist_ok=True)
    s = content["slides"]
    paden = []
    cover = slide(fotos[content["coverfoto"]], content["titel"], content.get("ondertitel", ""), 0, len(s) + 2, cover=True)
    p = os.path.join(uitmap, "slide_01.jpg"); cover.save(p, quality=93); paden.append(p)
    for n, sl in enumerate(s, 1):
        im = slide(fotos[sl["foto"]], sl["kop"], sl["tekst"], n, len(s) + 2)
        p = os.path.join(uitmap, f"slide_{n+1:02d}.jpg"); im.save(p, quality=93); paden.append(p)
    cta = slide(fotos[content["ctafoto"]], content.get("cta_kop", "Meer weten?"),
                content.get("cta_tekst", "Stuur ons een DM of mail naar info@yurtandpeak.com"), 0, len(s) + 2, cta=True)
    p = os.path.join(uitmap, f"slide_{len(s)+2:02d}.jpg"); cta.save(p, quality=93); paden.append(p)
    return paden


def kies_muziek(muziekmap, seed=None):
    import random
    if not muziekmap or not os.path.isdir(muziekmap):
        return None
    tracks = [os.path.join(muziekmap, f) for f in sorted(os.listdir(muziekmap)) if f.lower().endswith((".mp3", ".m4a", ".wav", ".aac"))]
    return random.Random(seed).choice(tracks) if tracks else None


def maak_reel(content, fotos, uitbestand, sec_per_slide=3.2, fade=0.5, muziek=None, volume=0.35):
    """Zelfde inhoud als video 1080x1920, langzame zoom en overgangen, zonder geluid."""
    tmp = uitbestand + "_tmp"
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    s = content["slides"]
    beelden = []
    beelden.append(slide(fotos[content["coverfoto"]], content["titel"], content.get("ondertitel", ""), 0, len(s) + 2, w=1080, h=1920, cover=True))
    for n, sl in enumerate(s, 1):
        beelden.append(slide(fotos[sl["foto"]], sl["kop"], sl["tekst"], n, len(s) + 2, w=1080, h=1920))
    beelden.append(slide(fotos[content["ctafoto"]], content.get("cta_kop", "Meer weten?"),
                         content.get("cta_tekst", "Stuur ons een DM of mail naar info@yurtandpeak.com"), 0, len(s) + 2, w=1080, h=1920, cta=True))
    paden = []
    for i, im in enumerate(beelden):
        p = os.path.join(tmp, f"s{i}.png"); im.save(p); paden.append(p)
    fps = 30
    dur = sec_per_slide + fade
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for p in paden:
        cmd += ["-framerate", str(fps), "-loop", "1", "-t", f"{dur}", "-i", p]
    totaal = sec_per_slide * len(paden) + fade
    if muziek:
        cmd += ["-stream_loop", "-1", "-i", muziek]
    filt = []
    for i in range(len(paden)):
        # lichte inzoom (1.00 -> 1.06) per beeld
        filt.append(f"[{i}:v]scale=w='trunc(1080*(1+0.06*t/{dur})/2)*2':h='trunc(1920*(1+0.06*t/{dur})/2)*2':eval=frame,crop=1080:1920,setsar=1,fps={fps}[v{i}]")
    laatste = "v0"
    t = sec_per_slide
    for i in range(1, len(paden)):
        nieuw = f"x{i}"
        filt.append(f"[{laatste}][v{i}]xfade=transition=fade:duration={fade}:offset={t:.2f}[{nieuw}]")
        laatste = nieuw
        t += sec_per_slide
    if muziek:
        filt.append(f"[{len(paden)}:a]atrim=0:{totaal:.2f},asetpts=PTS-STARTPTS,volume={volume},"
                    f"afade=t=in:st=0:d=1,afade=t=out:st={totaal-1.5:.2f}:d=1.5,aformat=sample_rates=44100:channel_layouts=stereo[aud]")
    cmd += ["-filter_complex", ";".join(filt), "-map", f"[{laatste}]"]
    if muziek:
        cmd += ["-map", "[aud]", "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-t", f"{totaal:.2f}",
            "-pix_fmt", "yuv420p", "-r", str(fps), "-movflags", "+faststart", uitbestand]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return uitbestand
