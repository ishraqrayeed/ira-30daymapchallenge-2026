"""Local browser-test result collector, never a gameplay dependency or deployed asset."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
import json
class Handler(SimpleHTTPRequestHandler):
 def do_POST(self):
  if self.path!='/__qa':self.send_error(404);return
  obj=json.loads(self.rfile.read(int(self.headers['Content-Length'])));Path('/tmp/day24-game-browser-report.json').write_text(json.dumps(obj,indent=2)+'\n');self.send_response(200);self.send_header('Access-Control-Allow-Origin','http://127.0.0.1:8016');self.end_headers();self.wfile.write(b'OK')
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8017),partial(Handler,directory=str(Path(__file__).resolve().parent))).serve_forever()
