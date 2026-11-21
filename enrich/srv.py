import http.server, socketserver, os, json, re, subprocess, sys
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=D,**k)
    def end_headers(s):
        s.send_header('Access-Control-Allow-Origin','*'); s.send_header('Access-Control-Allow-Private-Network','true'); s.send_header('Access-Control-Allow-Headers','*'); super().end_headers()
    def do_OPTIONS(s): s.send_response(204); s.end_headers()
    def do_GET(s):
        m=re.match(r'/scan_js/(\w+)$',s.path)
        if m:
            out=subprocess.run([sys.executable,'monitor.py','scan',m.group(1)],cwd=D,capture_output=True,text=True).stdout.encode()
            s.send_response(200); s.send_header('Content-Type','text/plain; charset=utf-8'); s.send_header('Content-Length',str(len(out))); s.end_headers(); s.wfile.write(out); return
        return super().do_GET()
    def do_POST(s):
        n=int(s.headers.get('Content-Length',0)); b=s.rfile.read(n)
        name=re.sub(r'[^\w.-]','_',s.path.strip('/'))
        open(os.path.join(D,'inbox',name),'wb').write(b)
        s.send_response(200); s.end_headers(); s.wfile.write(b'ok %d'%n)
    def log_message(s,*a): pass
socketserver.TCPServer.allow_reuse_address=True
with socketserver.TCPServer(('127.0.0.1',8765),H) as srv: srv.serve_forever()
