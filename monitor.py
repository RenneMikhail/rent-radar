#!/usr/bin/env python3
"""Rent monitor state tool.
  python3 monitor.py known            -> JSON {site: [refs]} for the browser scan scripts
  python3 monitor.py ingest new.jsonl -> merge newly found listings (one JSON per line)
  python3 monitor.py build            -> regenerate arenda_mobile.html (artifact) + PDF/HTML
  python3 monitor.py summary          -> short text: counts + new today
Listing JSON for ingest: {"site","ref","url","loc","addr","price","rooms","m2","lift","temp","defer","avail"}
"""
import json, os, re, sys, html, datetime, subprocess
from urllib.parse import quote
D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(D)                       # ~/Documents/AI/Claude/Projects/Rent
STATE = os.path.join(D, "state.json")
exec(open(os.path.join(D, "zone_info.py")).read())   # U, E, ZI
exec(open(os.path.join(D, "bcn_zones.py")).read())   # MUN, MUN_RULES, G_*
_ZB = None
def zb():
    global _ZB
    if _ZB is None:
        import rooms as _r; _ZB = _r
    return _ZB
def zinfo(z):
    if z in MUN: return MUN[z][:5]
    if z in ZI: return ZI[z]
    return zb().ZB[z]

SUBV = {"Burjassot","Paterna","Alboraya","Meliana/Foios/Museros","Moncada/Alfara/Benaguasil","Mislata/Manises/Quart","Aldaia/Torrent/Silla/Sollana","Benetússer/Alfafar/Catarroja","Pobla de Farnals/Puig/Puçol","Canet d'En Berenguer","Sagunto/Puerto de Sagunto"}
SUBC = {"Benicàssim Playa (Voramar/Torreón)","Benicàssim Heliópolis/Golf","Oropesa/Marina d'Or","Borriol","Almassora","Vila-real","Burriana Playa/Centro","Burriana/Moncofa","Vinaròs"}
FLOOD = {"Aldaia/Torrent/Silla/Sollana","Benetússer/Alfafar/Catarroja","Pobles del Sud (Valencia)"}
DRUG = {"Grau (Castelló)","Cabanyal","Orriols/Rascanya","Almassora","Russafa","El Carme","Beteró/Marítim"}
NOISE = {"Russafa","El Carme","Benimaclet","Cabanyal"}
INDUSTRY = {"Grau (Castelló)","Almassora","Vila-real","Sagunto/Puerto de Sagunto","Paterna","El Grau (Valencia)"}

# keyword -> zone (first match wins; text is lower-cased, accents kept)
RULES = [
 (r"almassora|almazora", "Almassora"), (r"vila-real|villarreal|vila real", "Vila-real"),
 (r"benic[aà]ssim|benicasim|voramar|heli[oó]polis|els terrers|беникас", None),   # resolved below
 (r"бурриан", "Burriana Playa/Centro"), (r"кастельон|кастельо", "Castelló"),
 (r"burriana|borriana", "Burriana Playa/Centro"), (r"borriol", "Borriol"),
 (r"oropesa|orpesa|marina d.or|morro de gos|torre la sal|alcossebre", "Oropesa/Marina d'Or"),
 (r"moncofa|moncófar|nules|chilches|almenara|vall d.u", "Burriana/Moncofa"), (r"vinar[oò]s|benicarl|peñ[ií]scola", "Vinaròs"),
 (r"el grao|el grau.*castell|grao de castell|grau de castell|castell.*grao", "Grau (Castelló)"),
 (r"ensanche|parque oeste|ribalta|parque sensal", "Castelló Ensanche/Parque Oeste"), (r"hospital", "Castelló Hospital"),
 (r"castell[oó]n|castelló|castello", "Castelló"),   # resolved below
 (r"alboraya|alboraia|patacona|port saplaya", "Alboraya"), (r"burjassot|burjasot", "Burjassot"), (r"paterna|pobla de vallbona", "Paterna"),
 (r"meliana|foios|museros|massamagrell", "Meliana/Foios/Museros"), (r"moncada|montcada|alfara|benaguasil", "Moncada/Alfara/Benaguasil"),
 (r"mislata|manises|quart de poblet|xirivella", "Mislata/Manises/Quart"),
 (r"aldaia|torrent|silla|sollana|picassent|alaqu", "Aldaia/Torrent/Silla/Sollana"),
 (r"benet[uú]sser|alfafar|catarroja|paiporta|massanassa|sed[aá]v|albal", "Benetússer/Alfafar/Catarroja"),
 (r"farnals|el puig|puig de|pu[cç]ol", "Pobla de Farnals/Puig/Puçol"), (r"canet d", "Canet d'En Berenguer"),
 (r"sagunt|port de sagunt|puerto de sagunt|puerto sagunto", "Sagunto/Puerto de Sagunto"),
 (r"pinedo|castellar|oliveral|la torre|forn d.alcedo|la punta|pobles del sud|quatre carreres", "Pobles del Sud (Valencia)"),
 (r"orriols|rascanya", "Orriols/Rascanya"), (r"benicalap|torrefiel|raiosa|rai[oó]sa", "Benicalap/Torrefiel/La Raiosa"),
 (r"russafa|ruzafa", "Russafa"), (r"carme|carmen|velluters", "El Carme"), (r"bot[aà]nic|petxina|pla del real", "Botànic/Petxina"),
 (r"cabanyal|canyamelar|malvarrosa|casitas rosas", "Cabanyal"), (r"benimaclet", "Benimaclet"), (r"corts|patraix|extramurs|jes[uú]s", "Corts/Patraix"),
 (r"nou moles|aragon|safranar", "Nou Moles"), (r"malilla|jaume roig|ciutat de les arts", "Jaume Roig/Malilla"),
 (r"tres forques|olivereta|la luz", "Tres Forques/Olivereta"), (r"el saler|perellonet|perell", "El Saler/Perellonet"),
 (r"morvedre|marxalenes", "Morvedre"), (r"benim[aà]met|pobles de l.oest", "Benimàmet/Pobles de l'Oest"),
 (r"el grau|el grao|marítim|maritim", "El Grau (Valencia)"), (r"valencia|val[eè]ncia|валенси", "Valencia общий"),
]
def zone_for(text):
    t = (text or "").lower().replace("_", " ")
    if not re.search(r"[a-zà-ú]08(0[0-4]\d)\b", t):
        for pat, z in MUN_RULES:
            if re.search(pat, t): return z
    z = zb().zone_bcn(t)
    if z and z != "BCN общий": return z
    z = zone_for_old(t)          # Кастельон и его пригороды (Валенсию не берём)
    if z: return z
    return None
def zone_for_old(text):
    t = (text or "").lower()
    for pat, z in RULES:
        if re.search(pat, t):
            if z is None:
                return "Benicàssim Heliópolis/Golf" if re.search(r"heli[oó]polis|curva|golf|palmeral|ferrandis|apòstol|apostol", t) else "Benicàssim Playa (Voramar/Torreón)"
            if z == "Castelló":
                if re.search(r"centro|casco|historic", t): return "Castelló Centro/Casco"
                if re.search(r"\bsur\b", t): return "Castelló Sur"
                if re.search(r"\beste\b|\bnorte\b", t): return "Castelló Este/Norte"
                return "Castelló общий"
            return z
    return None

def group_for(z):
    if z in MUN: return MUN[z][5]
    if z.startswith("BCN "): return G_BCN
    if z in SUBV: return "Пригород Валенсии"
    if z in SUBC: return "Пригород Кастельона"
    if z.startswith("Castelló") or z.startswith("Grau"): return "Кастельон"
    return "Валенсия"

def flags_for(z):
    f = []
    if z in FLOOD: f.append("зона затопления DANA")
    if z in DRUG: f.append("наркоторговля в районе (по СМИ)")
    if z in NOISE: f.append("шум")
    if z in INDUSTRY: f.append("промзона рядом")
    return f

def link_for(site, ref, url):
    return url

def load(): return json.load(open(STATE))
def save(s): json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=0)
def now(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def key_of(site, ref):
    ref = str(ref)
    if site == "Pisos.com":
        m = re.search(r"-(\d{9,16})_", ref); return m.group(1) if m else ref
    if site == "yaencontre": return ref.split("-")[-1]
    return ref

def cmd_known(site=None):
    s = load(); by = {}
    for c in s["listings"].values():
        by.setdefault(c["site"], set()).add(key_of(c["site"], c["ref"]))
    for st, keys in s.get("rejected", {}).items():
        by.setdefault(st, set()).update(keys)
    by = {k: sorted(v) for k, v in by.items()}
    print(json.dumps(by.get(site, []) if site else by, ensure_ascii=False))

def cmd_scan(site):
    name = {"idealista":"Idealista","pisos":"Pisos.com","yaencontre":"yaencontre","milanuncios":"Milanuncios","fotocasa":"Fotocasa","habitaclia":"Habitaclia","habitaclia_all":"Habitaclia","fotocasa_all":"Fotocasa","casas_idealista":"Idealista","casas_pisos":"Pisos.com","casas_yae":"yaencontre","studios_idealista":"Idealista","studios_pisos":"Pisos.com"}[site]
    s = load(); keys = set()
    for c in s["listings"].values():
        if c["site"] == name: keys.add(key_of(name, c["ref"]))
    keys.update(s.get("rejected", {}).get(name, []))
    js = open(os.path.join(D, "scan", site + ".js")).read().replace("__KNOWN__", json.dumps(sorted(keys)))
    print(js)

def cmd_reject(site, path):
    s = load(); rj = s.setdefault("rejected", {}).setdefault(site, [])
    for line in open(path):
        k = line.strip()
        if k and k not in rj: rj.append(k)
    save(s); print("rejected", len(rj))

FAR = re.compile(r"finca|chalet|casa adosada|casa pareada|masía|masia|casa rural", re.I)
def url_for(site, ref, h=""):
    if site == "Idealista": return "https://www.idealista.com/inmueble/%s/" % ref
    if site == "Pisos.com": return "https://www.pisos.com/alquilar/%s/" % ref
    if site == "yaencontre": return "https://www.yaencontre.com/alquiler/piso/%s" % ref
    return h

def parse_line(line):
    line = line.strip()
    if not line: return None
    if line.startswith("{"): return json.loads(line)
    f = line.split("¦")            # site¦ref¦addr¦price¦rooms¦m2¦lift¦temp¦avail¦url(optional)
    f += [""] * (10 - len(f))
    return dict(site=f[0], ref=f[1], addr=f[2], loc=f[2] + " " + f[1], price=f[3], rooms=f[4], m2=f[5], lift=f[6] or "?", temp=(f[7] == "1"), avail=f[8], url=f[9] or url_for(f[0], f[1]))

DEFER_RE = re.compile(r"((desde|a partir|libre|disponible\w*|entrada|entrar a vivir|доступн\w*|\bс|visitas)(?:\W+\w+){0,4}?\W+(diciembre|enero|febrero|декабр|январ|феврал))|((diciembre|enero|febrero|декабр|январ|феврал)\s+(de\s+)?20\d\d)|(начало|с начала)\s+(декабр|январ)", re.I)

def cmd_ingest(path, baseline=False, kind=None):
    s = load(); added = []; skipped = []
    today = "2026-11-15" if baseline else datetime.date.today().isoformat()
    for line in open(path):
        n = parse_line(line)
        if not n: continue
        url = n.get("url") or url_for(n["site"], n["ref"])
        if url in s["listings"]: continue
        key = key_of(n["site"], n["ref"])
        zk = n.get("zone") or zone_for(n.get("loc","") + " " + n.get("addr",""))
        txt = n.get("loc","") + " " + n.get("addr","")
        if (not zk) or (FAR.search(txt) and kind != "house"):
            s.setdefault("rejected", {}).setdefault(n["site"], [])
            if key not in s["rejected"][n["site"]]: s["rejected"][n["site"]].append(key)
            skipped.append((n["site"], key, txt[:50])); continue
        if kind == "house" and not (group_for(zk) in (G_BCN, G_BAIX, G_MAR, G_ST, G_GAR, G_TAR) or zk in ("Sant Cugat del Vallès", "Cerdanyola/Ripollet/Montcada", "Rubí")):
            skipped.append((n["site"], key, "дом: слишком далеко " + zk)); continue
        g = zinfo(zk)
        if g[0] <= 2:
            s.setdefault("rejected", {}).setdefault(n["site"], [])
            if key not in s["rejected"][n["site"]]: s["rejected"][n["site"]].append(key)
            skipped.append((n["site"], key, "плохой район " + zk)); continue
        addr = n.get("addr") or n.get("loc") or ""
        addr = re.sub(r"^\s*(Квартира|Студио|Пентхаус|Дуплекс|Дом[^в]*) в\s*", "", addr).strip()
        city = "Barcelona"
        try: m2 = int(float(str(n["m2"]).replace(".", ""))) if n.get("m2") not in (None, "") else None
        except Exception: m2 = None
        if m2 and (m2 > 250 or m2 < 10): m2 = None
        c = dict(site=n["site"], also="", group=group_for(zk), zone=zk, addr=addr, price=int(n["price"]), rooms=str(n.get("rooms","?")), m2=m2, lift=n.get("lift","?"),
                 temp=bool(n.get("temp")), link=url, grade=g[0], note=g[1], flood=(zk in FLOOD), ref=str(n["ref"]), extra=n.get("extra",""), transport=g[2], evidence=g[3], level=g[4],
                 flags=flags_for(zk), kind=(kind or "apt"), maps="https://www.google.com/maps/search/?api=1&query=" + quote(addr + ", " + city),
                 first_seen=today, seen_ts=now(), deferred=bool(n.get("defer")), avail_note=n.get("avail_note", ""), gone=False)
        _av = n.get("avail") or ""
        _pm = re.search(r"\s*\[P:(.)\]", _av)
        if _pm:
            c["park"] = {"I": "incl", "N": "no", "Y": "yes"}.get(_pm.group(1), "?"); _av = _av.replace(_pm.group(0), "").strip()
        c["furn"] = n.get("furn") or ("yes" if n["site"] in ("Idealista", "yaencontre", "Pisos.com") else ("yes" if "amueblado" in url else "?"))
        if n.get("park"): c["park"] = n["park"]
        _fm = re.search(r"\s*\[F:(.)\]", _av)
        if _fm:
            c["furn"] = {"Y": "yes", "N": "no"}.get(_fm.group(1), "?"); _av = _av.replace(_fm.group(0), "").strip()
        c["phone"] = ""; c["parkn"] = ""
        if _av and not c["avail_note"]: c["avail_note"] = _av
        if c["avail_note"] and DEFER_RE.search(c["avail_note"]): c["deferred"] = True
        dup = next((x for x in s["listings"].values() if x["price"]==c["price"] and x["m2"] and x["m2"]==c["m2"] and x["zone"]==zk and str(x["rooms"])==c["rooms"]), None)
        if dup:
            if c["site"] != dup["site"] and c["site"] not in dup.get("also",""): dup["also"] = (dup.get("also","") + ", " + c["site"]).lstrip(", ")
            continue
        s["listings"][url] = c; added.append(c)
    s["last_run"] = now(); save(s)
    print("added", len(added), "| skipped(out of scope)", len(skipped))
    for a in added: print(" +", a["site"], "|", a["zone"], "|", a["price"], "€", a["rooms"], "комн.", a["m2"], "м2", "| defer" if a["deferred"] else "", ("| " + a["avail_note"][:60]) if a["avail_note"] else "", "|", a["link"])

def mark_gone(path):
    """path: file with one URL per line that no longer exist"""
    s = load()
    for line in open(path):
        u = line.strip()
        if u in s["listings"]: s["listings"][u]["gone"] = True
    save(s)

def card_score(c):
    r = str(c["rooms"]); rn = int(r) if r.isdigit() and int(r) <= 6 else (0 if r.startswith("студ") else 1)
    sc = c["grade"]*10 + min(c["m2"] or 0, 95)/6 + (3 if c["lift"]=="да" else 0) - (2 if c["temp"] else 0) + (6 if rn>=2 else 0) - (10 if c["m2"] and c["m2"]<30 else 0) - (30 if c["flood"] else 0)
    return sc

def attach_extras(cards):
    """Фото (photos/*.json) и координаты (geo.json) к карточкам."""
    import re as _re
    ph = {}
    for fn in ("idealista", "pisos", "yae", "fotocasa"):
        pth = os.path.join(D, "photos", fn + ".json")
        if os.path.exists(pth): ph[fn] = json.load(open(pth))
    src = []
    def _mid(k):
        h = 2166136261
        for ch in k: h ^= ord(ch); h = (h * 16777619) & 0xFFFFFFFF
        n = h; s = ""
        while n: s = "0123456789abcdefghijklmnopqrstuvwxyz"[n % 36] + s; n //= 36
        return "m" + (s or "0")
    ip = os.path.join(D, "pub", "index.json"); pidx = json.load(open(ip)) if os.path.exists(ip) else {}
    gp = os.path.join(D, "geo.json"); geo = json.load(open(gp)) if os.path.exists(gp) else {}
    for c in cards:
        l = c["link"]; urls = []
        if "idealista.com" in l:
            m = _re.search(r"/inmueble/(\d+)", l)
            for x in (ph.get("idealista", {}).get(m.group(1), "") if m else "").split(","):
                if x: urls.append("https://img4.idealista.com/blur/WEB_DETAIL-M-L/0/id.pro.es.image.master/%s.jpg" % x)
        elif "pisos.com" in l:
            m = _re.search(r"-(\d{9,16})_", l)
            for x in (ph.get("pisos", {}).get(m.group(1), []) if m else []): urls.append("https://fotos.imghs.net/fchm-wp/%s.jpg" % x)
        elif "yaencontre.com" in l:
            m = _re.search(r"-(\d+)$", l)
            for x in (ph.get("yae", {}).get(m.group(1), []) if m else []): urls.append("https://media.yaencontre.com/img/photo/w630/%s.jpg" % x)
        elif "fotocasa.es" in l:
            m = _re.search(r"/(\d+)/d$", l)
            for x in (ph.get("fotocasa", {}).get(m.group(1), []) if m else []): urls.append("https://static.fotocasa.es/images/ads/%s?rule=web_948x542_ar" % x)
        g = geo.get(l)
        c["geo"] = g if g and g.get("lat") else None
        src.append({"link": l, "photos": urls, "geo": c["geo"]})
        c["np"] = pidx.get(_mid(l), min(len(urls), 20)); c.pop("photos", None)
    json.dump(src, open(os.path.join(D, "pub_src.json"), "w"), ensure_ascii=False)

def cmd_build():
    s = load()
    cards = [c for c in s["listings"].values() if not c.get("gone") and not c.get("archived") and not c.get("excl")]
    for c in cards: c["score"] = card_score(c)
    attach_extras(cards)
    today = datetime.date.today().isoformat()
    tpl = open(os.path.join(D, "page_template.html")).read()
    try:
        import rooms as _rooms
        rcards = _rooms.cards()
    except Exception as ex:
        print("rooms skipped:", ex); rcards = []
    data = json.dumps(cards + rcards, ensure_ascii=False).replace("</", "<\\/")
    def _st(c):
        return "снято" if c.get("gone") else ("отфильтровано: " + str(c.get("excl"))[:60] if c.get("excl") else ("архив" if c.get("archived") else ""))
    lookup = [{"s": c.get("site"), "a": c.get("addr"), "z": c.get("zone"), "p": c.get("price"), "r": c.get("rooms"), "m": c.get("m2"), "t": c.get("phone") or "", "l": c.get("link"), "x": _st(c)} for c in s["listings"].values()]
    lookup = json.dumps(lookup, ensure_ascii=False).replace("</", "<\\/")
    msg = open(os.path.join(D, "contact.txt"), encoding="utf8").read().strip()
    page = tpl.replace("__MSG__", json.dumps(msg, ensure_ascii=False)).replace("__LOOKUP__", lookup).replace("__DATA__", data).replace("__TODAY__", today).replace("__UPDATED__", s.get("last_run", now()))
    open(os.path.join(OUT, "arenda_mobile.html"), "w").write(page)
    # ---- PDF / HTML ----
    def tbl(rows):
        h = "<table><tr><th>#</th><th>Сайт</th><th>Район / адрес</th><th>Цена</th><th>Комн.</th><th>м²</th><th>Срок</th><th>Район</th><th>Ссылка</th></tr>"
        for i, r in enumerate(rows, 1):
            col = {5:"#1b7a3d",4:"#4c9a2a",3:"#c28b00",2:"#c0392b",1:"#c0392b"}[r["grade"]]
            fl = "".join("<br><b style='color:#c0392b'>%s</b>" % html.escape(x) for x in r["flags"])
            av = ("<br><i>%s</i>" % html.escape(r["avail_note"])) if r.get("avail_note") else ""
            h += ("<tr><td>%d</td><td>%s</td><td><b>%s</b><br>%s%s</td><td>%s €</td><td>%s</td><td>%s</td><td>%s</td><td style='color:%s'><b>%s/5</b>%s</td><td style='word-break:break-all;width:150px'><a href='%s'>открыть</a><br><small>%s</small></td></tr>" % (
                i, r["site"], html.escape(r["zone"]), html.escape(r["addr"]), av, r["price"], r["rooms"], r["m2"] or "?", "врем." if r["temp"] else "долг.", col, r["grade"], fl, r["link"], r["link"].replace("https://","")))
        return h + "</table>"
    main = sorted([c for c in cards if not c["deferred"] and c.get("kind") != "house"], key=lambda c: -c["score"])
    later = sorted([c for c in cards if c["deferred"]], key=lambda c: -c["score"])
    new = [c for c in main if c["first_seen"] == today and c["first_seen"] != "2026-11-15"]
    body = "<h2>Новые за сегодня (%d)</h2>%s" % (len(new), tbl(new) if new else "<p>Пока нет.</p>")
    for title, g in [(g, g) for g in (G_BCN, G_BAIX, G_MAR, G_ST, G_VAL, G_GAR, G_TAR)]:
        rows = [c for c in main if c["group"] == g]
        body += "<h2>%s: %d</h2>%s" % (title, len(rows), tbl(rows))
    body += "<h2>С декабря и позже (отдельная папка): %d</h2>%s" % (len(later), tbl(later) if later else "<p>Нет.</p>")
    def rtbl(rows):
        h = "<table><tr><th>#</th><th>Сайт</th><th>Город / район</th><th>Цена</th><th>Санузел</th><th>Срок</th><th>Район</th><th>Ссылка</th></tr>"
        for i, r in enumerate(rows, 1):
            col = {5:"#1b7a3d",4:"#4c9a2a",3:"#c28b00",2:"#c0392b",1:"#c0392b"}[r["grade"]]
            bt = {"private":"свой","shared":"общий"}.get(r["bath"], "не указан")
            h += ("<tr><td>%d</td><td>%s</td><td><b>%s, %s</b><br>%s%s</td><td>%s €</td><td>%s</td><td>%s</td><td style='color:%s'><b>%s/5</b></td><td style='word-break:break-all;width:150px'><a href='%s'>открыть</a></td></tr>" % (
                i, r["site"], html.escape(r["group"]), html.escape(r["zone"].replace("BCN ", "")), html.escape(r["addr"]), ("<br><i>%s</i>" % html.escape(r["avail_note"])) if r.get("avail_note") else "", r["price"], bt,
                ("%s мес." % r["minstay"]) if r.get("minstay") != "" else "?", col, r["grade"], r["link"]))
        return h + "</table>"
    for gname in ("Барселона", "Валенсия", "Кастельон"):
        for lab, flt in (("с санузлом", lambda r: r["bath"] == "private"), ("без санузла или не указан", lambda r: r["bath"] != "private")):
            rows = sorted([r for r in rcards if r["group"] == gname and flt(r)], key=lambda r: -r["score"])
            body += "<h2>Комнаты, %s, %s: %d</h2>%s" % (gname, lab, len(rows), rtbl(rows) if rows else "<p>Нет.</p>")
    zones = "<table><tr><th>Район</th><th>Оценка</th><th>Что известно</th><th>Транспорт</th></tr>" + "".join(
        "<tr><td><b>%s</b></td><td>%s/5</td><td>%s</td><td>%s</td></tr>" % (html.escape(k), v[0], html.escape(v[1]), html.escape(v[2])) for k, v in sorted([(k, v[:5]) for k, v in MUN.items()] + list(_rooms.ZB.items()), key=lambda kv: kv[1][0])) + "</table>"
    css = "body{font-family:-apple-system,Helvetica,Arial;font-size:9px;margin:16px}h1{font-size:18px}h2{font-size:13px;margin-top:18px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:3px;vertical-align:top}th{background:#eee}tr{page-break-inside:avoid}"
    page2 = ("<html><head><meta charset='utf-8'><style>" + css + "</style></head><body><h1>Аренда: Барселона и окрестности до Таррагоны. Обновлено " + str(s.get("last_run", now())) + "</h1>"
             "<p>Квартиры 500-1000 €/мес, с мебелью; комнаты (Барселона, Валенсия, Кастельон) до 500 €. Комнат: " + str(len(rcards)) + ". Квартир: " + str(len(cards)) + " объявлений: " + str(len(main)) + " в основном списке и " + str(len(later)) + " в разделе «с декабря и позже».</p>"
             + body + "<h2>Районы</h2>" + zones + "</body></html>")
    hp = os.path.join(OUT, "arenda_polnyj_poisk.html"); open(hp, "w").write(page2)
    ch = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(ch):
        subprocess.run([ch, "--headless=new", "--disable-gpu", "--no-sandbox", "--print-to-pdf=" + os.path.join(OUT, "arenda_polnyj_poisk.pdf"), "--no-pdf-header-footer", "file://" + hp], capture_output=True)
    print("built:", len(cards), "cards;", len(main), "main;", len(later), "later;", len(new), "new today")

def cmd_summary():
    s = load(); today = datetime.date.today().isoformat()
    cards = [c for c in s["listings"].values() if not c.get("gone") and not c.get("archived") and not c.get("excl")]
    new = [c for c in cards if c["first_seen"] == today and c["first_seen"] != "2026-11-15"]
    print("total", len(cards), "| deferred", sum(1 for c in cards if c["deferred"]), "| new today", len(new), "| last_run", s.get("last_run"))
    for c in new: print(" +", c["site"], c["zone"], c["price"], "€", c["rooms"], "комн.", c["m2"], "м2", c["link"])

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "known": cmd_known(a[1] if len(a)>1 else None)
    elif a[0] == "scan": cmd_scan(a[1])
    elif a[0] == "reject": cmd_reject(a[1], a[2])
    elif a[0] == "ingest": cmd_ingest(a[1], baseline=("--baseline" in a), kind=("house" if "--casa" in a else None))
    elif a[0] == "gone": mark_gone(a[1])
    elif a[0] == "urls":
        for u,c in load()["listings"].items():
            if not c.get("gone") and a[1] in u: print(u)
    elif a[0] == "build": cmd_build()
    elif a[0] == "summary": cmd_summary()
