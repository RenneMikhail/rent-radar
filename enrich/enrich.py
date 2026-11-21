"""Обогащение карточек: мебель (furn), парковка (park, parkn), телефон (phone).
furn: yes | no | ?      park: incl | extra | yes | no | ?
Телефоны берём ТОЛЬКО из кода страницы (Pisos.com, Fotocasa) или из текста объявления; кнопки «Показать телефон» не нажимаем.
"""
import re, json, os, sys, time, html, urllib.request
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36", "Accept-Language": "es-ES,es;q=0.9"}
BOIL = re.compile(r"Garajes? (para|de|y)|Alquiler plaza de garaje|Alquilar garajes|precio, m²|Garajes y trasteros", re.I)
NEG = re.compile(r"(no incluye|sin|no dispone de|no tiene|no hay|carece de)\W+(\w+\W+){0,3}(parking|garaje|aparcamiento|plaza)|(parking|garaje|aparcamiento)[^.]{0,30}(no incluid|no disponible)", re.I)
EXTRA = re.compile(r"(plaza|parking|garaje|aparcamiento)[^.]{0,60}(opcional|\d+\s?€|por \d+|aparte|adicional|no incluid)|opcional[^.]{0,30}(plaza|parking|garaje|aparcamiento)", re.I)
INCL = re.compile(r"(plaza de (garaje|parking|aparcamiento)|garaje|parking|aparcamiento)[^.]{0,40}(incluid|privad[ao])|incluye[^.]{0,30}(plaza de )?(garaje|parking|aparcamiento)|(garaje|parking|aparcamiento)\s+(propio|privado)|plaza (privada )?de (parking|garaje) para cada", re.I)
YES = re.compile(r"plaza de (garaje|aparcamiento|parking)|\bgaraje\b|\bparking\b|aparcamiento", re.I)
FREE_ST = re.compile(r"gratuit|en la calle|zona azul|calle|a \d+ m", re.I)
def classify_park(lines, struct=False):
    price = ""
    for x in lines:
        if BOIL.search(x) or len(x) < 12: continue
        if NEG.search(x): return "no", ""
    for x in lines:
        if BOIL.search(x) or len(x) < 12 or FREE_ST.search(x): continue
        if EXTRA.search(x):
            m = re.search(r"(\d+)\s?€", x); return "extra", ((m.group(1) + " €/мес") if m else "")
    for x in lines:
        if BOIL.search(x) or len(x) < 12 or FREE_ST.search(x): continue
        if INCL.search(x): return "incl", ""
    if struct: return "yes", ""
    for x in lines:
        if BOIL.search(x) or len(x) < 12 or FREE_ST.search(x): continue
        if YES.search(x): return "yes", ""
    return "?", ""
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode("utf8", "replace")
def txt(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h); h = re.sub(r"<[^>]+>", "\n", h)
    return [re.sub(r"\s+", " ", html.unescape(x)).strip() for x in h.split("\n") if x.strip()]
def py_enrich(card):
    """Pisos.com / Fotocasa: прямой запрос."""
    l = card["link"]; r = {"furn": "yes", "park": "?", "parkn": "", "phone": ""}
    h = get(l); lines = txt(h)
    if "pisos.com" in l:
        ph = re.findall(r'"telefono"\s*:\s*"\+?(?:34)?(\d{9})"', h)
        cm = re.search(r'"caracteristicasInmueble":"([^"]*)"', h); struct = bool(cm and "garaje" in cm.group(1))
        lab = [x for x in lines if re.match(r"Garaje:\s*$", x)]
        struct = struct or bool(lab)
        r["park"], r["parkn"] = classify_park([x for x in lines if len(x) > 20], struct)
        r["phone"] = ph[0] if ph else ""
        if not any(re.search(r"(?i)^Amueblado$", x) for x in lines) and re.search(r"(?i)sin amueblar|sin muebles", h): r["furn"] = "no"
    else:
        k = re.search(r"/(\d+)/d$", l).group(1); ph = []
        for m in re.finditer(r'"phone"\s*:\s*"\+?(?:34)?(\d{9})"', h):
            if k in h[max(0, m.start() - 3000):m.end() + 3000]: ph.append(m.group(1))
        r["phone"] = ph[0] if ph else ""
        slug = l.split("/")[-3] if l.endswith("/d") else ""
        struct = "parking" in slug.split("-")
        r["park"], r["parkn"] = classify_park([x for x in lines if len(x) > 20], struct)
        r["furn"] = "no" if re.search(r"(^|-)no-amueblado", slug) else ("yes" if "amueblado" in slug else "?") if True else ("?" if True else "?")
    return r
if __name__ == "__main__":
    st = os.path.join(D, "state.json"); s = json.load(open(st)); n = 0
    for c in s["listings"].values():
        if c.get("gone") or c.get("archived") or c.get("enr"): continue
        if "pisos.com" in c["link"] or "fotocasa.es" in c["link"]:
            try:
                r = py_enrich(c)
                if c.get("furn") in ("yes", "no"): r.pop("furn", None)
                if c.get("park") in ("incl", "extra", "no") : r.pop("park", None); r.pop("parkn", None)
                c.update(r); c["enr"] = 1; n += 1
            except Exception as e: print("ERR", c["link"][-40:], e)
            time.sleep(0.8)
    json.dump(s, open(st, "w"), ensure_ascii=False, indent=0); print("py-enriched", n)
