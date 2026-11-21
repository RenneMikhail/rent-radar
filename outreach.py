#!/usr/bin/env python3
"""Dry-run: кому и что бот отправил бы. Ничего не отправляет.
python3 outreach.py            -> outreach_dryrun.md
Источники: state.json, marks_dump/marks/*.json (пометки Да/Нет/Позвонил), outreach_log.json (уже писали).
"""
import json, glob, os, re
H = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(f"{H}/state.json"))["listings"]
TXT = open(f"{H}/contact.txt", encoding="utf-8").read().strip()
marks = {}
for f in glob.glob(f"{H}/marks_dump/marks/*.json"):
    try:
        d = json.load(open(f)); d = d.get("data", d); marks[d.get("k")] = d
    except Exception: pass
log = json.load(open(f"{H}/outreach_log.json")) if os.path.exists(f"{H}/outreach_log.json") else {}
FORM = {"Idealista": "форма «Связаться» на Idealista (нужен вход)", "Fotocasa": "форма на Fotocasa (нужен вход)",
        "Habitaclia": "форма на Habitaclia", "Pisos.com": "форма на Pisos.com", "yaencontre": "форма на yaencontre"}
rows = []; skip = {"снято/скрыто": 0, "Нет": 0, "уже звонили": 0, "уже писали": 0, "комната/дом вне квартир": 0}
for k, c in S.items():
    if c.get("gone") or c.get("excl") or c.get("archived"): skip["снято/скрыто"] += 1; continue
    if c.get("kind") not in (None, "apt"): skip["комната/дом вне квартир"] += 1; continue
    m = marks.get(c.get("link"), {})
    if m.get("s") == "bad": skip["Нет"] += 1; continue
    if m.get("c"): skip["уже звонили"] += 1; continue
    if k in log: skip["уже писали"] += 1; continue
    msg = TXT.format(addr=c.get("addr", ""), price=c.get("price", ""), link=c.get("link", ""))
    ph = re.sub(r"\D", "", str(c.get("phone") or ""))
    ch = (f"1) проверить +34{ph[-9:]} в WhatsApp; есть → wa.me (1 тап); нет → " if len(ph) >= 9 else "") + FORM.get(c.get("site"), "форма портала")
    rows.append((c, ch, msg))
out = [f"# Dry-run рассылки\nВсего кандидатов: {len(rows)}. Пропущено: " + ", ".join(f"{a} {b}" for a, b in skip.items()) + "\n\nНИЧЕГО НЕ ОТПРАВЛЕНО.\n"]
for c, ch, msg in rows:
    out.append(f"## {c.get('site')} · {c.get('zone')} · {c.get('price')} € · {c.get('rooms')} комн. · {c.get('m2')} м²\n{c.get('addr')}\n{c.get('link')}\nКанал: {ch}\n")
out.append("\n## Текст (пример для первого объявления)\n```\n" + (rows[0][2] if rows else "") + "\n```\n")
open(f"{H}/outreach_dryrun.md", "w", encoding="utf-8").write("\n".join(out))
print(len(rows), skip, sum(1 for c,_,_ in rows if c.get("phone")))
