"""Criativos do Natal do Rafa (PIL). Saída em ../natal/criativos/"""
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "..", "natal", "criativos"); os.makedirs(OUT, exist_ok=True)
FR = "/tmp/package/files/fraunces-latin-{}-{}.woff"
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
def fr(sz, w=600, it=False): return ImageFont.truetype(FR.format(w, "italic" if it else "normal"), sz)
def it_(sz, w="SemiBold"): return ImageFont.truetype(INTER.format(w), sz)

PINE, PINE2, CREAM, GOLD, GOLD2, INK, MUT, RED = (16,41,31), (36,80,61), (251,247,239), (233,185,73), (246,222,154), (27,42,34), (94,107,98), (179,38,30)
img = lambda c: Image.open(os.path.join(D, "img", c + ".webp")).convert("RGB")
def brl(n): return f"{int(round(n)):,}".replace(",", ".")


def fundo(W, H):
    bg = Image.new("RGB", (W, H), PINE)
    glow = Image.new("L", (W, H), 0); g = ImageDraw.Draw(glow)
    g.ellipse((int(W*.35), -int(H*.35), int(W*1.4), int(H*.45)), fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    bg = Image.composite(Image.new("RGB", (W, H), PINE2), bg, glow)
    # grão leve
    random.seed(3); n = Image.effect_noise((W, H), 18).convert("RGB")
    return Image.blend(bg, n, 0.035)


def fio(base, y0=26, n=None):
    W = base.width; n = n or 13; passo = W / (n - 1)
    pts = [(int(i*passo), y0 + (26 if i % 2 else 0)) for i in range(n)]
    luz = Image.new("RGB", base.size, (0, 0, 0)); dl = ImageDraw.Draw(luz)
    d = ImageDraw.Draw(base)
    d.line(pts, fill=(42, 59, 49), width=4)
    cores = [GOLD, GOLD2, (201, 79, 61), GOLD, (156, 201, 168)]
    for i, (x, y) in enumerate(pts):
        c = cores[i % 5]
        dl.ellipse((x-34, y-10, x+34, y+62), fill=c)
    luz = luz.filter(ImageFilter.GaussianBlur(26))
    import numpy as np
    out = Image.fromarray(np.clip(np.asarray(base).astype(int) + np.asarray(luz).astype(int)*0.55, 0, 255).astype("uint8"))
    d = ImageDraw.Draw(out)
    for i, (x, y) in enumerate(pts):
        c = cores[i % 5]
        d.rounded_rectangle((x-8, y, x+8, y+12), 3, fill=(42, 59, 49))
        d.ellipse((x-13, y+10, x+13, y+48), fill=c)
        d.ellipse((x-6, y+16, x-1, y+26), fill=(255, 250, 235))
    return out


def cobre(im, w, h):
    r = max(w/im.width, h/im.height); im = im.resize((int(im.width*r)+1, int(im.height*r)+1), Image.LANCZOS)
    x, y = (im.width-w)//2, (im.height-h)//2
    return im.crop((x, y, x+w, y+h))


def contem(im, w, h, bg=(255, 255, 255)):
    c = Image.new("RGB", (w, h), bg); t = im.copy(); t.thumbnail((w, h), Image.LANCZOS)
    c.paste(t, ((w-t.width)//2, (h-t.height)//2)); return c


def arred(im, r):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width-1, im.height-1), r, fill=255); return m


def texto(d, xy, s, f, fill, maxw=None, lh=1.12, anchor="la"):
    """Quebra por palavras se maxw; devolve y final."""
    x, y = xy
    linhas = [s]
    if maxw:
        linhas, cur = [], ""
        for w in s.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= maxw: cur = t
            else: linhas.append(cur); cur = w
        linhas.append(cur)
    for l in linhas:
        d.text((x, y), l, font=f, fill=fill, anchor=anchor); y += int(f.size*lh)
    return y


def rodape(d, W, y, cta="Monte o seu em 30 segundos"):
    d.rounded_rectangle((60, y, W-60, y+96), 26, fill=GOLD)
    d.text((W//2, y+48), cta + "  →", font=it_(36, "Bold"), fill=INK, anchor="mm")
    d.text((W//2, y+124), "natal.ofertadorafa.com.br", font=it_(30, "SemiBold"), fill=GOLD2, anchor="mm")


# ------------------------------------------------------------------ B: kit com preço
def kit(nome, W, H, titulo1, titulo2, itens, total, mais=None, faixa=""):
    base = fio(fundo(W, H)); d = ImageDraw.Draw(base)
    story = H > 1500
    y = 118 if not story else 380
    d.text((60, y), "NATAL DO RAFA  ·  EXEMPLO DE KIT " + faixa, font=it_(26, "Bold"), fill=GOLD)
    y = texto(d, (60, y+46), titulo1, fr(68, 600), CREAM, W-120, 1.08)
    y = texto(d, (60, y), titulo2, fr(68, 500, True), GOLD2, W-120, 1.08) + 26
    # cartão creme com os itens
    cols = 3 if len(itens) > 4 else 2
    rows = math.ceil(len(itens)/cols)
    pad, gap = 28, 18
    cw = W - 120; tw = (cw - 2*pad - gap*(cols-1)) // cols
    avail = H - y - (215 if not story else 470)
    tw = min(tw, (avail - 2*pad - rows*80 - (rows-1)*gap - 104) // rows)
    th = tw + 80
    ch = pad*2 + rows*th + (rows-1)*gap + 104
    gx = (cw - (cols*tw + (cols-1)*gap)) // 2
    card = Image.new("RGB", (cw, ch), CREAM); dc = ImageDraw.Draw(card)
    for i, (code, rot, preco) in enumerate(itens):
        nrow = min(cols, len(itens) - (i//cols)*cols)
        off = (cols - nrow)*(tw+gap)//2
        cx = gx + off + (i % cols)*(tw+gap); cy = pad + (i//cols)*(th+gap)
        ph = contem(img(code), tw, tw) if code in CONTEM else cobre(img(code), tw, tw)
        card.paste(ph, (cx, cy), arred(ph, 18))
        dc.text((cx+2, cy+tw+10), rot, font=it_(24, "SemiBold"), fill=INK)
        dc.text((cx+2, cy+tw+42), "R$ " + brl(preco), font=fr(32, 700), fill=PINE)
    yy = ch - 104 + 8
    dc.line((pad, yy, cw-pad, yy), fill=(228, 220, 203), width=2)
    dc.text((pad, yy+52), "Total aproximado" + (f"  (+ {mais})" if mais else ""), font=it_(28, "SemiBold"), fill=MUT, anchor="lm")
    dc.text((cw-pad, yy+52), "R$ " + brl(total), font=fr(52, 700), fill=RED, anchor="rm")
    base.paste(card, (60, y), arred(card, 34))
    y += ch + 16
    d.text((W//2, y), "Preços aproximados do Mercado Livre, conferidos em nov/2026", font=it_(22, "Medium"), fill=(175, 194, 181), anchor="mt")
    rodape(d, W, y + 40)
    base.convert("RGB").save(os.path.join(OUT, nome), quality=90)


# ------------------------------------------------------------------ A: a dor
def dor(nome, W, H):
    base = fundo(W, H); story = H > 1500
    ph_h = int(H*0.50)
    foto = cobre(img("628600-MLB119040119405_102026"), W, ph_h)
    base.paste(foto, (0, 0))
    grad = Image.new("L", (1, 256)); [grad.putpixel((0, i), int(255*max(0, (i-90)/166)**1.4)) for i in range(256)]
    grad = grad.resize((W, ph_h)); base.paste(Image.new("RGB", (W, ph_h), PINE), (0, 0), grad)
    base = fio(base); d = ImageDraw.Draw(base)
    y = ph_h - 130
    for s, cor in [("Árvore torta.", CREAM), ("Pisca-pisca queimado.", CREAM), ("Bola que não combina.", CREAM)]:
        d.text((60, y), s, font=fr(70, 600), fill=cor); y += 82
    y += 24
    y = texto(d, (60, y), "Diga quanto quer gastar. A gente monta o seu Natal inteiro.", fr(54, 500, True), GOLD2, W-120, 1.15) + 20
    d.text((60, y), "Árvore, luzes, bolas, ponteira e saia que combinam,", font=it_(30, "Medium"), fill=(201, 214, 204))
    d.text((60, y+42), "de R$ 200 a R$ 1.200, só item bem avaliado.", font=it_(30, "Medium"), fill=(201, 214, 204))
    rodape(d, W, H - (420 if story else 230))
    base.save(os.path.join(OUT, nome), quality=90)


# ------------------------------------------------------------------ C: comparação
def comp(nome, W, H):
    base = fio(fundo(W, H)); d = ImageDraw.Draw(base); story = H > 1500
    y = 160 if not story else 300
    d.text((60, y), "NATAL DO RAFA", font=it_(26, "Bold"), fill=GOLD)
    y = texto(d, (60, y+46), "Montar a decoração de Natal:", fr(64, 600), CREAM, W-120)
    y += 26
    cw = (W - 120 - 24)//2; chh = 600
    for i, (tit, cor, fg, linhas) in enumerate([
        ("Sozinho", (36, 58, 47), CREAM, ["14 abas abertas", "2 horas comparando", "Árvore grande, pisca curto", "Bola que não combina", "Estoura o orçamento"]),
        ("No Natal do Rafa", CREAM, INK, ["4 perguntas", "30 segundos", "Luzes na medida da árvore", "Cores combinando", "Cabe no seu valor"])]):
        x = 60 + i*(cw+24)
        d.rounded_rectangle((x, y, x+cw, y+chh), 30, fill=cor, outline=GOLD if i else None, width=4 if i else 0)
        d.text((x+30, y+40), tit, font=fr(40, 700), fill=GOLD2 if i == 0 else PINE)
        yy = y + 120
        for l in linhas:
            if i == 0:
                d.line((x+34, yy+20, x+54, yy+40), fill=(255, 140, 120), width=5); d.line((x+54, yy+20, x+34, yy+40), fill=(255, 140, 120), width=5)
            else:
                d.line((x+32, yy+30, x+42, yy+40), fill=(47, 125, 79), width=6); d.line((x+42, yy+40, x+60, yy+18), fill=(47, 125, 79), width=6)
            texto(d, (x+76, yy+10), l, it_(30, "SemiBold"), fg, cw-100, 1.15); yy += 98
    y += chh + 30
    # tirinha de produtos reais
    codes = ["654010-MLA120493941857_102026", "739448-MLB112438227504_062026", "862174-MLB86287188296_062025", "998248-MLA120309570453_102026", "905320-MLA100267699943_122025"]
    s = min((W - 120 - 4*14)//5, H - (420 if story else 230) - 40 - y)
    x0 = (W - (5*s + 4*14))//2
    for i, c in enumerate(codes):
        ph = cobre(img(c), s, s); base.paste(ph, (x0 + i*(s+14), y), arred(ph, 16))
    rodape(d, W, H - (420 if story else 230), "Montar meu kit agora")
    base.save(os.path.join(OUT, nome), quality=90)


CONTEM = {"806997-MLA95576811375_102025", "740675-MLB90273911708_082025"}
K200 = [("727033-MLB119658685590_112026", "Árvore 1,20 m", 78), ("739448-MLB112438227504_062026", "300 LEDs, 30 m", 59),
        ("622871-MLA117626329708_102026", "Ponteira estrela", 26), ("905320-MLA100267699943_122025", "Saia da árvore", 30)]
K500 = [("654010-MLA120493941857_102026", "Árvore 1,80 m", 206), ("739448-MLB112438227504_062026", "300 LEDs, 30 m", 59),
        ("862174-MLB86287188296_062025", "Kit 100 bolas", 143), ("998248-MLA120309570453_102026", "Ponteira com LED", 40),
        ("905320-MLA100267699943_122025", "Saia da árvore", 30)]
K1200 = [("694060-MLA120376227981_102026", "Árvore 2,40 m", 485), ("739448-MLB112438227504_062026", "2× 300 LEDs", 118),
         ("862174-MLB86287188296_062025", "Kit 100 bolas", 143), ("628600-MLB119040119405_102026", "Saia tapete", 79),
         ("743390-MLB116559261888_092026", "Guirlanda c/ LED", 70), ("962431-MLB116269020056_092026", "6 laços de veludo", 45)]
for W, H, suf in [(1080, 1350, "F"), (1080, 1920, "S")]:
    kit(f"natal_B200_{suf}.jpg", W, H, "Natal completo", "por menos de R$ 200.", K200, sum(p for *_, p in K200), faixa="ATÉ R$ 200")
    kit(f"natal_B500_{suf}.jpg", W, H, "Árvore de 1,80 m", "com tudo, até R$ 500.", K500, sum(p for *_, p in K500), faixa="ATÉ R$ 500")
    kit(f"natal_B1200_{suf}.jpg", W, H, "A casa toda no clima", "por até R$ 1.200.", K1200, 1148, mais="festão, mesa e sala", faixa="ATÉ R$ 1.200")
    dor(f"natal_A_{suf}.jpg", W, H)
    comp(f"natal_C_{suf}.jpg", W, H)
print("ok")
