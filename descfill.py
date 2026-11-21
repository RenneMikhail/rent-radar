#!/usr/bin/env python3
"""Полные описания для всех активных карточек (шаг цикла после ingest, до screen.py).
  python3 descfill.py gen    -> scan/desc_idea.js, scan/desc_yae.js (запустить во вкладках Idealista / yaencontre, потом скопировать window.__dd.out в inbox/desc_idea.json / desc_yae.json через <pre> + cmd+a, cmd+c, pbpaste)
  python3 descfill.py direct -> Pisos.com / Fotocasa / Habitaclia напрямую (urllib)
  python3 descfill.py apply  -> влить inbox/desc_*.json в details/*.json, снятые (ERR404/410 у yae) пометить gone, обновить поле d в pub/p/*.json
Описание yaencontre берётся из .box-readmore (в выдаче оно обрезано «...»), Idealista из .commentsContainer .comment."""
import json, os, re, sys, time
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
import screen
def S(): return json.load(open("state.json"))
def det(n):
    p = "details/%s.json" % n
    return json.load(open(p)) if os.path.exists(p) else {}
ALL = "--all" in sys.argv
def bad(d): return ALL or len(d) < 40 or d.rstrip().endswith("...")
def gen():
    s = S()["listings"]; di = det("idealista"); dy = det("yae"); ide = []; yae = []
    for l, c in s.items():
        if c.get("gone") or c.get("archived"): continue
        if "idealista.com" in l:
            i = re.search(r"/inmueble/(\d+)", l).group(1)
            if bad((di.get(i) or {}).get("d", "")): ide.append("/ru/inmueble/%s/" % i)
        elif "yaencontre.com" in l:
            k = l.rstrip("/").split("-")[-1]
            if bad((dy.get(k) or {}).get("d", "")): yae.append(l.split("yaencontre.com")[1])
    def js(L, sel):
        return ("window.__dd={done:false,out:{},n:0};(async()=>{const L=%s;const sleep=ms=>new Promise(r=>setTimeout(r,ms));\n"
                "for(const p of L){try{const r=await fetch(p);const id=p.match(/(\\d+)\\/?$/)[1];if(!r.ok){window.__dd.out[id]='ERR'+r.status;}else{const t=await r.text();const d=new DOMParser().parseFromString(t,'text/html');%s}}catch(e){}window.__dd.n++;await sleep(500);}\n"
                "window.__dd.done=true;})();'started'") % (json.dumps(L), sel)
    open("scan/desc_idea.js", "w").write(js(ide, "let e=d.querySelector('.commentsContainer .comment')||d.querySelector('.adCommentsLanguage')||d.querySelector('.commentsContainer');window.__dd.out[id]=e?e.innerText.replace(/\\s+/g,' ').trim():'';"))
    open("scan/desc_yae.js", "w").write(js(yae, "let es=[...d.querySelectorAll('.box-readmore')].map(x=>x.innerText.replace(/[ \\t]+/g,' ').trim()).filter(x=>x&&!/Al guardar, aceptas/.test(x)).sort((a,b)=>b.length-a.length);window.__dd.out[id]=es[0]||'';"))
    print("Idealista без описания:", len(ide), "| yaencontre без полного описания:", len(yae))
def direct():
    import details as DT
    s = S()["listings"]
    for site, fn, key, name in (("pisos.com", DT.pisos, r"-(\d{9,16})_", "pisos"), ("fotocasa.es", DT.fotocasa, r"/(\d+)/d$", "fotocasa"), ("habitaclia.com", DT.fotocasa, r"/([0-9a-f-]{36})/d$", "habitaclia")):
        db = det(name); ok = n = 0
        for u, c in s.items():
            if site not in u or c.get("gone") or c.get("archived"): continue
            m = re.search(key, u)
            if not m or ((db.get(m.group(1)) or {}).get("d") and not ALL): continue
            r = fn(u); n += 1
            if r and r.get("d"):
                r["p"] = (db.get(m.group(1)) or {}).get("p") or r["p"]; db[m.group(1)] = r; ok += 1
            time.sleep(0.5)
        json.dump(db, open("details/%s.json" % name, "w"), ensure_ascii=False); print(name, "пробовал", n, "заполнено", ok)
def apply():
    for site, f in (("yae", "inbox/desc_yae.json"), ("idealista", "inbox/desc_idea.json")):
        if not os.path.exists(f): continue
        new = json.load(open(f)); db = det(site); gone = []
        for k, v in new.items():
            if v.startswith("ERR4"): gone.append(k)
            elif len(v) > 40: db[k] = dict(db.get(k) or {"p": []}, d=v)
        json.dump(db, open("details/%s.json" % site, "w"), ensure_ascii=False)
        if site == "yae":
            s = S(); c = 0
            for l, x in s["listings"].items():
                if "yaencontre.com" in l and l.rstrip("/").split("-")[-1] in gone and not x.get("gone"): x["gone"] = True; c += 1
            json.dump(s, open("state.json", "w"), ensure_ascii=False, indent=1); print("yae снято (410):", c)
    screen.DET.clear(); n = 0
    for l, c in S()["listings"].items():
        if c.get("gone") or c.get("archived"): continue
        d = screen.details_desc(l); pp = os.path.join("pub", "p", screen.mid(l) + ".json")
        if d and os.path.exists(pp):
            pk = json.load(open(pp))
            if (pk.get("d") or "") != d: pk["d"] = d; json.dump(pk, open(pp, "w")); n += 1
    print("пакетов обновлено:", n)
if __name__ == "__main__": {"gen": gen, "direct": direct, "apply": apply}[sys.argv[1]]()
