#!/usr/bin/env python3
"""Rooms module for the rent monitor (Barcelona, Valencia, Castellon; price <= 500, min stay <= 1 month).
  python3 rooms.py scan <idealista|pisos|fotocasa|milanuncios>   -> ready JS for the browser tab (stores itself in localStorage.roomScan)
  python3 rooms.py ingest file.tsv                                -> classify / filter / store in rooms.json
  python3 rooms.py cards                                          -> JSON of room cards (used by monitor.py build)
  python3 rooms.py summary
TSV: site¦ref¦city(BCN|VLC|CST|TGN)¦addr¦price¦minstay_months¦free_from¦url¦desc
"""
import json, os, re, sys, datetime
from urllib.parse import quote
D = os.path.dirname(os.path.abspath(__file__))
RS = os.path.join(D, "rooms.json")
exec(open(os.path.join(D, "zone_info.py")).read())          # U, E, ZI
# reuse zone rules for Valencia / Castellon from monitor.py
sys.path.insert(0, D)
import monitor as _m
_zone_for0, group_for, flags_for = _m.zone_for, _m.group_for, _m.flags_for
def zone_for(text):
    t = (text or "").lower()
    for pat, z in CYR_V:
        if re.search(pat, t): t += " " + z
    return _zone_for0(t)
FLOOD, DRUG, INDUSTRY, NOISE = _m.FLOOD, _m.DRUG, _m.INDUSTRY, _m.NOISE

# ---------------- Barcelona: zones (grade 1-5; <=2 are excluded for rooms) ----------------
SRC = dict(
 idea_bcn="https://www.idealista.com/de/news/leben-in-spanien/2026/02/09/879190-die-gefaehrlichsten-viertel-in-barcelona",
 local_raval="https://www.thelocal.es/20181018/welcome-to-el-raval-barcelonas-most-dangerous-neighbourhood",
 bcn_safe="https://www.bcn.travel/?p=243955",
 ha_avoid="https://housinganywhere.com/Barcelona--Spain/areas-to-avoid-in-barcelona",
 ha_guide="https://housinganywhere.com/Barcelona--Spain/barcelona-neighborhood-guide",
 plum="https://plumguide.com/journal/these-5-neighbourhoods-are-the-safest-places-to-stay-in-barcelona",
)
def ev(*ks):
    lab = dict(idea_bcn="Idealista: самые опасные районы Барселоны", local_raval="The Local: El Raval", bcn_safe="bcn.travel: самые безопасные районы",
               ha_avoid="HousingAnywhere: районы, которых лучше избегать", ha_guide="HousingAnywhere: гид по районам", plum="Plum Guide: безопасные районы")
    return [(lab[k], SRC[k]) for k in ks]
ZB = {
 "BCN El Raval": (1, "Самый проблемный район центра: мелкая торговля наркотиками, кражи, шум ночью (особенно южная часть).", "Метро L3 Liceu/Drassanes, но для проживания не рекомендуется.", ev("local_raval", "idea_bcn", "ha_avoid"), "репутация (официальных данных по району нет)"),
 "BCN La Barceloneta": (2, "Туристический район у пляжа: шум, карманные кражи, ночью неспокойно.", "Метро L4 Barceloneta, автобусы.", ev("idea_bcn", "ha_avoid"), "репутация"),
 "BCN Ciutat Vella (Gòtic/Born)": (2, "Много карманных краж и ночного шума, туристическая нагрузка.", "Метро L1/L3/L4 рядом.", ev("idea_bcn", "bcn_safe"), "репутация и общегородская статистика"),
 "BCN Besòs/Maresme/Verneda": (2, "Окраина с низкими доходами и случаями торговли наркотиками на отдельных улицах.", "Метро L4 (Besòs, Besòs Mar), трамвай T4.", ev("idea_bcn", "ha_avoid"), "репутация"),
 "BCN Nou Barris (проблемные кварталы)": (2, "Ciutat Meridiana, Torre Baró, Trinitat Nova, Roquetes, Verdun, Vallbona: социально сложные кварталы, отдельные точки торговли наркотиками.", "Метро L3/L4, но далеко и с пересадками.", ev("idea_bcn", "ha_avoid"), "репутация"),
 "BCN Bon Pastor/Baró de Viver/Trinitat Vella": (2, "Окраинные кварталы у промзон и магистралей, репутация неблагополучных.", "Метро L1 / Rodalies.", ev("idea_bcn"), "репутация"),
 "BCN Zona Franca/Port": (2, "Промышленная зона и порт: шум, фуры, мало жилья.", "Метро L9 Zona Universitària / автобусы.", ev("ha_avoid"), "репутация"),
 "BCN Nou Barris (Prosperitat/Guineueta/Turó)": (3, "Спальные кварталы, обычно спокойные, но удалены от моря и центра.", "Метро L3/L4/L5.", ev("ha_guide"), "репутация"),
 "BCN Poble-sec": (3, "Живой район у Монжуика, есть зелёные склоны; на отдельных улицах бывают точки торговли.", "Метро L3 Poble Sec / Paral·lel.", ev("ha_guide", "idea_bcn"), "репутация"),
 "BCN Sagrera/Sant Andreu": (3, "Спокойные жилые районы на севере, много транспортных узлов, меньше туристов.", "Метро L1/L5/L9/L4, Rodalies.", ev("ha_guide"), "репутация"),
 "BCN Horta-Guinardó (Carmel/Vall d'Hebron)": (3, "Холмы и парки (Carmel, Guinardó), спокойно; в Carmel крутые улицы и неровная репутация отдельных кварталов.", "Метро L5, автобусы.", ev("ha_guide", "bcn_safe"), "репутация"),
 "BCN Horta/Guinardó": (4, "Зелёный, тихий район с парками Guinardó и Horta, вдали от туристов.", "Метро L4/L5, автобусы.", ev("ha_guide", "bcn_safe"), "репутация"),
 "BCN Sant Antoni/Eixample": (4, "Центральные районы с низкой преступностью по городским сводкам; много транспорта, но есть шумные улицы.", "Метро L1/L2/L3/L5.", ev("bcn_safe", "plum"), "общегородские данные"),
 "BCN Gràcia": (4, "Безопасный живой район с характером; вечером людно, на площадях шумно.", "Метро L3/L4, FGC.", ev("bcn_safe", "plum", "ha_guide"), "репутация"),
 "BCN Sants/Hostafrancs": (4, "Жилой район у вокзала Sants, спокойный, хорошо связан.", "Sants Estació (Renfe/AVE), метро L1/L5.", ev("bcn_safe", "ha_guide"), "репутация"),
 "BCN Clot/Poblenou/Diagonal Mar": (4, "Район у моря и парков (Poblenou, Diagonal Mar, Parc del Fòrum), безопасный и зелёный, но летом много туристов.", "Метро L1/L4, трамвай T4.", ev("bcn_safe", "plum"), "репутация"),
 "BCN Les Corts/Sarrià/Sant Gervasi": (5, "Один из самых безопасных, зелёных и тихих районов города (по общегородским данным 2023: Eixample и Sarrià-Sant Gervasi с низкой преступностью).", "Метро L3/L5, FGC (Sarrià, Sant Gervasi), трамвай.", ev("bcn_safe", "plum"), "общегородские данные"),
 "BCN общий": (3, "Район в объявлении не уточнён, нужно проверить адрес на карте.", "Метро в Барселоне покрывает город, проверить по адресу.", ev("bcn_safe"), "нет данных по району"),
}
BCN_RULES = [
 (r"raval|sant pau.{0,6}santa creu|santa creu", "BCN El Raval"),
 (r"barceloneta", "BCN La Barceloneta"),
 (r"g[oò]tic|rambla\b|sant pere.{0,6}santa caterina|\bborn\b|la ribera|ciutat vella", "BCN Ciutat Vella (Gòtic/Born)"),
 (r"bes[oò]s|maresme|la mina|verneda|\bpau\b", "BCN Besòs/Maresme/Verneda"),
 (r"ciutat meridiana|torre bar[oó]|trinitat nova|roquetes|verdun|vallbona", "BCN Nou Barris (проблемные кварталы)"),
 (r"bon pastor|bar[oó] de viver|trinitat vella", "BCN Bon Pastor/Baró de Viver/Trinitat Vella"),
 (r"zona franca|marina del prat|port\b.*barcelona|la marina de port", "BCN Zona Franca/Port"),
 (r"prosperitat|guineueta|tur[oó] de la peira|vilapicina|porta\b|canyelles|nou barris", "BCN Nou Barris (Prosperitat/Guineueta/Turó)"),
 (r"poble.?sec|montju[iï]c", "BCN Poble-sec"),
 (r"sagrera|sant andreu|navas|congr[eé]s|bonpastor", "BCN Sagrera/Sant Andreu"),
 (r"carmel|can bar[oó]|vall d.hebron|teixonera|montbau|sant gen[ií]s|la clota", "BCN Horta-Guinardó (Carmel/Vall d'Hebron)"),
 (r"horta|guinard[oó]|el baix guinard[oó]", "BCN Horta/Guinardó"),
 (r"sant antoni|eixample|esquerra de l|dreta de l|fort pienc|sagrada fam[ií]lia|la nova esquerra|l.antiga esquerra", "BCN Sant Antoni/Eixample"),
 (r"gr[aà]cia|camp d.en grassot|vallcarca|el coll|la salut|penitents", "BCN Gràcia"),
 (r"sants|hostafrancs|bordeta|font de la guatlla|badal|la marina", "BCN Sants/Hostafrancs"),
 (r"el clot|camp de l.arpa|poblenou|poble nou|diagonal mar|proven[cç]als|vila ol[ií]mpica|sant mart[ií]|el parc i la llacuna|el besòs", "BCN Clot/Poblenou/Diagonal Mar"),
 (r"sarri[aà]|sant gervasi|bonanova|putxet|tres torres|pedralbes|galvany|les corts|maternitat|sant ramon|vallvidrera|tibidabo|st\. gervasi", "BCN Les Corts/Sarrià/Sant Gervasi"),
]
NOT_BCN = re.compile(r"hospitalet|badalona|santa coloma|sant adri|corn[eé]ll|sant boi|esplugues|sant cugat|castelldefels|terrassa|sabadell|mataró|mataro|el prat|viladecans|gav[aà]", re.I)
BCN_EXCL = re.compile(r"\bunder-?the-?floor\b", re.I)

CYR = [(r"равал", "raval"), (r"готическ|готик", "gòtic"), (r"барселонет", "barceloneta"), (r"бесос|маресме|верн[еэ]да", "besòs"), (r"меридиан|торре-?баро|тринитат|рокетес|вердун|вальбона", "ciutat meridiana"),
       (r"бон-?пастор|баро-де-вивер", "bon pastor"), (r"зона-?франка", "zona franca"), (r"сант-?пере|борн\b|рибера", "sant pere santa caterina"), (r"побле-?сек|монжуик", "poble sec"),
       (r"сагрера|сант-?андреу|навас|конгрес", "sant andreu"), (r"кармель|вальд.?эброн", "carmel"), (r"\bорта\b|гинардо", "horta"), (r"эшампле|эйшампле|эскерра|дрета|сагра-?да|санта-?фамилия|форт-?пиенк|сант-?антони", "eixample"),
       (r"грас[иы]|грассот|ваккарка|эль-?колл|ла-?салют", "gràcia"), (r"сантс|остафранк|хостафранк|бордета|бадал", "sants"), (r"клот|побленоу|диагональ-?мар|провенсалс|сант-?март|олимпик|льякуна|парк-и", "poblenou"),
       (r"саррия|сарри[аы]|сант-?жерва|бонанова|путчет|педральбес|корт[её]с|лес-?корс|матерните|сант-?рамон|тибидабо|вальвидрера|гальван", "sarrià"), (r"гуинуэта|гинеуэта|прос[пп]ерит|туро-?де|вилапишина", "guineueta")]
CYR_V = [(r"орриол", "orriols"), (r"кабаньял|малварроз|каньямелар|касит", "cabanyal"), (r"русаф", "russafa"), (r"эль-?карме|карме\b|велюттерс|вельютерс", "el carme"), (r"бенимаклет", "benimaclet"), (r"бенимамет", "benimàmet"),
         (r"эль-?грау|эль-?грао|мариттим|поблатс-?маритим", "el grau valencia"), (r"беникалап|торрефьель|торрефиэль|раиоса", "benicalap"), (r"эль-?сальер", "el saler"), (r"пинедо|кастелляр|оливераль|ла-?торре|форн-д-алседо", "pobles del sud"),
         (r"ботаник|петхина", "botànic"), (r"патра[ий]кс|эстремадура|хесус|корте?с", "corts"), (r"тресс?-?форкес|оливерета", "tres forques")]
def zone_bcn(text, allow_default=True):
    t = (text or "").lower()
    for pat, z in CYR:
        if re.search(pat, t): t += " " + z
    for pat, z in BCN_RULES:
        if re.search(pat, t): return z
    if allow_default and re.search(r"barcelona|barna|барселон", t): return "BCN общий"
    return None

CITY_NAME = dict(BCN="Барселона", VLC="Валенсия", CST="Кастельон", TGN="Таррагона")
CITY_Q = dict(BCN="Barcelona", VLC="Valencia", CST="Castellón de la Plana", TGN="Tarragona")

# ---------------- bath detection ----------------
PRIV = re.compile(r"(ba[ñn]o|aseo|suite|ванн\w+|санузел|душ\w*|bathroom)\W{0,3}(privad\w*|propio|particular|en suite|en la habitaci[oó]n|individual|exclusiv\w*|частн\w*|собствен\w*|личн\w*|свой|своя)"
                  r"|(privad\w*|propio|particular|individual|exclusiv\w*|частн\w*|собствен\w*|личн\w*|свой|своя|своей)\W{0,3}(ba[ñn]o|aseo|ванн\w*|санузел|душ\w*|bathroom)"
                  r"|en.?suite|con ba[ñn]o|con aseo|ba[ñn]o incluido|habitaci[oó]n con ba[ñn]o|с ванн\w*|с санузл\w*|со своей ванн\w*|con su propio|private bath|ba[ñn]o dentro|dentro de la habitaci[oó]n", re.I)
SHARED = re.compile(r"ba[ñn]o\W{0,3}compartid\w*|compartid\w*\W{0,3}ba[ñn]o|общ\w+ (ванн\w*|санузел)|(ванн\w*|санузел\w*)\W{0,3}общ\w+|shared bath|ba[ñn]os? compartidos|comparte ba[ñn]o|compartir ba[ñn]o", re.I)
def bath_of(text):
    if PRIV.search(text): return "private"
    if SHARED.search(text): return "shared"
    return "unknown"

# ---------------- availability ----------------
MONTHS = dict(enero=1, febrero=2, marzo=3, abril=4, mayo=5, junio=6, julio=7, agosto=8, septiembre=9, setiembre=9, octubre=10, noviembre=11, diciembre=12)
def free_date(s):
    s = (s or "").strip().lower()
    m = re.match(r"(\d\d)-(\d\d)-(\d{4})", s)
    if m: return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.search(r"(\d{1,2}) de (\w+)(?: de (\d{4}))?", s)
    if m and m.group(2) in MONTHS:
        y = int(m.group(3) or datetime.date.today().year); mo = MONTHS[m.group(2)]
        d = datetime.date(y, mo, min(int(m.group(1)), 28))
        if not m.group(3) and d < datetime.date.today() - datetime.timedelta(days=60): d = d.replace(year=y + 1)
        return d
    m = re.search(r"([a-zñé]+) (20\d\d)", s)
    if m and m.group(1) in MONTHS: return datetime.date(int(m.group(2)), MONTHS[m.group(1)], 1)
    return None
DEFER_TXT = re.compile(r"((?:desde|a partir|libre|disponible\w*|entrada)(?:\W+\w+){0,4}?\W+(?:diciembre|enero|febrero|marzo)|(?:diciembre|enero|febrero|marzo)\W+(?:de\W+)?20\d\d|с\W+(?:декабр|январ|феврал))", re.I)
GENDER = [(re.compile(r"s[oó]lo (chicas|mujeres)|solo para (chicas|mujeres)|chicas? (estudiantes|trabajadoras)|только (девуш|женщин)|для девушек|female only|only girls", re.I), "только для девушек"),
          (re.compile(r"s[oó]lo (chicos|hombres)|solo para (chicos|hombres)|только (парн|мужчин)|male only", re.I), "только для парней")]

def load():
    if os.path.exists(RS): return json.load(open(RS))
    return dict(created=datetime.date.today().isoformat(), last_run="", listings={}, rejected={}, excluded={})
def save(s): json.dump(s, open(RS, "w"), ensure_ascii=False, indent=0)
def now(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
def key_of(site, ref):
    ref = str(ref)
    if site == "Pisos.com":
        m = re.search(r"-(\d{9,16})_", ref); return m.group(1) if m else ref
    return ref

def cmd_scan(site, only=False):
    name = dict(idealista="Idealista", pisos="Pisos.com", fotocasa="Fotocasa", milanuncios="Milanuncios")[site]
    s = load(); keys = set(key_of(c["site"], c["ref"]) for c in s["listings"].values() if c["site"] == name)
    keys.update(s["rejected"].get(name, []))
    here = os.path.join(D, "rooms_scan")
    js = open(os.path.join(here, site + ".js")).read().replace("__COMMON__", open(os.path.join(here, "common.txt")).read().strip()).replace("__KNOWN__", json.dumps(sorted(keys)))
    only_keys = sorted(set(key_of(c["site"], c["ref"]) for c in s["listings"].values() if c["site"] == name)) if only else None
    if only:
        print("localStorage.setItem('roomOnly', %s);'set'" % json.dumps(json.dumps(only_keys)), file=sys.stderr)
    print(js)

def rej(s, site, key, why):
    r = s["rejected"].setdefault(site, [])
    if key not in r: r.append(key)
    s["excluded"][why] = s["excluded"].get(why, 0) + 1

def cmd_ingest(path):
    s = load(); added = []; today = datetime.date.today()
    for line in open(path):
        line = line.rstrip("\n")
        if not line.strip(): continue
        line = re.sub(r"^[^¦]*?(?=(Idealista|Pisos\.com|Fotocasa|Milanuncios|Миланун\w+)\s*¦)", "", line.strip())
        f = re.split(r"\s*¦\s*", line); f += [""] * (9 - len(f))
        site, ref, city, addr, price, ms, fr, url, desc = [x.strip() for x in f[:9]]
        site = site.replace("room:", "")
        site = "Milanuncios" if re.search(r"милан|milan", site, re.I) else ("Pisos.com" if re.search(r"pisos|писос", site, re.I) else ("Fotocasa" if re.search(r"foto|фото", site, re.I) else ("Idealista" if re.search(r"ideal|идеал", site, re.I) else site)))
        key = key_of(site, ref)
        bcode = None; gcode = ""; ccode = "?"
        mm = re.match(r"([PSU])([FM]?)([YN?]?)\|(.*)", desc, re.S)
        if mm: bcode, gcode, ccode, desc = mm.group(1), mm.group(2), (mm.group(3) or "?"), mm.group(4)
        if not url and site == "Idealista": url = "https://www.idealista.com/inmueble/%s/" % ref
        url = url.replace("@P", "https://www.pisos.com").replace("@M", "https://www.milanuncios.com").replace("@F", "https://www.fotocasa.es")
        if url in s["listings"]:
            ex = s["listings"][url]
            if bcode:
                cc = ccode or "?"
                if cc == "N":
                    del s["listings"][url]; s["excluded"]["только для одного человека"] = s["excluded"].get("только для одного человека", 0) + 1
                else:
                    if cc != "?": ex["couple"] = cc
                    nb = {"P": "private", "S": "shared"}.get(bcode)
                    if nb and ex.get("bath") == "unknown": ex["bath"] = nb
            continue
        try: price = int(float(price))
        except Exception: continue
        text = addr + " " + desc
        if price > 500 or price < 80: rej(s, site, key, "цена"); continue
        if re.search(r"busco|buscamos|ищу|ищем|se busca habitaci", addr + " " + desc[:80], re.I): rej(s, site, key, "поиск жильцом"); continue
        if city == "BCN":
            if NOT_BCN.search(text[:200]): rej(s, site, key, "не Барселона (пригород)"); continue
            slug = re.sub(r"[-_]\d{6,}.*$", "", ref).replace("_", " ").replace("-", " ") if site == "Pisos.com" else ""
            zk = zone_bcn(addr, False) or zone_bcn(slug, False) or zone_bcn(desc[:260], False) or zone_bcn(addr + " " + desc[:120])
            g = ZB.get(zk) if zk else None
        else:
            slug = re.sub(r"[-_]\d{6,}.*$", "", ref).replace("_", " ").replace("-", " ") if site == "Pisos.com" else ""
            zk = zone_for(addr) or zone_for(slug.replace("habitacion", "")) or zone_for(desc[:200])
            if not zk or zk in ("Valencia общий",):
                if not zk and city == "VLC": zk = "Valencia общий"
                if not zk and city == "CST": zk = "Castelló общий"
                if not zk and city == "TGN": zk = "Tarragona общий"
            if not zk and re.search(r"valencia|val[eè]ncia|castell[oó]n|castelló", addr, re.I): zk = zone_for(addr + " " + desc[:200])
            if not zk and city in ("VLC", "CST"):
                zk = zone_for(desc[:200]) if re.search(r"valencia|castell", desc[:200], re.I) else None
            if zk and ((city == "VLC" and group_for(zk) not in ("Валенсия",)) or (city == "CST" and group_for(zk) not in ("Кастельон",)) or (city == "TGN" and group_for(zk) not in ("Таррагона и побережье",))):
                rej(s, site, key, "пригород/другой город"); continue
            if zk and _m.FAR.search(text[:200]): rej(s, site, key, "далеко"); continue
            g = (ZI.get(zk) or (_m.zinfo(zk) if city == "TGN" else None)) if zk else None
        if not g or (city == "BCN" and zk == "BCN общий"): rej(s, site, key, "район не определён"); continue
        # quality filter: bad districts out
        flags = flags_for(zk) if city != "BCN" else []
        bad = g[0] <= 2 or (city != "BCN" and (zk in FLOOD or zk in DRUG or zk in INDUSTRY))
        if bad:
            rej(s, site, key, "плохой район: " + zk); continue
        if ccode == "N": rej(s, site, key, "только для одного человека"); continue
        # minimum stay: need <= 1 month
        try: msn = int(ms) if ms else None
        except Exception: msn = None
        if msn and msn > 1: rej(s, site, key, "минимальный срок больше 1 месяца"); continue
        bath = {"P": "private", "S": "shared", "U": "unknown"}.get(bcode) or bath_of(desc + " " + addr)
        fd = free_date(fr) or free_date(desc[:200])
        deferred = bool(fd and fd > today + datetime.timedelta(days=35)) or bool(DEFER_TXT.search(fr + " " + desc[:250]))
        avail = ("свободно с " + fd.strftime("%d.%m.%Y")) if fd else (fr[:60] if fr else "")
        tags = [t for rx, t in GENDER if rx.search(text)]
        if gcode == "F" and "только для девушек" not in tags: tags.append("только для девушек")
        if gcode == "M" and "только для парней" not in tags: tags.append("только для парней")
        ut = re.search(r"gastos \+(\d+)", desc)
        extra = ("+%s €/мес коммунальные" % ut.group(1)) if ut else ""
        clean_addr = re.sub(r"^\s*(Habitaci[oó]n|Comparto|Room)\s+(en|in)\s+", "", addr, flags=re.I)[:90]
        c = dict(kind="room", site=("Pisos.com" if site == "Pisos.com" else site), also="", group=CITY_NAME[city], city=city, zone=zk, addr=clean_addr, price=price, rooms="комната", m2=None, lift="?", temp=False,
                 link=url, grade=g[0], note=g[1], flood=False, ref=str(ref), extra=extra, transport=g[2], evidence=g[3], level=g[4], flags=flags + (["район в объявлении не указан"] if zk.endswith("общий") else []) + tags,
                 maps="https://www.google.com/maps/search/?api=1&query=" + quote(clean_addr + ", " + CITY_Q[city]), first_seen=today.isoformat(), seen_ts=now(),
                 deferred=deferred, avail_note=avail, gone=False, bath=bath, couple=ccode, minstay=(msn if msn is not None else ""), score=0)
        dup = next((x for x in s["listings"].values() if x["city"] == city and x["price"] == price and re.sub(r"\W", "", x["addr"].lower())[:22] == re.sub(r"\W", "", clean_addr.lower())[:22]), None)
        if dup:
            if site not in dup["site"] and site not in dup["also"]: dup["also"] = (dup["also"] + ", " + site).lstrip(", ")
            continue
        s["listings"][url] = c; added.append(c)
    s["last_run"] = now(); save(s)
    print("added", len(added), "| excluded (all time):", json.dumps(s["excluded"], ensure_ascii=False))
    for a in added: print(" +", a["site"], "|", a["group"], a["zone"], "|", a["price"], "€", "| санузел:", a["bath"], "| мин.срок:", a["minstay"] or "?", "|", a["avail_note"], "| defer" if a["deferred"] else "", "|", a["addr"][:50])

def cards():
    s = load(); out = []
    for c in s["listings"].values():
        if c.get("gone"): continue
        c = dict(c); c["score"] = c["grade"] * 10 + (6 if c["bath"] == "private" else 0) + (4 if c.get("couple") == "Y" else 0) - (c["price"] / 60.0); out.append(c)
    return out

def cmd_summary():
    s = load(); cs = cards(); t = datetime.date.today().isoformat()
    print("rooms", len(cs), "| deferred", sum(1 for c in cs if c["deferred"]), "| with bath", sum(1 for c in cs if c["bath"] == "private"), "| new today", sum(1 for c in cs if c["first_seen"] == t), "| last_run", s.get("last_run"))
    print("by city:", {k: sum(1 for c in cs if c["group"] == k) for k in CITY_NAME.values()})
    print("excluded:", json.dumps(s["excluded"], ensure_ascii=False))

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "scan": cmd_scan(a[1], only=("--only" in a))
    elif a[0] == "ingest": cmd_ingest(a[1])
    elif a[0] == "cards": print(json.dumps(cards(), ensure_ascii=False))
    elif a[0] == "summary": cmd_summary()
