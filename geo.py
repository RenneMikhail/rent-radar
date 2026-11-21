# Геокодер для карточек: python3 geo.py  (кэш geo.json, Nominatim, 1 запрос/сек)
import json, re, time, urllib.request, urllib.parse, os, sys
D = os.path.dirname(os.path.abspath(__file__))
GP = os.path.join(D, "geo.json")
geo = json.load(open(GP)) if os.path.exists(GP) else {}
s = json.load(open(os.path.join(D, "state.json")))
cards = [v for v in s["listings"].values() if not v.get("archived") and not v.get("gone")]
CITY = {"Salou/Vila-seca": "Salou", "Cambrils": "Cambrils", "Altafulla/Torredembarra": "Torredembarra", "Tarragona (центр/Part Alta)": "Tarragona",
        "El Masnou/Premià de Mar/Vilassar": "El Masnou", "Vilanova i la Geltrú": "Vilanova i la Geltrú", "Calafell/Cunit/Segur": "Calafell",
        "Sant Feliu/Molins de Rei": "Sant Feliu de Llobregat", "L'Hospitalet (Santa Eulàlia/Bellvitge)": "L'Hospitalet de Llobregat"}
def city_of(c):
    z = c["zone"]
    if z.startswith("BCN"): return "Barcelona"
    if z.startswith("Castelló") or z.startswith("Grau (Castelló)"): return "Castelló de la Plana"
    if z.startswith("Benicàssim"): return "Benicàssim"
    if c.get("group") == "Валенсия": return "València"
    if z.startswith("Burriana"): return "Burriana"
    return CITY.get(z, z.split("/")[0].split(" (")[0])
def clean(a):
    a = re.sub(r"^(Piso|Estudio|Ático|Apartamento|Квартира|Студия|Апартаменты|Пентхаус|Alquiler de temporada)[^,]*? (en|на|по адресу|в районе|в) ", "", a)
    a = re.sub(r"^(Piso|Estudio|Ático|Apartamento) en ", "", a)
    a = re.sub(r"\d+ / \d+", "", a)
    return a.strip(" ,")
def q(text):
    u = "https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=es&q=" + urllib.parse.quote(text)
    r = urllib.request.Request(u, headers={"User-Agent": "rent-map-personal/1.0"})
    try:
        j = json.load(urllib.request.urlopen(r, timeout=20))
    except Exception as e:
        return None
    time.sleep(1.1)
    return (float(j[0]["lat"]), float(j[0]["lon"]), j[0].get("type", "")) if j else None
def ok(c, p):
    lat, lon = p[0], p[1]
    if c.get('group') in ('Валенсия','Пригород Валенсии'): return 39.3 < lat < 39.8 and -0.7 < lon < -0.15
    if c.get('group') in ('Кастельон','Пригород Кастельона'): return 39.85 < lat < 40.6 and -0.6 < lon < 0.3
    if not (40.4 < lat < 42.2 and 0.0 < lon < 3.2): return False
    if c["zone"].startswith("BCN") and not (41.31 < lat < 41.47 and 2.05 < lon < 2.23): return False
    return True
n = 0
for c in cards:
    k = c["link"]
    if k in geo: continue
    a = clean(c["addr"]); city = city_of(c)
    tries = []
    if re.search(r"[A-Za-zÀ-ÿ]", a) and not re.search(r"[А-Яа-я]", a): tries.append((a + ", " + city, "addr"))
    parts = [x.strip() for x in a.split(",") if x.strip()]
    if len(parts) >= 2 and not re.search(r"[А-Яа-я]", a): tries.append((parts[0] + ", " + city, "street"))
    zn = c["zone"].replace("BCN ", "").split("/")[0].split(" (")[0]
    tries.append((zn + ", " + city, "zone"))
    tries.append((city + (", Castellón, España" if c.get("group") in ("Кастельон","Пригород Кастельона") else ", Valencia, España" if c.get("group") in ("Валенсия","Пригород Валенсии") else ", Catalunya"), "city"))
    res = None
    for t, lvl in tries:
        p = q(t)
        if p and ok(c, p):
            res = {"lat": round(p[0], 5), "lon": round(p[1], 5), "lvl": lvl}; break
    geo[k] = res or {"lat": None, "lon": None, "lvl": "none"}
    n += 1
    print(n, geo[k]["lvl"], c["addr"][:50], flush=True)
    json.dump(geo, open(GP, "w"), ensure_ascii=False)
print("done", len(geo))
