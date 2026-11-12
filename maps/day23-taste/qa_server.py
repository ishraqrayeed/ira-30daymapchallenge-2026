"""Optional local-only browser test collector; never packaged or deployed."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
import json
class H(SimpleHTTPRequestHandler):
 def do_POST(self):
  if self.path!='/__qa':self.send_error(404);return
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  Path('/tmp/day23-browser-report.json').write_text(json.dumps(data,indent=2))
  self.send_response(200);self.send_header('Access-Control-Allow-Origin','http://127.0.0.1:8014');self.end_headers();self.wfile.write(b'OK')
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8015),partial(H,directory=str(Path(__file__).resolve().parent))).serve_forever()
