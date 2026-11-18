"""Natal do Rafa — contador de visitantes (só biblioteca padrão do Python).
Recebe os eventos do site em POST /api/hit e serve os dados do painel em GET /api/painel?k=CHAVE.
Guarda só cidade/UF aproximada (pelo IP), aparelho, página, produto e anúncio de origem. O IP não é gravado."""
import json, os, sqlite3, threading, time, urllib.request, hashlib, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get('PORT', 8787))
KEY = os.environ.get('PAINEL_KEY', '')
DB = os.environ.get('DB', '/data/visitas.db')
TZ_OFFSET = -3 * 3600  # Fortaleza
ONLINE_S = 60

lock = threading.Lock()
KITS = os.path.join(os.path.dirname(DB) or '.', 'kits')
os.makedirs(KITS, exist_ok=True)
_rate = {}  # hash do IP -> [timestamps] (limite de kits salvos por hora)


def limpar_kits():
    lim = time.time() - 86400 * 60
    for f in os.listdir(KITS):
        p = os.path.join(KITS, f)
        try:
            if os.path.getmtime(p) < lim: os.remove(p)
        except OSError:
            pass


def vigia_codigo():
    """Se o server.py mudar (git pull), sai: o Docker (restart: unless-stopped) sobe a versão nova."""
    me = os.path.abspath(__file__)
    t0 = os.path.getmtime(me)
    while True:
        time.sleep(30)
        try:
            if os.path.getmtime(me) != t0:
                print('server.py mudou, reiniciando', flush=True); os._exit(0)
        except OSError:
            pass

con = sqlite3.connect(DB, check_same_thread=False)
con.execute('''CREATE TABLE IF NOT EXISTS ev(
  ts REAL, sid TEXT, tipo TEXT, pagina TEXT, produto TEXT, cidade TEXT, uf TEXT,
  aparelho TEXT, origem TEXT, anuncio TEXT)''')
con.execute('CREATE INDEX IF NOT EXISTS ev_ts ON ev(ts)')
con.execute('CREATE TABLE IF NOT EXISTS sess(sid TEXT PRIMARY KEY, ultimo REAL, pagina TEXT, cidade TEXT, uf TEXT, aparelho TEXT, anuncio TEXT)')
con.commit()

_geo = {}  # cache em memória: hash do IP -> (cidade, uf)


def geo(ip):
    h = hashlib.sha256(ip.encode()).hexdigest()[:16]
    if h in _geo:
        return _geo[h]
    cid, uf = '', ''
    if ip and not ip.startswith(('10.', '172.', '192.168.', '127.')):
        try:
            with urllib.request.urlopen(f'http://ip-api.com/json/{ip}?fields=status,city,region&lang=pt-BR', timeout=3) as r:
                d = json.load(r)
            if d.get('status') == 'success':
                cid, uf = d.get('city', ''), d.get('region', '')
        except Exception:
            pass
    _geo[h] = (cid, uf)
    if len(_geo) > 20000:
        _geo.clear()
    return cid, uf


def aparelho(ua):
    ua = ua or ''
    if 'iPhone' in ua: return 'iPhone'
    if 'iPad' in ua: return 'iPad'
    if 'Android' in ua: return 'Android'
    if 'Windows' in ua: return 'Windows'
    if 'Mac OS' in ua: return 'Mac'
    return 'Outro'


def clip(s, n=120):
    return re.sub(r'[\x00-\x1f]', '', str(s or ''))[:n]


def inicio_do_dia():
    agora = time.time()
    return agora - ((agora + TZ_OFFSET) % 86400)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _send(self, code, body, ctype, cache='no-store'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', cache)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def salvar_kit(self):
        import base64, secrets
        n = int(self.headers.get('Content-Length', 0))
        if n <= 0 or n > 1_200_000:
            return self._json(413, {})
        ip = (self.headers.get('X-Forwarded-For') or self.client_address[0]).split(',')[0].strip()
        h = hashlib.sha256(ip.encode()).hexdigest()[:16]; agora = time.time()
        with lock:
            lst = [t for t in _rate.get(h, []) if t > agora - 3600]
            if len(lst) >= 40:
                return self._json(429, {})
            lst.append(agora); _rate[h] = lst
            if len(_rate) > 50000: _rate.clear()
        try:
            d = json.loads(self.rfile.read(n))
            img = d.get('img', '')
            img = base64.b64decode(img.split(',', 1)[-1])
            kit = d.get('kit') or {}
            assert img[:3] == b'\xff\xd8\xff' and len(img) < 900_000
            itens = [{'id': clip(i.get('id'), 60), 'q': max(1, min(9, int(i.get('q', 1))))} for i in kit.get('itens', [])][:20]
            meta = {'orc': int(kit.get('orc', 0)), 'tam': clip(kit.get('tam'), 2), 'est': clip(kit.get('est'), 12),
                    'tem': [clip(x, 12) for x in (kit.get('tem') or [])][:3], 'alt': float(kit.get('alt', 1.8)),
                    'itens': itens, 'total': int(kit.get('total', 0)), 'titulo': clip(kit.get('titulo'), 120),
                    'resumo': clip(kit.get('resumo'), 300)}
        except Exception:
            return self._json(400, {})
        kid = secrets.token_hex(4)
        open(os.path.join(KITS, kid + '.jpg'), 'wb').write(img)
        json.dump(meta, open(os.path.join(KITS, kid + '.json'), 'w'), ensure_ascii=False)
        if secrets.randbelow(50) == 0: limpar_kits()
        return self._json(200, {'id': kid})

    def ver_kit(self, resto):
        import html
        m = re.fullmatch(r'([0-9a-f]{8})(\.jpg|\.json)?', resto)
        if not m:
            return self._json(404, {})
        kid, ext = m.group(1), m.group(2) or ''
        base = os.path.join(KITS, kid)
        if not os.path.exists(base + '.json'):
            return self._redir('/')
        if ext == '.jpg':
            return self._send(200, open(base + '.jpg', 'rb').read(), 'image/jpeg', 'public, max-age=2592000')
        meta = json.load(open(base + '.json'))
        if ext == '.json':
            return self._json(200, meta)
        host = clip(self.headers.get('X-Forwarded-Host') or self.headers.get('Host') or 'natal.ofertadorafa.com.br', 80)
        url = f'https://{host}/api/k/{kid}'
        dest = f'/?kit={kid}'
        e = lambda x: html.escape(str(x), quote=True)
        pag = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>{e(meta.get('titulo') or 'Meu kit de Natal')}</title>
<meta property="og:type" content="website"><meta property="og:site_name" content="Natal do Rafa">
<meta property="og:title" content="{e(meta.get('titulo') or 'Meu kit de Natal')}">
<meta property="og:description" content="{e(meta.get('resumo') or 'Monte o seu kit de Natal no orçamento')}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(url)}.jpg"><meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1080"><meta property="og:image:height" content="1350">
<meta name="twitter:card" content="summary_large_image">
<meta http-equiv="refresh" content="0;url={e(dest)}"></head>
<body><script>location.replace({json.dumps(dest)})</script><a href="{e(dest)}">Ver o kit</a></body></html>'''
        return self._send(200, pag.encode(), 'text/html; charset=utf-8', 'public, max-age=300')

    def do_HEAD(self):
        return self.do_GET()

    def _redir(self, to):
        self.send_response(302); self.send_header('Location', to); self.end_headers()

    def do_POST(self):
        if self.path.startswith('/api/kit'):
            return self.salvar_kit()
        if not self.path.startswith('/api/hit'):
            return self._json(404, {})
        try:
            n = min(int(self.headers.get('Content-Length', 0)), 4000)
            d = json.loads(self.rfile.read(n) or b'{}')
        except Exception:
            return self._json(400, {})
        tipo = d.get('t')
        if tipo not in ('view', 'ping', 'click', 'quiz'):
            return self._json(400, {})
        sid = clip(d.get('sid'), 40)
        if not sid:
            return self._json(400, {})
        ip = (self.headers.get('X-Forwarded-For') or self.client_address[0]).split(',')[0].strip()
        now = time.time()
        with lock:
            row = con.execute('SELECT cidade, uf FROM sess WHERE sid=?', (sid,)).fetchone()
        cid, uf = row if row else geo(ip)
        ap = aparelho(self.headers.get('User-Agent'))
        pag, prod = clip(d.get('p')), clip(d.get('prod'), 60)
        origem, anuncio = clip(d.get('src'), 40), clip(d.get('ad'), 80)
        with lock:
            con.execute('INSERT INTO sess VALUES(?,?,?,?,?,?,?) ON CONFLICT(sid) DO UPDATE SET ultimo=excluded.ultimo, pagina=excluded.pagina',
                        (sid, now, pag, cid, uf, ap, anuncio))
            if tipo != 'ping':
                con.execute('INSERT INTO ev VALUES(?,?,?,?,?,?,?,?,?,?)', (now, sid, tipo, pag, prod, cid, uf, ap, origem, anuncio))
            con.commit()
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/k/'):
            return self.ver_kit(self.path[7:].split('?')[0])
        if not self.path.startswith('/api/painel'):
            return self._json(404, {})
        from urllib.parse import urlparse, parse_qs
        k = parse_qs(urlparse(self.path).query).get('k', [''])[0]
        if not KEY or k != KEY:
            return self._json(403, {'erro': 'chave inválida'})
        now, hoje = time.time(), inicio_do_dia()
        with lock:
            online = con.execute('SELECT sid, pagina, cidade, uf, aparelho, anuncio, ultimo FROM sess WHERE ultimo>? ORDER BY ultimo DESC',
                                 (now - ONLINE_S,)).fetchall()
            q = lambda sql, *a: con.execute(sql, a).fetchone()[0]
            visitantes = q("SELECT COUNT(DISTINCT sid) FROM ev WHERE ts>? AND tipo='view'", hoje)
            views = q("SELECT COUNT(*) FROM ev WHERE ts>? AND tipo='view'", hoje)
            cliques = q("SELECT COUNT(*) FROM ev WHERE ts>? AND tipo='click'", hoje)
            quem_clicou = q("SELECT COUNT(DISTINCT sid) FROM ev WHERE ts>? AND tipo='click'", hoje)
            kits = q("SELECT COUNT(DISTINCT sid) FROM ev WHERE ts>? AND tipo='quiz'", hoje)
            faixas = con.execute("SELECT produto, COUNT(DISTINCT sid) n FROM ev WHERE ts>? AND tipo='quiz' GROUP BY produto ORDER BY n DESC", (hoje,)).fetchall()
            ultimos = con.execute('SELECT ts, tipo, pagina, produto, cidade, uf, aparelho, anuncio FROM ev ORDER BY ts DESC LIMIT 60').fetchall()
            cidades = con.execute("SELECT cidade, uf, COUNT(DISTINCT sid) n FROM ev WHERE ts>? AND cidade!='' GROUP BY cidade, uf ORDER BY n DESC LIMIT 10", (hoje,)).fetchall()
            produtos = con.execute("SELECT produto, COUNT(*) n FROM ev WHERE ts>? AND tipo='click' GROUP BY produto ORDER BY n DESC", (hoje,)).fetchall()
            anuncios = con.execute("SELECT anuncio, COUNT(DISTINCT sid) v, SUM(tipo='click') c FROM ev WHERE ts>? AND anuncio!='' GROUP BY anuncio ORDER BY v DESC LIMIT 12", (hoje,)).fetchall()
            con.execute('DELETE FROM sess WHERE ultimo<?', (now - 86400 * 3,))
            con.commit()
        self._json(200, {
            'agora': now,
            'online': [dict(zip(['sid', 'pagina', 'cidade', 'uf', 'aparelho', 'anuncio', 'ultimo'], r)) for r in online],
            'hoje': {'visitantes': visitantes, 'paginas': views, 'cliques': cliques, 'quem_clicou': quem_clicou, 'kits': kits},
            'ultimos': [dict(zip(['ts', 'tipo', 'pagina', 'produto', 'cidade', 'uf', 'aparelho', 'anuncio'], r)) for r in ultimos],
            'cidades': [dict(zip(['cidade', 'uf', 'n'], r)) for r in cidades],
            'produtos': [dict(zip(['produto', 'n'], r)) for r in produtos],
            'faixas': [dict(zip(['faixa', 'n'], r)) for r in faixas],
            'anuncios': [dict(zip(['anuncio', 'visitantes', 'cliques'], r)) for r in anuncios],
        })


if __name__ == '__main__':
    threading.Thread(target=vigia_codigo, daemon=True).start()
    print(f'visitas na porta {PORT}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), H).serve_forever()
