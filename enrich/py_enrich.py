import urllib.request,re,json,time,html,sys
UA={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36","Accept-Language":"es-ES,es;q=0.9"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30).read().decode('utf8','replace')
s=json.load(open('state.json'))['listings']
act=[c for c in s.values() if not c.get('gone') and not c.get('archived')]
out={}
def txt(h):
    h=re.sub(r'(?is)<(script|style).*?</\1>',' ',h); h=re.sub(r'<[^>]+>','\n',h); return [re.sub(r'\s+',' ',html.unescape(x)).strip() for x in h.split('\n') if x.strip()]
for c in act:
    l=c['link']
    if 'pisos.com' in l:
        k=re.search(r'-(\d{9,16})_',l).group(1)
        try: h=get(l)
        except Exception as e: out[l]={'err':str(e)}; continue
        ph=re.findall(r'"telefono"\s*:\s*"\+?(?:34)?(\d{9})"',h)
        cm=re.search(r'"caracteristicasInmueble":"([^"]*)"',h); struct=cm.group(1) if cm else ''
        lines=txt(h)
    elif 'fotocasa.es' in l:
        k=re.search(r'/(\d+)/d$',l).group(1)
        try: h=get(l)
        except Exception as e: out[l]={'err':str(e)}; continue
        # phone of the ad itself: look near the ad id
        ph=[]; struct=''
        for m in re.finditer(r'"phone"\s*:\s*"\+?(?:34)?(\d{9})"',h):
            seg=h[max(0,m.start()-3000):m.end()+3000]
            if k in seg: ph.append(m.group(1))
        lines=txt(h)
    else: continue
    park=list(dict.fromkeys(x[:160] for x in lines if re.search(r'(?i)garaje|aparcamiento|parking|plaza de',x) and len(x)<400))[:4]
    furn=list(dict.fromkeys(x[:120] for x in lines if re.search(r'(?i)amueblad|equipad|sin muebles|vac[ií]o',x) and len(x)<300))[:3]
    out[l]={'ph':list(dict.fromkeys(ph))[:2],'park':park,'furn':furn,'struct':struct}
    time.sleep(0.8)
json.dump(out,open('enrich/py_out.json','w'),ensure_ascii=False,indent=0)
print(len(out), sum(1 for v in out.values() if v.get('ph')), 'with phone')
