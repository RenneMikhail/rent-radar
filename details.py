# Полные списки фото и описания для Pisos.com и Fotocasa (прямые запросы). Idealista/yaencontre собираются из вкладок (см. scan/details_*.js).
# Результат: details/<site>.json  {id: {"p":[url..], "d":"описание"}}
import json, os, re, sys, time, html, urllib.request
D = os.path.dirname(os.path.abspath(__file__))
BR = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36", "Accept-Language": "es-ES,es;q=0.9"}
def page(u):
    try: return urllib.request.urlopen(urllib.request.Request(u, headers=BR), timeout=25).read().decode("utf8", "ignore")
    except Exception: return None
def clean(t): return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", html.unescape(re.sub(r"<br\s*/?>", "\n", t)))).strip()
def pisos(u):
    h = page(u)
    if not h: return None
    ph = []
    for m in re.findall(r"fotos\.imghs\.net/fchm-wp/([^\"'\s\\]+)\.jpg", h):
        if m not in ph: ph.append(m)
    m = re.search(r'class="description__content">(.*?)</div>', h, re.S)
    d = clean(re.sub(r"<[^>]+>", "", m.group(1))) if m else ""
    return {"p": ["https://fotos.imghs.net/fchm-wp/%s.jpg" % x for x in ph[:40]], "d": d}
def fotocasa(u):
    h = page(u)
    if not h: return None
    ph = []
    i = h.find('multimedias":[')
    if i >= 0:
        try:
            arr, _ = json.JSONDecoder().raw_decode(h[i + 13:])
            for x in arr:
                if isinstance(x, dict) and x.get("type", "image") == "image" and x.get("url"):
                    mm = re.search(r"images/ads/([0-9a-f-]{36})", x["url"])
                    if mm and mm.group(1) not in ph: ph.append(mm.group(1))
        except Exception:
            seg = h[i:i + 30000]
            for mm in re.findall(r"images/ads/([0-9a-f-]{36})", seg):
                if mm not in ph: ph.append(mm)
    if not ph:
        for mm in re.findall(r"images/ads/([0-9a-f-]{36})", h):
            if mm not in ph: ph.append(mm)
    m = re.search(r'"description":"((?:[^"\\]|\\.)*)"', h)
    d = ""
    if m:
        try: d = json.loads('"' + m.group(1) + '"')
        except Exception: d = m.group(1)
    return {"p": ["https://static.fotocasa.es/images/ads/%s?rule=web_948x542_ar" % x for x in ph[:40]], "d": clean(d)}
if __name__ == "__main__":
    s = json.load(open(os.path.join(D, "state.json")))["listings"]
    for site, fn, key in (("pisos.com", pisos, r"-(\d{9,16})_"), ("fotocasa.es", fotocasa, r"/(\d+)/d$"), ("habitaclia.com", fotocasa, r"/([0-9a-f-]{36})/d$")):
        f = os.path.join(D, "details", site.split(".")[0] + ".json")
        db = json.load(open(f)) if os.path.exists(f) else {}
        n = 0
        for u, c in s.items():
            if site not in u or c.get("gone") or c.get("archived"): continue
            m = re.search(key, u)
            if not m: continue
            k = m.group(1)
            if k in db and db[k].get("p") and "--force" not in sys.argv: continue
            r = fn(u)
            if r: db[k] = r; n += 1; print(site, k, len(r["p"]), len(r["d"]), flush=True)
            time.sleep(0.6)
        json.dump(db, open(f, "w"), ensure_ascii=False)
        print("saved", site, n)
