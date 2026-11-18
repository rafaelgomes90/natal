#!/usr/bin/env python3
"""Gera o site estático Natal do Rafa a partir de produtos.json.

Saída: produtos.js, index.html, sitemap.xml, robots.txt.  Rode:  python3 build.py
O quiz (assets/quiz.js) monta o kit no navegador com os produtos de produtos.js.
"""
import json, html, os

BASE = "https://natal.ofertadorafa.com.br"
PIXEL = "4651558238447028"
V = "3"  # suba quando mudar CSS/JS (cache de 7 dias)
ROOT = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(ROOT, "produtos.json"), encoding="utf-8"))
for _p in P:
    if os.path.exists(os.path.join(ROOT, "img", _p["id"] + ".webp")): _p["imagem"] = "/img/" + _p["id"] + ".webp"

CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "config.json")) else {}
GRUPO = CFG.get("grupo_whatsapp", "").strip()

e = lambda s: html.escape(str(s), quote=True)
def brl(n): return f"{int(round(n)):,}".replace(",", ".")
def nota(n): return f"{n:.1f}".replace(".", ",")

PAPEIS = [("arvore", "Árvores", "Do cantinho de 1,20 m à de 2,40 m pra pé-direito alto."),
          ("luzes", "Pisca-pisca e luzes", "Regra de bolso: uns 150 LEDs por metro de árvore."),
          ("bolas", "Bolas e enfeites", "Kits com cores pra escolher no próprio anúncio."),
          ("ponteira", "Ponteiras", "A estrela do topo."),
          ("saia", "Saias de árvore", "Escondem o pé e fecham o visual."),
          ("festao", "Festões", None), ("lacos", "Laços", None), ("destaque", "Bolas de destaque", None),
          ("guirlanda", "Guirlandas de porta", None), ("janela", "Luz de janela", None),
          ("mesa", "Mesa da ceia", None), ("almofadas", "Sala", None), ("papai", "Peças de destaque", None)]
CAT = [("arvore",), ("luzes", "janela"), ("bolas", "destaque"), ("ponteira", "saia", "festao", "lacos"),
       ("guirlanda", "mesa", "almofadas", "papai")]
CAT_NOME = ["Árvores", "Luzes", "Bolas", "Enfeites da árvore", "Pra casa toda"]
CAT_ID = ["arvores", "luzes", "bolas", "enfeites", "casa"]

ICON_EXT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>'
STAR = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="m12 2 3 6.6 7.2.8-5.4 4.9 1.5 7.1L12 17.8 5.7 21.4l1.5-7.1L1.8 9.4 9 8.6z"/></svg>'
LOGO = open(os.path.join(ROOT, "favicon.svg"), encoding="utf-8").read().replace('<svg xmlns="http://www.w3.org/2000/svg"', '<svg aria-hidden="true"')


def head(title, desc, path, og_img):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE}{path}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:site_name" content="Natal do Rafa">
<meta property="og:image" content="{e(og_img)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#10291F">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://http2.mlstatic.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v={V}">
<script>
!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','{PIXEL}');fbq('track','PageView');
</script>
<noscript><img height="1" width="1" style="display:none" alt="" src="https://www.facebook.com/tr?id={PIXEL}&ev=PageView&noscript=1"></noscript>
</head>"""


def ml(p, inner, cls="", origem=""):
    return (f'<a class="{cls}" href="{e(p["link"])}" target="_blank" rel="noopener sponsored" '
            f'data-ml="{p["id"]}" data-origem="{origem}">{inner}</a>')


def card(p):
    selo = f'<span class="selo">{e(p["selo"])}</span>' if p.get("selo") else ""
    return f"""<article class="card">
  {ml(p, f'<img src="{e(p["imagem"])}" alt="{e(p["nome"])}" loading="lazy" decoding="async">' + selo, "foto", "catalogo-foto")}
  <div class="corpo">
    <h3>{ml(p, e(p['nome']), "", "catalogo-nome")}</h3>
    <p class="aval">{STAR}<b>{nota(p['nota'])}</b> <span>({brl(p['avaliacoes'])} avaliações)</span></p>
    <p class="preco">por volta de <b>R$ {brl(p['precoAprox'])}</b></p>
    {ml(p, 'Comprar no Mercado Livre ' + ICON_EXT, "ml", "catalogo-botao")}
  </div>
</article>"""


def grupo_bloco():
    if not GRUPO: return ""
    return f"""<section class="sec"><div class="wrap estreito">
  <div class="grupo">
    <div class="grupo-ic" aria-hidden="true"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.4.8 3.2.7.5-.1 1.5-.6 1.8-1.2.2-.6.2-1.1.1-1.2l-.1-.1Z"/></svg></div>
    <div class="grupo-tx">
      <h3>Não é hora de comprar?</h3>
      <p>Entra no grupo <b>Oferta do Rafa</b> no WhatsApp: cupons e quedas de preço do Mercado Livre todo dia. Se a árvore que você gostou baixar de preço até o Natal, você fica sabendo.</p>
    </div>
    <a class="btn grupo-btn" href="{e(GRUPO)}" target="_blank" rel="noopener" data-grupo="home">Entrar no grupo grátis</a>
  </div>
</div></section>"""


# luzinhas do fio no topo do hero (SVG decorativo)
def fio():
    pts, bulbs = [], []
    cores = ["#E9B949", "#F2D58A", "#C94F3D", "#E9B949", "#9CC9A8"]
    for i in range(61):
        x = 20 + i * 50
        y = 12 + (14 if i % 2 else 0)
        pts.append(f"{x},{y}")
        c = cores[i % len(cores)]
        bulbs.append(f'<g class="lamp" style="--d:{(i * 0.37) % 3:.2f}s"><rect x="{x-3}" y="{y}" width="6" height="5" rx="1" fill="#2A3B31"/><ellipse cx="{x}" cy="{y+12}" rx="5.5" ry="8" fill="{c}"/></g>')
    return (f'<svg class="fio" viewBox="0 0 3040 58" preserveAspectRatio="xMidYMin slice" aria-hidden="true">'
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="#2A3B31" stroke-width="2"/>{"".join(bulbs)}</svg>')


# ---------------------------------------------------------------- produtos.js
with open(os.path.join(ROOT, "produtos.js"), "w", encoding="utf-8") as f:
    f.write("// GERADO por build.py a partir de produtos.json — edite o JSON e rode python3 build.py\n")
    f.write("window.PRODUTOS = " + json.dumps(P, ensure_ascii=False, separators=(",", ":")) + ";\n")

# ---------------------------------------------------------------- catálogo
cat_html = ""
for nome, papeis, cid in zip(CAT_NOME, CAT, CAT_ID):
    itens = [p for p in P if p["papel"] in papeis]
    if p_ord := sorted(itens, key=lambda p: (papeis.index(p["papel"]), p.get("altura", 0), p["precoAprox"])):
        cat_html += f'<h3 class="cat-title" id="{cid}">{nome}</h3>\n<div class="grid">\n' + "\n".join(card(p) for p in p_ord) + "\n</div>\n"
chips = "".join(f'<a class="chipa" href="#{cid}">{n}</a>' for n, cid in zip(CAT_NOME, CAT_ID))

FAQ = [("Por que cada item tem seu próprio botão?", "Porque cada produto é vendido por uma loja diferente dentro do Mercado Livre. Você abre um por um, confere o preço do dia e coloca no carrinho do ML. No fim paga tudo junto lá."),
       ("Os preços são esses mesmo?", "São aproximados, conferidos no Mercado Livre. Preço muda todo dia (às vezes cai com cupom), então o valor que vale é o que aparece no anúncio na hora da compra."),
       ("Chega antes do Natal?", "Depende da sua cidade e da loja. O prazo aparece no anúncio antes de pagar. Pra garantir, compre até o começo de dezembro."),
       ("Quantas bolas e luzes eu preciso?", "Um jeito simples de calcular: uns 150 LEDs e umas 40 bolas por metro de árvore. O montador já faz essa conta e coloca a quantidade certa no kit."),
       ("E a voltagem do pisca-pisca?", "Em vários anúncios você escolhe 127V ou 220V. Confira a da sua tomada antes de finalizar."),
       ("É seguro comprar pelo link?", "Sim. A compra é feita no próprio Mercado Livre, com Compra Garantida. A gente só indica e monta a combinação.")]
faq = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in FAQ)

og = BASE + "/og.jpg"
index = head("Natal do Rafa — sua decoração de Natal completa, dentro do seu orçamento",
             "Diga quanto quer gastar e o tamanho da sala: montamos a árvore, as luzes, as bolas e o resto com produtos bem avaliados do Mercado Livre.",
             "/", og) + f"""
<body>
<header class="hdr"><div class="wrap">
  <a class="logo" href="/" aria-label="Natal do Rafa">{LOGO}<span>Natal do Rafa</span></a>
  <nav class="menu" aria-label="Menu"><a href="#montar">Montar kit</a><a href="#catalogo">Produtos</a><a class="hide-sm" href="#duvidas">Dúvidas</a></nav>
</div></header>
<section class="hero">{fio()}<div class="wrap">
  <p class="eyebrow">Natal 2026 · produtos do Mercado Livre</p>
  <h1>Quanto você quer gastar no Natal? <em>A gente monta a decoração inteira.</em></h1>
  <p class="sub">Árvore, pisca-pisca, bolas, ponteira e saia que combinam entre si e cabem no seu bolso. Só itens bem avaliados.</p>
</div></section>
<main>
<section class="quiz-wrap" id="montar"><div class="wrap estreito">
  <div class="quiz" id="quiz" aria-live="polite">
    <div class="q-prog"><i id="q-bar"></i></div>
    <div id="q-corpo"></div>
  </div>
  <div id="kit" hidden></div>
</div></section>

<section class="sec alt" id="catalogo"><div class="wrap">
  <div class="sec-title"><h2>Prefere escolher peça por peça?</h2><p>Tudo o que o montador usa, com a nota de quem já comprou.</p></div>
  <nav class="chips" aria-label="Categorias">{chips}</nav>
  {cat_html}
  <p class="disc">Preços aproximados. O valor final, o frete e os cupons aparecem no Mercado Livre.</p>
</div></section>
{grupo_bloco()}
<section class="sec" id="duvidas"><div class="wrap estreito">
  <div class="sec-title"><h2>Dúvidas</h2></div>
  <div class="faq">{faq}</div>
</div></section>
</main>
<footer><div class="in">
  <p>Natal do Rafa © 2026 · Indicamos produtos vendidos no Mercado Livre. Ao comprar pelos nossos links podemos receber uma comissão, sem custo extra pra você. Preços e estoque mudam todo dia; o valor final é o do Mercado Livre.</p>
  <a href="#montar">Montar kit</a> · <a href="#catalogo">Produtos</a> · <a href="/privacidade.html">Política de privacidade</a>
</div></footer>
<script src="/produtos.js?v={V}"></script>
<script src="/assets/app.js?v={V}"></script>
<script src="/assets/quiz.js?v={V}"></script>
</body>
</html>
"""
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(index)

open(os.path.join(ROOT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    f"  <url><loc>{BASE}/</loc></url>\n</urlset>\n")
open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
print("ok:", len(P), "produtos")
