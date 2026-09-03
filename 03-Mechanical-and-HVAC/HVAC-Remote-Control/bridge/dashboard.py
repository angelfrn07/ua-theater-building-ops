#!/usr/bin/env python3
"""
Local dashboard for the UA Theater Novar panel.

Why a server and not a plain .html file: the panel has no CORS headers, so a
file:// page cannot read it. The 8/23 dashboard worked only because the JS was
injected into the panel's own authenticated tab, which is why it died on
reload. This serves the page from localhost and proxies obix server-side, so
it survives reloads and needs no Java and no injection.

  python3 dashboard.py [port]     default 8770
"""

import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import bas

PAGE = r"""<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UA Theater - Building Panel</title>
<style>
  :root{
    --bg:#0e1013; --panel:#161a20; --line:#242a33; --ink:#e8ecf1;
    --dim:#8b95a3; --ok:#3ecf8e; --down:#ff6b6b; --warn:#ffb454; --accent:#5b9dff;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
    padding:20px 16px 64px;max-width:860px;margin-inline:auto}
  h1{font-size:19px;margin:0 0 2px;letter-spacing:-.01em}
  .sub{color:var(--dim);font-size:13px;margin-bottom:18px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;
    padding:16px;margin-bottom:14px}
  .banner{display:flex;gap:12px;align-items:flex-start}
  .dot{width:10px;height:10px;border-radius:50%;flex:none;margin-top:6px}
  .dot.on{background:var(--ok);box-shadow:0 0 0 4px rgba(62,207,142,.15)}
  .dot.off{background:var(--down);box-shadow:0 0 0 4px rgba(255,107,107,.15)}
  .banner h2{margin:0 0 4px;font-size:15px}
  .steps{margin:8px 0 0;padding-left:18px;color:var(--dim);font-size:13px}
  .steps li{margin:3px 0}
  h3{font-size:12px;text-transform:uppercase;letter-spacing:.09em;
    color:var(--dim);margin:0 0 12px;font-weight:600}
  .counts{display:flex;gap:22px;margin-bottom:14px}
  .n{font-size:26px;font-weight:600;line-height:1}
  .n small{display:block;font-size:11px;font-weight:400;color:var(--dim);
    text-transform:uppercase;letter-spacing:.07em;margin-top:5px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(84px,1fr));gap:7px}
  .u{border:1px solid var(--line);border-radius:8px;padding:8px 9px;font-size:13px;
    background:#12151a}
  .u b{display:block;font-weight:600}
  .u span{font-size:11px;color:var(--dim)}
  .u.up{border-color:rgba(62,207,142,.35)} .u.up b{color:var(--ok)}
  .u.down{border-color:rgba(255,107,107,.35)} .u.down b{color:var(--down)}
  button{font:inherit;font-size:14px;padding:11px 15px;border-radius:9px;
    border:1px solid var(--line);background:#1c222b;color:var(--ink);
    cursor:pointer;width:100%;text-align:left;margin-bottom:8px}
  button:hover:not(:disabled){border-color:var(--accent)}
  button:disabled{opacity:.4;cursor:not-allowed}
  button b{display:block} button span{font-size:12px;color:var(--dim)}
  .dormant{opacity:.55}
  .note{color:var(--dim);font-size:12.5px;margin-top:12px;
    border-top:1px solid var(--line);padding-top:12px}
  #log{font:12px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--dim);
    white-space:pre-wrap;word-break:break-word;max-height:190px;overflow:auto}
  .row{display:flex;gap:8px}.row button{margin-bottom:0}
</style>

<h1>UA Theater &middot; Building Panel</h1>
<div class="sub">Novar XCM.20R &middot; NiagaraAX 3.5.34 &middot; 8725 W Amarillo Blvd</div>

<div class="card banner" id="conn">
  <div class="dot off"></div><div><h2>Checking panel...</h2></div>
</div>

<div class="card">
  <h3>Rooftop units</h3>
  <div id="census"><span class="sub">Waiting on the panel.</span></div>
</div>

<div class="card">
  <h3>Cooling</h3>
  <button data-c="cool_start"><b>Start cooling</b><span>1 hour, then auto-reverts. Reaches only units on the bus.</span></button>
  <div class="row">
    <button data-c="cool_hold"><b>Hold</b><span>Past the timer</span></button>
    <button data-c="cool_release"><b>Release</b><span>Back to Auto</span></button>
  </div>
  <div class="note">Every button asks once before it writes. A green result means the
    panel accepted the command, not that a compressor started. Watch the unit temps.</div>
</div>

<div class="card dormant">
  <h3>Lighting &middot; dormant</h3>
  <button data-c="lights_interior_test"><b>Test interior zone</b><span>Override goes Active, output stays null</span></button>
  <button data-c="lights_exterior_test"><b>Test exterior zone</b><span>Same, photocell zone</span></button>
  <div class="note">The lighting side was never commissioned. These fire cleanly and
    turn on nothing. Making the panel run lights is a BGIS commissioning job.</div>
</div>

<div class="card"><h3>Activity</h3><div id="log">ready</div></div>

<script>
const $ = s => document.querySelector(s);
const log = m => { const l=$('#log');
  l.textContent = new Date().toLocaleTimeString() + '  ' + m + '\n' + l.textContent; };
const api = (p,q) => fetch('/api/'+p+(q?'?'+new URLSearchParams(q):'')).then(r=>r.json());

let online = false;

async function ping(){
  const d = await api('ping');
  online = !!d.reachable;
  const c = $('#conn');
  if (online){
    c.innerHTML = '<div class="dot on"></div><div><h2>Panel connected</h2>'
      + '<div class="sub" style="margin:0">' + (d.serverName||'station') + '</div></div>';
  } else {
    c.innerHTML = '<div class="dot off"></div><div><h2>Not on the panel yet</h2>'
      + '<div class="sub" style="margin:0">This laptop has no route to 192.168.1.123.</div>'
      + '<ol class="steps">' + (d.fix||[]).map(s=>'<li>'+s+'</li>').join('') + '</ol></div>';
  }
  document.querySelectorAll('button').forEach(b => b.disabled = !online);
  return online;
}

async function census(){
  if (!online) return;
  const d = await api('census');
  const el = $('#census');
  if (d.error){ el.innerHTML = '<span class="sub">'+d.error+'</span>'; return; }
  el.innerHTML =
    '<div class="counts">'
    + '<div class="n" style="color:var(--ok)">'+d.up+'<small>talking</small></div>'
    + '<div class="n" style="color:var(--down)">'+d.down+'<small>down</small></div>'
    + '<div class="n">'+d.total+'<small>total</small></div></div>'
    + '<div class="grid">' + d.devices.map(u =>
        '<div class="u '+u.state+'"><b>'+u.device+'</b><span>'+u.state+'</span></div>'
      ).join('') + '</div>'
    + '<div class="note">'+d.note+'</div>';
  log('census: '+d.up+' up, '+d.down+' down of '+d.total);
}

document.addEventListener('click', async e => {
  const b = e.target.closest('button[data-c]');
  if (!b || b.disabled) return;
  const name = b.dataset.c;
  const dry = await api('control', {name});
  if (!confirm(dry.would_send + '\n\n' + dry.effect + '\n\nReaches: ' + dry.reaches + '\n\nSend it?')) {
    log('cancelled ' + name); return;
  }
  b.disabled = true;
  const r = await api('control', {name, confirm:'1'});
  b.disabled = false;
  log((r.ok ? 'OK   ' : 'FAIL ') + name + '  HTTP ' + r.http + '  ' + r.effect);
  setTimeout(census, 1500);
});

(async () => { if (await ping()) census(); })();
setInterval(async () => { if (await ping()) census(); }, 30000);
</script>
"""


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        p = u.path

        if p in ("/", "/index.html"):
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        try:
            if p == "/api/ping":
                return self._json(bas.op_ping())
            if p == "/api/census":
                return self._json(bas.op_census(
                    q.get("network", "config/Drivers/NovarnetNetwork/")))
            if p == "/api/browse":
                return self._json(bas.op_browse(q.get("path", "config/")))
            if p == "/api/read":
                return self._json(bas.op_read(q["path"]))
            if p == "/api/controls":
                return self._json(bas.op_controls())
            if p == "/api/control":
                return self._json(bas.op_control(
                    q["name"], confirm=q.get("confirm") in ("1", "true")))
        except Exception as e:
            return self._json({"error": str(e)}, 500)

        self._json({"error": "not found"}, 404)

    def log_message(self, *a):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8770
    srv = HTTPServer(("127.0.0.1", port), Handler)
    print("UA Theater panel dashboard  ->  http://127.0.0.1:%d" % port)
    print("stop with:  pkill -f 'dashboard.py'")
    srv.serve_forever()


if __name__ == "__main__":
    main()
