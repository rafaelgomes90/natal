"""Plano B — 'O cupom que não estoura' (15 s, 1080x1920, 30 fps).
Natal passado: cupom fiscal longo que estoura o orçamento. Este Natal: cupom do Natal do Rafa,
itens com foto em pontilhado térmico, total R$ 478, troco R$ 22, carimbo DENTRO DO ORÇAMENTO.
Saída: video/planoB_natal.mp4 + video/contato_b.png"""
import os, math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "video"); os.makedirs(OUT, exist_ok=True)
IMG = os.path.join(D, "..", "img")
FR = "/tmp/package/files/fraunces-latin-{}-{}.woff"
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono{}.ttf"
def fr(sz, w=600, it=False): return ImageFont.truetype(FR.format(w, "italic" if it else "normal"), sz)
def inter(sz, w="SemiBold"): return ImageFont.truetype(INTER.format(w), sz)
def mono(sz, b=False): return ImageFont.truetype(MONO.format("-Bold" if b else ""), sz)

W, H, FPS, DUR = 1080, 1920, 30, 15.0
N = int(FPS * DUR)
RED, RED2, PAPER, INK, INK2, GOLD, CREAM, STAMP = (122, 22, 18), (158, 34, 26), (246, 241, 230), (38, 34, 32), (120, 112, 104), (233, 185, 73), (251, 247, 239), (196, 32, 28)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(x): x = clamp(x); return x*x*(3-2*x)
def eob(x): x = clamp(x); c = 1.9; return 1 + (c+1)*(x-1)**3 + c*(x-1)**2
def seg(t, a, b): return clamp((t-a)/(b-a))

# ---------- fundo vermelho com vinheta e listras sutis (papel de presente) ----------
def fundo():
    bg = Image.new("RGB", (W, H), RED)
    gl = Image.new("L", (W, H), 0); g = ImageDraw.Draw(gl)
    g.ellipse((-200, 300, W+200, H-200), fill=150); gl = gl.filter(ImageFilter.GaussianBlur(240))
    bg = Image.composite(Image.new("RGB", (W, H), RED2), bg, gl)
    lst = Image.new("RGB", (W, H), (0, 0, 0)); dl = ImageDraw.Draw(lst)
    for x in range(-H, W, 90): dl.line([(x, 0), (x + H, H)], fill=(18, 0, 0), width=26)
    return Image.fromarray(np.clip(np.asarray(bg).astype(int) - np.asarray(lst).astype(int) // 2, 0, 255).astype("uint8"))
BG = fundo()
random.seed(5)
GRAOS = [Image.effect_noise((W, H), 24).convert("RGB") for _ in range(6)]

# ---------- cupom ----------
PW = 860; PX = (W - PW) // 2; SLOT = 1580     # papel sai da fenda e sobe
LH = 58
F_M = mono(38); F_MB = mono(40, True); F_MBIG = mono(54, True); F_MS = mono(30)

def termico(cid, s=112):
    im = Image.open(os.path.join(IMG, cid + ".webp")).convert("RGB")
    w, h = im.size; k = s / max(w, h); im = im.resize((max(1, int(w*k)), max(1, int(h*k))), Image.LANCZOS)
    card = Image.new("RGB", (s, s), (255, 255, 255)); card.paste(im, ((s-im.width)//2, (s-im.height)//2))
    g = ImageOps.autocontrast(card.convert("L"), cutoff=2).point(lambda v: min(255, int(v * 1.08)))
    d = g.convert("1")  # Floyd–Steinberg = cara de impressora térmica
    out = Image.new("RGB", (s, s), PAPER); out.paste(Image.new("RGB", (s, s), INK), mask=ImageOps.invert(d.convert("L")))
    return out

def linha_pts(a, b, f=None):
    f = f or F_M; d = ImageDraw.Draw(Image.new("L", (1, 1))); alvo = PW - 72
    s = a + "." + b
    while d.textlength(a + "." * (len(s) - len(a) - len(b) + 1) + b, font=f) <= alvo: s = a + "." * (len(s) - len(a) - len(b) + 1) + b
    return s

# conteúdo dos dois cupons: lista de (altura, desenhar(draw, papel, y))
def cupom_ruim():
    L = []
    def txt(s, f=F_M, cor=INK, centro=False, h=LH):
        def dr(dd, pap, y):
            x = (PW - dd.textlength(s, font=f))/2 if centro else 36
            dd.text((x, y + 8), s, font=f, fill=cor)
        L.append((h, dr))
    txt("LOJAS DIVERSAS", F_MB, centro=True); txt("cupom nº 2025", F_MS, INK2, True, 46); txt("-" * 40, F_MS, INK2, True, 40)
    for a, b in [("PISCA-PISCA", "39,90"), ("PISCA (DE NOVO)", "39,90"), ("BOLAS AVULSAS", "89,90"),
                 ("MAIS BOLAS*", "74,90"), ("ARVORE TORTA", "289,00"), ("FITA, COLA, ETC", "78,40")]:
        txt(linha_pts(a, b))
    txt("*nao combinou com as outras", F_MS, INK2, h=46)
    txt("-" * 40, F_MS, INK2, True, 40)
    txt(linha_pts("TOTAL", "R$ 612,00", F_MBIG), F_MBIG, INK, h=84)
    return L

KIT = [("arvore-180-800-galhos", "ARVORE 1,80 M", "206,00"), ("cordao-300-leds-30m", "300 LEDS 30 M", "59,00"),
       ("bolas-kit-100", "KIT 100 BOLAS", "143,00"), ("ponteira-led", "PONTEIRA LED", "40,00"), ("saia-papai-noel", "SAIA DA ARVORE", "30,00")]
THUMB = {cid: termico(cid) for cid, *_ in KIT}
def cupom_bom():
    L = []
    def txt(s, f=F_M, cor=INK, centro=False, h=LH):
        def dr(dd, pap, y):
            x = (PW - dd.textlength(s, font=f))/2 if centro else 36
            dd.text((x, y + 8), s, font=f, fill=cor)
        L.append((h, dr))
    txt("NATAL DO RAFA", F_MB, centro=True); txt("ORCAMENTO: R$ 500,00", F_M, INK, True, 50)
    txt("sala media · classico", F_MS, INK2, True, 44); txt("-" * 40, F_MS, INK2, True, 40)
    for cid, nome, preco in KIT:
        def dr(dd, pap, y, cid=cid, nome=nome, preco=preco):
            pap.paste(THUMB[cid], (36, y + 8))
            dd.text((172, y + 20), nome, font=F_M, fill=INK)
            dd.text((172, y + 68), "R$ " + preco, font=F_MB, fill=INK)
            dd.text((PW - 36 - dd.textlength("x1", font=F_MS), y + 72), "x1", font=F_MS, fill=INK2)
        L.append((132, dr))
    txt("-" * 40, F_MS, INK2, True, 40)
    txt(linha_pts("TOTAL", "R$ 478,00", F_MBIG), F_MBIG, INK, h=84)
    txt(linha_pts("TROCO", "R$ 22,00", F_MB), F_MB, INK, h=60)
    txt("links no Mercado Livre", F_MS, INK2, True, 46)
    return L

def render_papel(linhas, n_vis, frac):
    """papel com as primeiras n_vis linhas inteiras + fração da próxima (impressão)."""
    alturas = [h for h, _ in linhas]
    vis = linhas[:n_vis]; hh = sum(alturas[:n_vis]) + (alturas[n_vis] * frac if n_vis < len(linhas) else 0) + 30
    hh = int(hh)
    pap = Image.new("RGB", (PW, max(hh, 40)), PAPER); dd = ImageDraw.Draw(pap)
    y = 20
    for h, dr in linhas[:n_vis + (1 if n_vis < len(linhas) else 0)]:
        dr(dd, pap, y); y += h
    # serrilhado no topo
    for x in range(0, PW, 24): dd.polygon([(x, 0), (x + 12, 10), (x + 24, 0)], fill=RED)
    # fibras do papel
    return pap

def sombra(img, off=(10, 16), r=18, a=110):
    sh = Image.new("L", (img.width + 80, img.height + 80), 0)
    ImageDraw.Draw(sh).rectangle((40, 40, 40 + img.width, 40 + img.height), fill=a)
    return sh.filter(ImageFilter.GaussianBlur(r))

RUIM, BOM = cupom_ruim(), cupom_bom()
# tempos de impressão
T1 = [0.55 + k * 0.19 for k in range(len(RUIM))]         # rápido, nervoso
T2 = [4.15 + k * 0.62 for k in range(len(BOM))]          # calmo, um item por vez
T2[-3:] = [T2[-4] + .55, T2[-4] + 1.1, T2[-4] + 1.5]
T_ESTOURO, T_CAI, T_TITULO2 = 2.35, 3.05, 3.55
T_CARIMBO = T2[-1] + .55
T_CTA = 12.4
SUB_CTA = "você diz quanto quer gastar, o site monta"

def papel_em(linhas, tempos, t, dur_linha=.16):
    n = 0; frac = 0.
    for k, tk in enumerate(tempos):
        if t >= tk + dur_linha: n = k + 1
        elif t >= tk: n = k; frac = (t - tk) / dur_linha; break
        else: break
    return render_papel(linhas, n, frac), n

def carimbo(texto, sub, ang, esc):
    f1, f2 = inter(84, "Black"), inter(34, "Bold")
    dd0 = ImageDraw.Draw(Image.new("L", (1, 1))); w = int(max(dd0.textlength(texto, font=f1), dd0.textlength(sub, font=f2)) + 90); h = 200
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w - 6, h - 6), 18, outline=STAMP + (235,), width=8)
    d.text(((w - d.textlength(texto, font=f1))/2, 18), texto, font=f1, fill=STAMP + (235,))
    d.text(((w - d.textlength(sub, font=f2))/2, 128), sub, font=f2, fill=STAMP + (235,))
    # tinta falhada
    rnd = np.random.default_rng(3); a = np.asarray(im).copy()
    mask = rnd.random(a.shape[:2]) < .13; a[mask, 3] = (a[mask, 3] * .25).astype("uint8"); im = Image.fromarray(a)
    im = im.resize((max(1, int(w*esc)), max(1, int(h*esc))), Image.LANCZOS)
    return im.rotate(ang, resample=Image.BICUBIC, expand=True)

F_T1 = fr(96, 600); F_T1i = fr(96, 500, True); F_URL = inter(46, "Bold"); F_SM = inter(38, "Medium")
def tc(d, y, s, f, cor, a=1.0, base=RED):
    if a <= 0: return
    c = tuple(int(base[i] + (cor[i]-base[i])*a) for i in range(3))
    d.text(((W - d.textlength(s, font=f))/2, y), s, font=f, fill=c)

def frame(i):
    t = i / FPS
    im = BG.copy(); d = ImageDraw.Draw(im)
    # fenda da impressora
    if t < T_CTA:
        d.rounded_rectangle((PX - 40, SLOT - 6, PX + PW + 40, SLOT + 46), 23, fill=(28, 10, 8))
        d.rounded_rectangle((PX - 20, SLOT + 8, PX + PW + 20, SLOT + 22), 7, fill=(8, 2, 2))
    # tremor da impressora enquanto imprime
    imprimindo = any(tk <= t < tk + .16 for tk in T1 + T2)
    jit = (random.Random(i).randint(-2, 2) if imprimindo else 0)
    # ---- cupom ruim ----
    if t < T_TITULO2:
        a = ease(seg(t, .05, .4))
        tc(d, 330, "Natal passado:", F_T1, CREAM, a)
        pap, n = papel_em(RUIM, T1, t)
        cai = ease(seg(t, T_CAI, T_TITULO2)) if t > T_CAI else 0
        y = SLOT - pap.height + int(cai * 1300); ang = cai * -14
        if t > T_ESTOURO:
            k = eob(seg(t, T_ESTOURO, T_ESTOURO + .22))
            ca = carimbo("ESTOUROU", "R$ 112 acima do orçamento", 9, 1.6 - .6 * k)
            pap = pap.convert("RGBA"); pap.alpha_composite(ca, ((PW - ca.width)//2, max(0, pap.height - ca.height - 150)))
            pap = pap.convert("RGB")
        if cai > 0:
            pr = pap.convert("RGBA").rotate(ang, resample=Image.BICUBIC, expand=True)
            im.paste(pr, (PX - (pr.width - PW)//2, y), pr)
        else:
            im.paste(Image.new("RGB", (1, 1)), (0, 0))
            sh = sombra(pap); im.paste(Image.new("RGB", sh.size, (30, 0, 0)), (PX - 30, y - 24), sh)
            im.paste(pap, (PX + jit, y))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((PX - 40, SLOT - 6, PX + PW + 40, SLOT + 46), 23, fill=(28, 10, 8))
    # ---- cupom bom ----
    else:
        a = ease(seg(t, T_TITULO2, T_TITULO2 + .35)) * (1 - ease(seg(t, T_CTA - .2, T_CTA + .2)))
        tc(d, 330, "Este Natal:", F_T1i, GOLD, a)
        pap, n = papel_em(BOM, T2, t)
        if t > T_CARIMBO:
            k = eob(seg(t, T_CARIMBO, T_CARIMBO + .22))
            ca = carimbo("DENTRO DO", "ORÇAMENTO · sobrou R$ 22", -7, 1.7 - .7 * k)
            pap = pap.convert("RGBA"); pap.alpha_composite(ca, (PW - ca.width - 20, max(0, pap.height - ca.height - 190)))
            pap = pap.convert("RGB")
        # CTA: cupom é arrancado, sobe e encolhe pra esquerda
        rasga = ease(seg(t, T_CTA, T_CTA + .55))
        esc = 1 - .4 * rasga
        pw2, ph2 = int(PW * esc), int(pap.height * esc)
        p2 = pap.resize((pw2, ph2), Image.LANCZOS) if esc < .999 else pap
        if rasga > 0:
            p2 = p2.convert("RGBA").rotate(-4 * rasga, resample=Image.BICUBIC, expand=True)
        x = int(PX + (W - pw2)/2 - PX) if rasga == 0 else int((W - p2.width)/2)
        y = int((SLOT - pap.height) * (1 - rasga) + (540) * rasga)
        sh = sombra(p2 if p2.mode == "RGB" else p2.convert("RGB")); im.paste(Image.new("RGB", sh.size, (30, 0, 0)), (x - 30, y - 24), sh)
        if p2.mode == "RGBA": im.paste(p2, (x, y), p2)
        else: im.paste(p2, (x + jit, y))
        d = ImageDraw.Draw(im)
        if rasga < 1:
            d.rounded_rectangle((PX - 40, SLOT - 6 + int(rasga * 400), PX + PW + 40, SLOT + 46 + int(rasga * 400)), 23, fill=(28, 10, 8))
        if t >= T_CTA:
            a2 = ease(seg(t, T_CTA + .3, T_CTA + .7))
            # faixa de título por cima
            tc(d, 300, "Monte o seu Natal", fr(84, 600), CREAM, a2)
            tc(d, 392, "no orçamento.", fr(84, 500, True), GOLD, a2)
            a3 = ease(seg(t, T_CTA + .7, T_CTA + 1.1))
            bw, bh, by = 840, 124, 1440
            cb = tuple(int(RED[k] + (GOLD[k]-RED[k])*a3) for k in range(3))
            d.rounded_rectangle(((W-bw)/2, by, (W+bw)/2, by+bh), 62, fill=cb)
            tc(d, by + 34, "natal.ofertadorafa.com.br", F_URL, RED, a3, cb)
            tc(d, by + 160, SUB_CTA, F_SM, CREAM, a3)
    im = Image.blend(im, GRAOS[i % 6], 0.03)
    return im

# ---------- áudio ----------
SR = 44100
def audio():
    n = int(SR * DUR); out = np.zeros(n); rng = np.random.default_rng(2)
    def add(sig, t0, g=1.):
        a = int(t0 * SR); b = min(n, a + len(sig)); out[a:b] += sig[:b-a] * g
    def x_(L): return np.arange(int(L * SR)) / SR
    # ambiente de loja: ruído grave bem baixo
    out += np.convolve(rng.standard_normal(n), np.ones(500)/500, "same") * .05
    # impressora térmica: motor de passo (zumbido com degraus) + atrito do papel, por linha
    def linha_impressa(L=.16, f=620):
        x = x_(L)
        passo = np.sign(np.sin(2*np.pi*f*x)) * (0.6 + .4*np.sign(np.sin(2*np.pi*38*x)))
        atrito = np.convolve(rng.standard_normal(len(x)), [1, -1], "same") * .5
        e = np.minimum(1, x/.006) * np.minimum(1, (L - x)/.02)
        return (passo * .22 + atrito * .35) * e
    for k, tk in enumerate(T1): add(linha_impressa(.16, 700 + k*8), tk, .5)
    for k, tk in enumerate(T2): add(linha_impressa(.16, 560), tk, .45)
    # carimbo ruim: baque + sopro descendente "ihh"
    def baque(t0, g=1.):
        x = x_(.35); s = np.sin(2*np.pi*(90 - 40*x)*x) * np.exp(-x*14) + rng.standard_normal(len(x)) * np.exp(-x*60) * .4
        add(s, t0, g)
    baque(T_ESTOURO + .18, .9)
    x = x_(.9); f = 420 * np.exp(-x*1.1)
    add(np.sin(2*np.pi*np.cumsum(f)/SR) * np.minimum(1, x/.03) * np.exp(-x*2.2) * .18, T_ESTOURO + .35)
    x = x_(.9); f = 330 * np.exp(-x*1.1)
    add(np.sin(2*np.pi*np.cumsum(f)/SR) * np.minimum(1, x/.03) * np.exp(-x*2.2) * .16, T_ESTOURO + .62)
    # papel caindo: whoosh
    x = x_(.6); w = rng.standard_normal(len(x)); w = np.convolve(w, np.ones(20)/20, "same")
    add(w * np.sin(np.pi * x / .6) * .5, T_CAI)
    # sino da "virada" pro Natal bom
    x = x_(1.6)
    for f, g in [(1318.5, .12), (1975.5, .07)]:
        add((np.sin(2*np.pi*f*x) + .4*np.sin(2*np.pi*f*2.7*x)*np.exp(-x*6)) * np.exp(-x*2.4) * g, T_TITULO2)
    # "plim" suave a cada item com foto (nota sobe)
    notas = [659.25, 783.99, 880.0, 987.77, 1174.66]
    for k in range(5):
        x = x_(.8); f = notas[k]
        add((np.sin(2*np.pi*f*x) + .3*np.sin(2*np.pi*2*f*x)) * np.minimum(1, x/.004) * np.exp(-x*5) * .09, T2[4 + k] + .16)
    # carimbo bom: baque + caixa registradora (sino duplo) + acorde
    baque(T_CARIMBO + .18, 1.)
    x = x_(1.4)
    for d_, f in [(0, 2093.0), (.09, 2637.0)]:
        add(np.sin(2*np.pi*f*x) * np.exp(-x*3.2) * .12 + np.sin(2*np.pi*f*2.76*x) * np.exp(-x*8) * .05, T_CARIMBO + .3 + d_)
    # rasgo do papel: ruído com filtro descendo
    x = x_(.45); r = rng.standard_normal(len(x))
    corte = np.linspace(.6, .05, len(x)); y = np.zeros_like(r); acc = 0.
    for k in range(len(r)): acc += corte[k] * (r[k] - acc); y[k] = acc
    add(y * (np.abs(np.sin(2*np.pi*31*x)) * .6 + .4) * np.exp(-x*3) * .9, T_CTA)
    # acorde final quente
    x = x_(2.4)
    ac = sum(np.sin(2*np.pi*f*x) * np.exp(-x*1.3) for f in [196.0, 246.94, 293.66, 392.0, 493.88])
    add(ac * np.minimum(1, x/.08) * .07, T_CTA + .5)
    add(np.sin(2*np.pi*49*x) * np.minimum(1, x/.3) * np.exp(-x*1.2) * .22, T_CTA + .5)
    # reverb curto (loja)
    L = int(.9*SR); ir = rng.standard_normal(L) * np.exp(-np.arange(L)/SR*5.5); ir[0] = 1
    from numpy.fft import rfft, irfft
    M = 1 << (n + L).bit_length(); wet = irfft(rfft(out, M) * rfft(ir, M), M)[:n]
    mix = out * .85 + wet / np.max(np.abs(wet)) * np.max(np.abs(out)) * .25
    mix = mix / np.max(np.abs(mix)) * .89
    fade = np.ones(n); fade[-int(.4*SR):] = np.linspace(1, 0, int(.4*SR)); mix *= fade
    p = os.path.join(OUT, "sfx_b.wav")
    with wave.open(p, "wb") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((mix*32767).astype(np.int16).tobytes())
    return p

if __name__ == "__main__":
    wav = audio()
    mp4 = os.path.join(OUT, "planoB_natal.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    marcas = [int(1.6*FPS), int(2.8*FPS), int(3.3*FPS), int(6.5*FPS), int(10.6*FPS), int(14.0*FPS)]
    thumbs = []
    for i in range(N):
        f = frame(i); ff.stdin.write(f.tobytes())
        if i in marcas: thumbs.append(f.resize((270, 480)))
    ff.stdin.close(); ff.wait()
    sheet = Image.new("RGB", (270*6 + 50, 500), (20, 6, 5))
    for k, th in enumerate(thumbs): sheet.paste(th, (10 + k*278, 10))
    sheet.save(os.path.join(OUT, "contato_b.png")); print(mp4)
