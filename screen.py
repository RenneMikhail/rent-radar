#!/usr/bin/env python3
"""Отсев объявлений: временная аренда, только студентам / врачам / госслужащим.
Читает описания из pub/p/<id>.json (поле d) + поля карточки; ставит c['excl']=причина (карточка скрывается при build).
Запуск: python3 screen.py [--dry]  (после pack.py, до финального build)."""
import json, os, re, sys
D = os.path.dirname(os.path.abspath(__file__))
def mid(k):
    h = 2166136261
    for ch in k: h ^= ord(ch); h = (h * 16777619) & 0xFFFFFFFF
    n = h; s = ""
    while n: s = "0123456789abcdefghijklmnopqrstuvwxyz"[n % 36] + s; n //= 36
    return "m" + (s or "0")
TEMP = [
 r"alquiler (de )?temporada", r"de temporada", r"por temporada", r"contrato de temporada", r"alquiler temporal", r"\btemporal\b", r"temporada (de )?(invierno|verano|escolar|acad)",
 r"alquiler de (corta|media) (estancia|duraci)", r"media estancia", r"corta estancia", r"estancia (corta|temporal)", r"mid[- ]?term", r"short[- ]?(term|stay)", r"temporary", r"seasonal",
 r"temporal de \d+ meses", r"alquiler (de )?(\d+|seis|nueve|once) meses",
 r"(m[aá]ximo|hasta|durante)\s*(\d+|seis|nueve|once|11)\s*meses", r"hasta (el )?(\d{1,2} de )?(mayo|junio|julio|agosto|septiembre)( de)? (20)?2[67]\b",
 r"hasta (finales de )?(mayo|junio|julio|agosto|septiembre)\b", r"1 año m[aá]ximo", r"menos de (un )?a[nñ]o",
 r"\bсезон", r"\bвременн\w*\s+(аренд|проживан|жиль|срок|размещ)", r"(аренд\w*|проживани\w*)\s+временн", r"только для временн", r"краткосрочн", r"на (\d+|несколько) месяц", r"до \d+ (мая|июня|июля|августа|сентября)", r"до (конца )?(мая|июня|июля|августа|сентября)\b",
 r"lloguer de temporada", r"temporada\b",
]
STUD = [
 r"(solo|[uú]nicamente|exclusivamente|exclusiu\w*|exclusivo|dirigido|destinado|orientado|pensad[oa]|reservad[oa])\s+(a|para|per)\s+(los\s+)?(estudiantes|estudiants|universitari\w*)",
 r"para estudiantes", r"per estudiants", r"student rooms?", r"residencia (\w+ )?(est|para est)", r"estudiantes? (de|universitari)", r"для студентов", r"студентам", r"студенты", r"только студент", r"студенческ",
]
WORK = [
 r"m[eé]dic[oa]s?\b", r"personal sanitario", r"sanitari[oa]s?", r"enfermer[oa]s?", r"\bMIR\b", r"funcionari[oa]s?", r"empleados? p[uú]blicos?", r"administraci[oó]n p[uú]blica", r"civil servants?", r"\bврач", r"медик", r"госслуж", r"чиновник",
]
NEG = re.compile(r"(a[nñ]os:?\s*$|\bno\b|\bsin\b|\bni\b|\bnot\b|\bнет\b|\bне\b)[^.]{0,30}$", re.I)
MIX = re.compile(r"profesional|trabajador|famili|parej|specialist|специалист|профессионал|работник|\bпар\b|пары|семь|jubilad|workers|professional", re.I)
AMEN = re.compile(r"(cerca|alrededor|rodead\w*|mercados?|comercios?|colegios?|escuelas?|hospitales|centros?|gimnasios?|supermercados?|servicios|transporte|cl[ií]nicas?)[^.]{0,80}$", re.I)
CLOTH = re.compile(r"^[^.]{0,12}(одежд|ropa)", re.I)
def find(pats, text, mix=False):
    for p in pats:
        for m in re.finditer(p, text, re.I):
            pre = text[max(0, m.start() - 40):m.start()]
            if NEG.search(pre): continue
            if p in WORK and AMEN.search(text[max(0, m.start() - 90):m.start()]): continue
            if CLOTH.search(text[m.end():m.end() + 25]): continue
            if mix and MIX.search(text[max(0, m.start() - 70):m.end() + 70]) and not re.search(r"solo|exclusiu|exclusivo|[uú]nicamente|только", text[max(0, m.start() - 30):m.end()], re.I): continue
            return text[max(0, m.start() - 30):m.end() + 30].replace("\n", " ")
    return None
def reason_for(c, desc):
    t = " ".join([desc or "", c.get("avail_note", ""), c.get("addr", "")])
    for kind, pats, label in (("temp", TEMP, "временная аренда"), ("stud", STUD, "студентам"), ("work", WORK, "врачам/госслужащим")):
        h = find(pats, t, mix=(kind=="stud"))
        if h: return label + ": …" + h.strip() + "…"
    return None
DET = {}
def details_desc(link):
    """описание из details/<site>.json по id объявления"""
    if not DET:
        for fn in ("idealista", "pisos", "yae", "fotocasa", "habitaclia"):
            fp = os.path.join(D, "details", fn + ".json")
            DET[fn] = json.load(open(fp)) if os.path.exists(fp) else {}
    if "idealista.com" in link: m = re.search(r"/inmueble/(\d+)", link); fn = "idealista"
    elif "pisos.com" in link: m = re.search(r"-(\d{9,16})_", link); fn = "pisos"
    elif "yaencontre.com" in link: m = re.search(r"-(\d+)$", link); fn = "yae"
    elif "fotocasa.es" in link: m = re.search(r"/(\d+)/d$", link); fn = "fotocasa"
    elif "habitaclia.com" in link: m = re.search(r"/([0-9a-f-]{36})/d", link); fn = "habitaclia"
    else: return ""
    if not m: return ""
    d = (DET.get(fn, {}).get(m.group(1), {}) or {}).get("d", "")
    if not d and fn == "idealista": d = (DET.get("yae", {}).get(m.group(1), {}) or {}).get("d", "")  # yaencontre дублирует Idealista под тем же номером
    return d
def main(dry=False):
    p = os.path.join(D, "state.json"); s = json.load(open(p)); n = 0; out = []
    for l, c in s["listings"].items():
        if c.get("gone") or c.get("archived"): continue
        if c.get("excl_keep"): continue
        pp = os.path.join(D, "pub", "p", mid(l) + ".json"); d = ""
        if os.path.exists(pp):
            try: d = json.load(open(pp)).get("d", "")
            except Exception: pass
        d2 = details_desc(l)
        if d2 and d2 not in d: d = d + " " + d2
        r = reason_for(c, d)
        if r: r = r.replace("\ufffd", "")
        if r and c.get("excl") != r:
            out.append((c["site"], c.get("zone"), c.get("price"), r[:110], l[-50:])); 
            if not dry: c["excl"] = r.replace("\ufffd", "")
            n += 1
        elif not r and c.get("excl") and d and not dry: c.pop("excl")
    if not dry: json.dump(s, open(p, "w"), ensure_ascii=False, indent=1)
    for o in out: print(" -", *o)
    print("excluded:", n, "| total excl:", sum(1 for c in s["listings"].values() if c.get("excl") and not c.get("gone")))
if __name__ == "__main__": main("--dry" in sys.argv)
