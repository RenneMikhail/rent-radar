# Упаковка фото и карт в pub/p/<id>.json (data: URI), потому что страница-артефакт не грузит внешние картинки.
# Запуск: .venv/bin/python pack.py   (после monitor.py build, он пишет pub_src.json)
import json, os, io, base64, hashlib, math, time, urllib.request, urllib.parse, sys
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(D, "pub", "p"); os.makedirs(PUB, exist_ok=True)
CACHE = os.path.join(D, "cache"); os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "rent-personal-viewer/1.0"}
def mid(k):
    h = 2166136261
    for ch in k:
        h ^= ord(ch); h = (h * 16777619) & 0xFFFFFFFF
    n = h; s = ""
    while n: s = "0123456789abcdefghijklmnopqrstuvwxyz"[n % 36] + s; n //= 36
    return "m" + (s or "0")
def get(url, tries=2):
    f = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest())
    if os.path.exists(f): return open(f, "rb").read()
    for _ in range(tries):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()
            open(f, "wb").write(b); return b
        except Exception: time.sleep(0.5)
    return None
def photo(url):
    b = get(url)
    if not b: return None
    try:
        im = Image.open(io.BytesIO(b)).convert("RGB")
        im.thumbnail((600, 450))
        o = io.BytesIO(); im.save(o, "JPEG", quality=58, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(o.getvalue()).decode()
    except Exception: return None
def tile(z, x, y):
    b = get("https://tile.openstreetmap.org/%d/%d/%d.png" % (z, x, y))
    if not (os.path.exists(os.path.join(CACHE, hashlib.md5(("https://tile.openstreetmap.org/%d/%d/%d.png" % (z, x, y)).encode()).hexdigest())) and b): return None
    return Image.open(io.BytesIO(b)).convert("RGB")
def mapimg(g):
    lat, lon, lvl = g["lat"], g["lon"], g["lvl"]
    z = 16 if lvl in ("addr", "street") else (14 if lvl == "zone" else 13)
    n = 2 ** z; xf = (lon + 180) / 360 * n; lr = math.radians(lat)
    yf = (1 - math.log(math.tan(lr) + 1 / math.cos(lr)) / math.pi) / 2 * n
    W, H = 640, 300
    x0, y0 = int(xf), int(yf)
    canvas = Image.new("RGB", (3 * 256, 3 * 256), (230, 230, 230))
    for i in range(3):
        for j in range(3):
            t = tile(z, x0 - 1 + i, y0 - 1 + j)
            if t: canvas.paste(t, (i * 256, j * 256))
            time.sleep(0.05)
    px, py = (xf - (x0 - 1)) * 256, (yf - (y0 - 1)) * 256
    left, top = int(px - W / 2), int(py - H / 2)
    left = max(0, min(left, 768 - W)); top = max(0, min(top, 768 - H))
    im = canvas.crop((left, top, left + W, top + H)).convert("RGBA")
    cx, cy = px - left, py - top
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if lvl in ("addr", "street"):
        d.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=(220, 38, 38, 255), outline=(255, 255, 255, 255), width=4)
        d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(255, 255, 255, 255))
    else:
        r = 60 if lvl == "zone" else 80
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(220, 38, 38, 55), outline=(220, 38, 38, 255), width=3)
    d.rectangle((W - 118, H - 16, W, H), fill=(255, 255, 255, 200))
    d.text((W - 114, H - 14), "© OpenStreetMap", fill=(30, 30, 30, 255))
    im = Image.alpha_composite(im, ov).convert("RGB")
    o = io.BytesIO(); im.save(o, "JPEG", quality=70, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(o.getvalue()).decode()

import re
BR = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36", "Accept-Language": "es-ES,es;q=0.9"}
def discover(link):
    """Ищет фото на странице объявления (Pisos.com, Fotocasa) прямым запросом с компьютера."""
    try:
        h = urllib.request.urlopen(urllib.request.Request(link, headers=BR), timeout=25).read().decode("utf8", "ignore")
    except Exception: return []
    out = []
    if "pisos.com" in link:
        for m in re.findall(r"fotos\.imghs\.net/fchm-wp/([^\"'\s\\]+)\.jpg", h):
            if m not in out: out.append(m)
        return ["https://fotos.imghs.net/fchm-wp/%s.jpg" % x for x in out[:5]]
    if "fotocasa.es" in link:
        i = h.find('multimedias":['); seg = h[i:i + 6000] if i >= 0 else ""
        e = seg.find("]"); seg = seg[:e] if e > 0 else seg
        for m in re.findall(r"images/ads/([0-9a-f-]{36})", seg):
            if m not in out: out.append(m)
        return ["https://static.fotocasa.es/images/ads/%s?rule=web_948x542_ar" % x for x in out[:5]]
    return []
import re as _re
DET = {}
for _s in ("idealista", "pisos", "yae", "fotocasa", "habitaclia"):
    _f = os.path.join(D, "details", _s + ".json")
    if os.path.exists(_f): DET[_s] = json.load(open(_f))
def detail_for(link):
    if "idealista.com" in link:
        m = _re.search(r"/inmueble/(\d+)", link); x = DET.get("idealista", {}).get(m.group(1)) if m else None
        if x: x = dict(x, p=["https://img4.idealista.com/blur/WEB_DETAIL-M-L/0/id.pro.es.image.master/%s.jpg" % u for u in x["p"]])
        return x
    if "pisos.com" in link:
        m = _re.search(r"-(\d{9,16})_", link); return DET.get("pisos", {}).get(m.group(1)) if m else None
    if "yaencontre.com" in link:
        x = DET.get("yae", {}).get(link.rstrip("/").split("-")[-1])
        if x: x = dict(x, p=["https://media.yaencontre.com/img/photo/w630/%s.jpg" % u for u in x["p"]])
        return x
    if "fotocasa.es" in link:
        m = _re.search(r"/(\d+)/d$", link); return DET.get("fotocasa", {}).get(m.group(1)) if m else None
    if "habitaclia.com" in link:
        m = _re.search(r"/([0-9a-f-]{36})/d$", link); return DET.get("habitaclia", {}).get(m.group(1)) if m else None
    return None
MAXP = 20
src = json.load(open(os.path.join(D, "pub_src.json")))
keep = set(); done = 0
for c in src:
    pid = mid(c["link"]); keep.add(pid + ".json")
    f = os.path.join(PUB, pid + ".json")
    if os.path.exists(f) and "--force" not in sys.argv:
        try: old = json.load(open(f))
        except Exception: old = {"p": [1]}
        if old.get("p") or "--redo-empty" not in sys.argv: continue
    pk = {"p": [], "m": None, "d": ""}
    det = detail_for(c["link"])
    if det:
        pk["d"] = det.get("d", "")
        if det.get("p"): c["photos"] = det["p"]
    if not c["photos"]: c["photos"] = discover(c["link"])
    for u in c["photos"][:MAXP]:
        d = photo(u)
        if d: pk["p"].append(d)
    if c["geo"]:
        try: pk["m"] = mapimg(c["geo"])
        except Exception as e: print("map fail", e)
    json.dump(pk, open(f, "w"))
    done += 1; print(done, pid, len(pk["p"]), bool(pk["m"]), flush=True)
for fn in os.listdir(PUB):
    if fn not in keep: os.remove(os.path.join(PUB, fn))
idx = {}
for fn in os.listdir(PUB):
    try: idx[fn[:-5]] = len(json.load(open(os.path.join(PUB, fn))).get("p", []))
    except Exception: pass
json.dump(idx, open(os.path.join(D, "pub", "index.json"), "w"))
print("packed", done, "total", len(keep))
