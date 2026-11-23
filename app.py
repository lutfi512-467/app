"""
WebWindow - Proxy Edition (Flask)
Jalankan:  python app.py   lalu buka http://127.0.0.1:5000

Variabel lingkungan opsional:
  HOST=127.0.0.1   (default; pakai 0.0.0.0 hanya jika kamu paham risikonya)
  PORT=5000
"""
import html as htmllib
import os
import re
from urllib.parse import quote, urljoin, urlparse

import requests
from flask import Flask, Response, jsonify, redirect, render_template, request

app = Flask(__name__, static_folder=None)
SESSIONS = {}  # sid -> {"s": requests.Session, "shield": bool}

UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36")

# ---------- Daftar blokir iklan (domain) ----------
BLOCK_DOMAINS = {
    "doubleclick.net", "googlesyndication.com", "googleadservices.com",
    "google-analytics.com", "googletagmanager.com", "adnxs.com", "popads.net",
    "popcash.net", "propellerads.com", "exoclick.com", "juicyads.com",
    "trafficjunky.com", "adsterra.com", "highperformanceformat.com",
    "onclickads.net", "clickadu.com", "hilltopads.net", "mgid.com",
    "taboola.com", "outbrain.com", "revcontent.com", "adcash.com",
    "adskeeper.com", "admaven.com", "a-ads.com", "amazon-adsystem.com",
    "criteo.com", "criteo.net", "rubiconproject.com", "pubmatic.com",
    "openx.net", "adform.net", "smartadserver.com", "moatads.com",
    "adsrvr.org", "yieldmo.com", "tiktokv-ads.com", "pangleglobal.com",
    "ads-twitter.com", "facebook.net", "hotjar.com", "monetag.com",
    "richpartners.com", "ad-maven.com", "pushwoosh.com", "tsyndicate.com",
}
BLOCK_PREFIX = ("ads.", "ad.", "adserver.", "banner.", "banners.", "track.", "pagead.")

CSS = """<style>ins.adsbygoogle,[id*="google_ads"],[class*="adsbygoogle"],
iframe[src*="doubleclick"],iframe[src*="googlesyndication"],[id^="ad-"],[id^="ads-"],
[class^="ad-"],[class*=" ad-"],[class*="ad-banner"],[class*="adbox"],[class*="popup-ad"],
[id*="popunder"],.ad,.ads,.advert,.advertisement,.banner-ad{display:none!important}</style>"""

# Disuntikkan ke setiap halaman HTML: arahkan fetch/XHR/link/atribut dinamis lewat proxy.
JS = r"""<script>(function(){
var SID="__SID__",PFX="__PFX__",SCH="__SCH__",SH=__SH__,MINE='/x/'+SID+'/';
var ATTRS={src:1,href:1,action:1,poster:1,'data-src':1,'data-original':1,'data-lazy-src':1,formaction:1};
function fx(u){
  try{
    if(u==null)return u;
    u=String(u);
    if(!u||/^(#|javascript:|mailto:|tel:|blob:|data:|about:)/i.test(u))return u;
    if(u.indexOf('//')===0)u=SCH+':'+u;
    var a=new URL(u,location.href);
    if(a.origin===location.origin){
      if(a.pathname.indexOf(MINE)===0)return u;
      return PFX+a.pathname+a.search+a.hash;
    }
    if(/^https?:$/.test(a.protocol))
      return MINE+a.protocol.slice(0,-1)+'/'+a.host+a.pathname+a.search+a.hash;
  }catch(e){}
  return u;
}
/* fetch / XHR / beacon */
var of=window.fetch;
if(of)window.fetch=function(i,o){
  try{if(typeof i==='string'||i instanceof URL)i=fx(i);else if(i&&i.url)i=new Request(fx(i.url),i)}catch(e){}
  return of.call(this,i,o)};
var oo=XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open=function(m,u){arguments[1]=fx(u);return oo.apply(this,arguments)};
if(navigator.sendBeacon){var ob=navigator.sendBeacon.bind(navigator);
  navigator.sendBeacon=function(u,d){return ob(fx(u),d)}}
/* popup & service worker */
var wo=window.open;
window.open=SH?function(){return null}:function(u,t,f){return wo.call(window,fx(u),t,f)};
if(navigator.serviceWorker){
  try{navigator.serviceWorker.register=function(){return Promise.reject(new Error('sw off'))}}catch(e){}}
/* history */
['pushState','replaceState'].forEach(function(k){
  var o=history[k];history[k]=function(s,t,u){
    try{if(u!=null)u=fx(u)}catch(e){}
    try{return o.call(this,s,t,u)}catch(e){}}});
/* setAttribute + property setters */
var sa=Element.prototype.setAttribute;
Element.prototype.setAttribute=function(n,v){
  try{if(typeof n==='string'&&ATTRS[n.toLowerCase()]&&typeof v==='string')v=fx(v)}catch(e){}
  return sa.call(this,n,v)};
function hook(proto,prop){
  try{var d=Object.getOwnPropertyDescriptor(proto,prop);
    if(!d||!d.set)return;
    Object.defineProperty(proto,prop,{get:d.get,configurable:true,enumerable:d.enumerable,
      set:function(v){d.set.call(this,typeof v==='string'?fx(v):v)}})}catch(e){}}
[[HTMLImageElement,'src'],[HTMLScriptElement,'src'],[HTMLLinkElement,'href'],
 [HTMLIFrameElement,'src'],[HTMLAnchorElement,'href'],[HTMLSourceElement,'src'],
 [HTMLMediaElement,'src'],[HTMLFormElement,'action'],[HTMLEmbedElement,'src'],
 [HTMLObjectElement,'data'],[HTMLTrackElement,'src']].forEach(function(p){hook(p[0].prototype,p[1])});
/* elemen yang disisipkan lewat innerHTML dsb. */
function fixNode(n){
  if(!n||n.nodeType!==1)return;
  var list=[n].concat([].slice.call(n.querySelectorAll('[src],[href],[action],[poster],[data-src]')));
  list.forEach(function(e){
    for(var k in ATTRS){
      var v=e.getAttribute&&e.getAttribute(k);
      if(v&&v.indexOf(MINE)!==0){var nv=fx(v);if(nv!==v)sa.call(e,k,nv)}}})}
try{new MutationObserver(function(ms){
  ms.forEach(function(m){[].forEach.call(m.addedNodes,fixNode)})
}).observe(document,{childList:true,subtree:true})}catch(e){}
/* klik & submit */
document.addEventListener('click',function(e){
  var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;
  var h=a.getAttribute('href');
  if(!h||/^(#|javascript:|mailto:|tel:|blob:|data:)/i.test(h))return;
  if(a.target==='_blank'&&SH)a.target='_self';else if(a.target==='_top'||a.target==='_parent')a.target='_self';
  if(h.indexOf(MINE)!==0)sa.call(a,'href',fx(a.href))},true);
document.addEventListener('submit',function(e){
  var f=e.target;
  try{f.target='_self';sa.call(f,'action',fx(f.getAttribute('action')||location.href))}catch(x){}},true);
})();</script>"""

ATTR_Q = re.compile(r"""(\s(?:href|src|action|formaction|poster|data|data-src|data-original|data-lazy-src)\s*=\s*)(["'])(.*?)\2""", re.I | re.S)
ATTR_U = re.compile(r"""(\s(?:href|src|action|formaction|poster|data-src)\s*=\s*)([^\s"'>=`][^\s"'>]*)""", re.I)
SRCSET = re.compile(r"""(\s(?:srcset|data-srcset|imagesrcset)\s*=\s*)(["'])(.*?)\2""", re.I | re.S)
STYLE_BLOCK = re.compile(r"(<style\b[^>]*>)(.*?)(</style>)", re.I | re.S)
STYLE_ATTR = re.compile(r"""(\sstyle\s*=\s*)(["'])(.*?)\2""", re.I | re.S)
BASE_TAG = re.compile(r"<base\b[^>]*>", re.I)
BASE_HREF = re.compile(r"""href\s*=\s*["']?([^"'\s>]+)""", re.I)
INTEGRITY = re.compile(r"""\s(?:integrity|crossorigin)\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""", re.I)
META_CSP = re.compile(r"""<meta\b[^>]*http-equiv\s*=\s*["']?content-security-policy[^>]*>""", re.I)
META_REFERRER = re.compile(r"""<meta\b[^>]*name\s*=\s*["']?referrer["']?[^>]*>""", re.I)
META_REFRESH = re.compile(r"""<meta\b[^>]*http-equiv\s*=\s*["']?refresh[^>]*>""", re.I)
REFRESH_URL = re.compile(r"""(url\s*=\s*["']?)([^"'>;]+)""", re.I)
CSS_URL = re.compile(r"""url\(\s*(["']?)(.*?)\1\s*\)""", re.I | re.S)
CSS_IMPORT = re.compile(r"""(@import\s+)(["'])(.*?)\2""", re.I)
SKIP = ("#", "data:", "javascript:", "mailto:", "tel:", "blob:", "about:")


def blocked(host):
    host = (host or "").split(":")[0].lower()
    if host.startswith(BLOCK_PREFIX):
        return True
    return any(host == d or host.endswith("." + d) for d in BLOCK_DOMAINS)


def sess(sid):
    return SESSIONS.setdefault(sid, {"s": requests.Session(), "shield": True})


def to_proxy(sid, absu):
    p = urlparse(absu)
    if p.scheme not in ("http", "https"):
        return absu
    out = "/x/%s/%s/%s%s" % (sid, p.scheme, p.netloc, p.path or "/")
    if p.query:
        out += "?" + p.query
    if p.fragment:
        out += "#" + p.fragment
    return out


def rewrite_url(v, sid, base, shield):
    """Kembalikan URL versi proxy, atau None bila tidak perlu diubah."""
    v = (v or "").strip()
    if not v or v.lower().startswith(SKIP) or v.startswith("/x/%s/" % sid):
        return None
    absu = urljoin(base, v)
    p = urlparse(absu)
    if p.scheme not in ("http", "https"):
        return None
    if shield and blocked(p.netloc):
        return "about:blank"
    return to_proxy(sid, absu)


def rewrite_css(css, sid, base, shield):
    def u(m):
        q, v = m.group(1), m.group(2)
        new = rewrite_url(v, sid, base, shield)
        if new is None:
            return m.group(0)
        if new == "about:blank":
            new = "data:,"
        return "url(%s%s%s)" % (q, new, q)

    def imp(m):
        new = rewrite_url(m.group(3), sid, base, shield)
        if new is None or new == "about:blank":
            return m.group(0)
        return m.group(1) + m.group(2) + new + m.group(2)

    css = CSS_URL.sub(u, css)
    return CSS_IMPORT.sub(imp, css)


def rewrite_m3u8(text, sid, base, shield):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            new = rewrite_url(s, sid, base, shield)
            line = new if new and new != "about:blank" else line
        elif 'URI="' in line:
            line = re.sub(r'URI="([^"]*)"',
                          lambda m: 'URI="%s"' % (rewrite_url(m.group(1), sid, base, shield) or m.group(1)),
                          line)
        out.append(line)
    return "\n".join(out)


def rewrite_html(html, sid, base_url, shield):
    # <base href> dipakai sebagai dasar resolusi URL, lalu dibuang
    bm = BASE_TAG.search(html)
    if bm:
        hm = BASE_HREF.search(bm.group(0))
        if hm:
            base_url = urljoin(base_url, htmllib.unescape(hm.group(1)))
    html = BASE_TAG.sub("", html)
    html = INTEGRITY.sub("", html)
    html = META_CSP.sub("", html)
    html = META_REFERRER.sub("", html)

    def attr_q(m):
        new = rewrite_url(htmllib.unescape(m.group(3)), sid, base_url, shield)
        if new is None:
            return m.group(0)
        return m.group(1) + m.group(2) + htmllib.escape(new, quote=True) + m.group(2)

    def attr_u(m):
        new = rewrite_url(htmllib.unescape(m.group(2)), sid, base_url, shield)
        if new is None:
            return m.group(0)
        return m.group(1) + '"' + htmllib.escape(new, quote=True) + '"'

    def srcset(m):
        parts = []
        for cand in re.split(r",\s+", htmllib.unescape(m.group(3))):
            cand = cand.strip()
            if not cand:
                continue
            bits = cand.split(None, 1)
            new = rewrite_url(bits[0], sid, base_url, shield)
            if new == "about:blank":
                continue
            bits[0] = new or bits[0]
            parts.append(" ".join(bits))
        return m.group(1) + m.group(2) + htmllib.escape(", ".join(parts), quote=True) + m.group(2)

    def style_attr(m):
        if "url(" not in m.group(3).lower():
            return m.group(0)
        css = rewrite_css(htmllib.unescape(m.group(3)), sid, base_url, shield)
        return m.group(1) + m.group(2) + htmllib.escape(css, quote=False).replace(m.group(2), "&quot;" if m.group(2) == '"' else "&#39;") + m.group(2)

    def refresh(m):
        def r(mm):
            new = rewrite_url(htmllib.unescape(mm.group(2)).strip(), sid, base_url, shield)
            return mm.group(1) + (htmllib.escape(new, quote=True) if new else mm.group(2))
        return REFRESH_URL.sub(r, m.group(0))

    html = STYLE_BLOCK.sub(lambda m: m.group(1) + rewrite_css(m.group(2), sid, base_url, shield) + m.group(3), html)
    html = STYLE_ATTR.sub(style_attr, html)
    html = SRCSET.sub(srcset, html)
    html = ATTR_Q.sub(attr_q, html)
    html = ATTR_U.sub(attr_u, html)
    html = META_REFRESH.sub(refresh, html)

    p = urlparse(base_url)
    js = (JS.replace("__SID__", sid)
            .replace("__PFX__", "/x/%s/%s/%s" % (sid, p.scheme, p.netloc))
            .replace("__SCH__", p.scheme)
            .replace("__SH__", "true" if shield else "false"))
    block = (CSS if shield else "") + js
    m = re.search(r"<head[^>]*>", html, re.I)
    return html[:m.end()] + block + html[m.end():] if m else block + html


def decode_html(raw, ctype):
    m = re.search(r"charset=([\w-]+)", ctype, re.I)
    enc = m.group(1) if m else None
    if not enc:
        mm = re.search(rb"""<meta[^>]+charset\s*=\s*["']?([\w-]+)""", raw[:4096], re.I)
        enc = mm.group(1).decode("ascii", "ignore") if mm else "utf-8"
    try:
        return raw.decode(enc, "replace")
    except LookupError:
        return raw.decode("utf-8", "replace")


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/shield")
def api_shield():
    d = request.get_json(silent=True) or {}
    sid = re.sub(r"\W", "", str(d.get("sid", "")))[:16]
    if sid:
        sess(sid)["shield"] = bool(d.get("on", True))
    return jsonify(ok=True)


@app.route("/x/<sid>/<scheme>/<path:rest>",
           methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def proxy(sid, scheme, rest):
    sid = re.sub(r"\W", "", sid)[:16]
    if scheme not in ("http", "https"):
        return Response("skema tidak didukung", 400)
    st = sess(sid)
    host = rest.split("/", 1)[0]
    url = "%s://%s" % (scheme, rest)
    if request.query_string:
        url += "?" + request.query_string.decode("utf-8", "ignore")

    if st["shield"] and blocked(host):
        return Response("", 204)

    headers = {
        "User-Agent": UA,
        "Accept": request.headers.get("Accept", "*/*"),
        "Accept-Language": "id,en;q=0.8",
        "Referer": "%s://%s/" % (scheme, host),
    }
    for h in ("Range", "X-Requested-With", "Authorization", "If-None-Match", "If-Modified-Since"):
        if h in request.headers:
            headers[h] = request.headers[h]
    data = None
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        data = request.get_data()
        headers["Content-Type"] = request.headers.get("Content-Type", "application/x-www-form-urlencoded")
        headers["Origin"] = "%s://%s" % (scheme, host)

    try:
        r = st["s"].request(request.method, url, headers=headers, data=data,
                            allow_redirects=False, timeout=(10, 30), stream=True)
    except requests.RequestException as e:
        return Response("<meta charset='utf-8'><h3 style='font-family:sans-serif'>Gagal membuka halaman</h3>"
                        "<p style='font-family:sans-serif'>%s</p>" % htmllib.escape(str(e)),
                        502, mimetype="text/html")

    if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
        code = r.status_code if r.status_code in (307, 308) else 302
        return redirect(to_proxy(sid, urljoin(url, r.headers["Location"])), code)

    ctype = r.headers.get("Content-Type", "")
    low = ctype.lower()
    if request.method != "HEAD" and "text/html" in low:
        html = decode_html(r.content, ctype)
        out = rewrite_html(html, sid, url, st["shield"])
        return Response(out.encode("utf-8"), r.status_code, content_type="text/html; charset=utf-8")
    if request.method != "HEAD" and "text/css" in low:
        css = decode_html(r.content, ctype)
        out = rewrite_css(css, sid, url, st["shield"])
        return Response(out.encode("utf-8"), r.status_code, content_type="text/css; charset=utf-8")
    if request.method != "HEAD" and ("mpegurl" in low or url.split("?")[0].lower().endswith(".m3u8")):
        out = rewrite_m3u8(r.content.decode("utf-8", "replace"), sid, url, st["shield"])
        return Response(out.encode("utf-8"), r.status_code, content_type=ctype or "application/vnd.apple.mpegurl")

    keep = {}
    for h in ("Content-Type", "Content-Disposition", "Content-Range", "Accept-Ranges", "ETag", "Last-Modified"):
        if h in r.headers:
            keep[h] = r.headers[h]
    if "Content-Length" in r.headers and "Content-Encoding" not in r.headers:
        keep["Content-Length"] = r.headers["Content-Length"]
    return Response(r.iter_content(65536), r.status_code, headers=keep)


@app.route("/<path:p>", methods=["GET", "POST"])
def fallback(p):
    """Link root-relatif (/foo.js) -> arahkan ke situs asal berdasar Referer."""
    ref = request.headers.get("Referer", "")
    m = re.search(r"/x/(\w+)/(https?)/([^/?#]+)", ref)
    if not m:
        return Response("Not found", 404)
    target = "/x/%s/%s/%s/%s" % (m.group(1), m.group(2), m.group(3), p)
    if request.query_string:
        target += "?" + request.query_string.decode("utf-8", "ignore")
    return redirect(target, 307)


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), threaded=True)
