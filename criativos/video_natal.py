"""Animatic 15 s do Natal do Rafa — 'A sala que se monta sozinha'.
Saída: ../natal/criativos/video/animatic_natal.mp4 (1080x1920, 30 fps) + folha de contato.
Sem voz ainda: os textos na tela marcam onde entra cada frase do Rafael."""
import os, math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "video"); os.makedirs(OUT, exist_ok=True)
IMG = os.path.join(D, "..", "img")
FR = "/tmp/package/files/fraunces-latin-{}-{}.woff"
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
def fr(sz, w=600, it=False): return ImageFont.truetype(FR.format(w, "italic" if it else "normal"), sz)
def inter(sz, w="SemiBold"): return ImageFont.truetype(INTER.format(w), sz)

W, H, FPS, DUR = 1080, 1920, 30, 15.0
N = int(FPS * DUR)
PINE, PINE2, CREAM, GOLD, GOLD2, MUT, RED = (16,41,31), (30,66,50), (251,247,239), (233,185,73), (246,222,154), (150,170,158), (201,79,61)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(x): x = clamp(x); return x*x*(3-2*x)
def eob(x):  # ease out back
    x = clamp(x); c = 1.7; return 1 + (c+1)*(x-1)**3 + c*(x-1)**2
def seg(t, a, b): return clamp((t-a)/(b-a))
def brl(n): return f"{int(round(n)):,}".replace(",", ".")

# ---------- fundo ----------
def fundo():
    bg = Image.new("RGB", (W, H), PINE)
    glow = Image.new("L", (W, H), 0); g = ImageDraw.Draw(glow)
    g.ellipse((int(W*.1), int(H*.18), int(W*1.1), int(H*.78)), fill=140)
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    return Image.composite(Image.new("RGB", (W, H), PINE2), bg, glow)
BG = fundo()
random.seed(7)
GRAOS = [Image.effect_noise((W, H), 22).convert("RGB") for _ in range(6)]

# ---------- sala em traço fino ----------
DY = 130
FLOOR = 1380 + DY
SALA = [  # (pontos, fecha?)
    ([(60, FLOOR), (1020, FLOOR)], False),
    ([(150, FLOOR), (150, 520)], False),                       # canto da parede
    ([(680, 600), (940, 600), (940, 940), (680, 940)], True),  # janela
    ([(810, 600), (810, 940)], False), ([(680, 770), (940, 770)], False),
    ([(740, FLOOR), (740, 1350), (1010, 1350), (1010, FLOOR)], False),  # sofá
    ([(740, 1400), (1010, 1400)], False),
    ([(705, FLOOR), (705, 1385), (740, 1385)], False), ([(1045, FLOOR), (1045, 1385), (1010, 1385)], False),
]
def comprimento(p): return sum(math.dist(p[i], p[i+1]) for i in range(len(p)-1))
def parcial(p, f):
    """primeiros f (0..1) do traço"""
    tot = comprimento(p) * f; out = [p[0]]
    for i in range(len(p)-1):
        l = math.dist(p[i], p[i+1])
        if tot >= l: out.append(p[i+1]); tot -= l
        else:
            a, b = p[i], p[i+1]; k = tot/l if l else 0
            out.append((a[0]+(b[0]-a[0])*k, a[1]+(b[1]-a[1])*k)); break
    return out

# árvore: 4 camadas em zigue-zague + tronco, centrada em x=360
CX, TOP, BASE = 360, 560 + DY, 1300 + DY
def arvore_traco():
    pts = [(CX, TOP)]
    camadas = [(TOP, 720+DY, 120), (660+DY, 880+DY, 180), (820+DY, 1060+DY, 240), (990+DY, 1240+DY, 300)]
    lado = 1
    for y0, y1, half in camadas:
        pts += [(CX - half, y1), (CX - half*0.45, y1 - 30)]
    # desce pela esquerda e sobe pela direita
    esq = [(CX, TOP)]
    for y0, y1, half in camadas: esq += [(CX - half, y1), (CX - half*0.42, y1 - 34)]
    dir_ = [(CX + half*0.42, y1 - 34) for y0, y1, half in reversed(camadas)]
    dirs = []
    for y0, y1, half in reversed(camadas): dirs += [(CX + half, y1), (CX + half*0.42, y1 - 34)]
    # contorno: topo → esquerda → base → direita → topo
    contorno = esq[:-1] + [(CX - 300, 1240+DY), (CX + 300, 1240+DY)] + dirs[1:] + [(CX, TOP)]
    tronco = [(CX - 34, 1240+DY), (CX - 34, 1300+DY), (CX + 34, 1300+DY), (CX + 34, 1240+DY)]
    return contorno, tronco
ARV, TRONCO = arvore_traco()

# fio de luz em espiral sobre a árvore
def largura_em(y):
    return 40 + (y - TOP) / (1240 + DY - TOP) * 250
FIO = []
for i in range(220):
    k = i / 219; y = TOP + 70 + k * (1180 + DY - TOP - 70)
    x = CX + math.sin(k * math.pi * 7.0) * largura_em(y) * 0.82
    FIO.append((x, y))
NB = 18
BULBOS = [FIO[int(i * (len(FIO)-1) / (NB-1))] for i in range(NB)]
CORES = [GOLD, GOLD2, RED, GOLD, (156, 201, 168)]

# ---------- produtos (kit até R$ 500 = 478) ----------
KIT = [("arvore-180-800-galhos", "Árvore 1,80 m", 206), ("cordao-300-leds-30m", "300 LEDs, 30 m", 59),
       ("bolas-kit-100", "Kit 100 bolas", 143), ("ponteira-led", "Ponteira LED", 40), ("saia-papai-noel", "Saia da árvore", 30)]
FOTOS = {}
for cid, _, _ in KIT:
    im = Image.open(os.path.join(IMG, cid + ".webp")).convert("RGB")
    s = 200; w, h = im.size; k = s / max(w, h)
    im = im.resize((int(w*k), int(h*k)), Image.LANCZOS)
    card = Image.new("RGB", (s, s), (255, 255, 255)); card.paste(im, ((s-im.width)//2, (s-im.height)//2))
    FOTOS[cid] = card

# ---------- linha do tempo (s) ----------
T_QUEIMA = (0.0, 2.4)     # sala apagada + pisca queimado
T_SLIDER = (2.4, 4.4)     # quanto quer gastar → R$ 500
T_ARV    = (4.4, 7.4)     # árvore se desenha
T_LUZ    = (7.4, 10.0)    # luzes acendem uma a uma
T_KIT    = (10.0, 12.6)   # cards com preço e total
T_CTA    = (12.6, 15.0)

def texto_centro(d, y, s, fonte, cor, alpha=1.0, base=None):
    if alpha <= 0: return
    w = d.textlength(s, font=fonte)
    c = tuple(int(base[i] + (cor[i]-base[i])*alpha) for i in range(3)) if base else cor
    d.text(((W - w)/2, y), s, font=fonte, fill=c)

F_H1 = fr(92, 600); F_H1i = fr(92, 500, True); F_H2 = fr(64, 600); F_SM = inter(40, "Medium")
F_NUM = inter(120, "Bold"); F_PR = inter(44, "Bold"); F_LB = inter(34, "SemiBold"); F_URL = inter(46, "SemiBold")

def frame(i):
    t = i / FPS
    im = BG.copy(); d = ImageDraw.Draw(im)
    luz = Image.new("RGB", (W//2, H//2), (0, 0, 0)); dl = ImageDraw.Draw(luz)
    # câmera derivando (zoom lento)
    linha = (*GOLD2,)
    # --- sala ---
    a_sala = 0.55 if t < T_KIT[0] else 0.55 * (1 - seg(t, T_KIT[0], T_KIT[0] + .5)) + 0.18
    corline = tuple(int(PINE[k] + (GOLD2[k]-PINE[k]) * a_sala) for k in range(3))
    fsala = ease(seg(t, 0.0, 1.2))
    for p, fecha in SALA:
        pts = p + [p[0]] if fecha else p
        q = parcial(pts, fsala)
        if len(q) > 1: d.line(q, fill=corline, width=3)
    # --- 1. pisca queimado no canto ---
    if t < T_SLIDER[0] + 0.3:
        pisca = [(175, 560 + j*60) for j in range(10)]
        d.line(pisca, fill=(60, 80, 68), width=3)
        for j, (x, y) in enumerate(pisca):
            vivo = (j % 3 == 0) and (random.Random(int(t*14) + j).random() > 0.45) and t < 2.15
            d.ellipse((x-9, y-9, x+9, y+9), fill=GOLD if vivo else (55, 70, 60))
            if vivo: dl.ellipse((x//2-22, y//2-22, x//2+22, y//2+22), fill=GOLD)
        if 2.15 < t < 2.3:  # faísca
            dl.ellipse((175//2-40, 800//2-40, 175//2+40, 800//2+40), fill=(255, 240, 200))
        al = ease(seg(t, .3, .9)) * (1 - ease(seg(t, 2.1, 2.5)))
        texto_centro(d, 310, "Todo ano a mesma", F_H1, CREAM, al, PINE)
        texto_centro(d, 410, "novela de Natal.", F_H1i, GOLD, al, PINE)
    # --- 2. slider ---
    if T_SLIDER[0] - .1 < t < T_ARV[0] + .5:
        al = ease(seg(t, T_SLIDER[0], T_SLIDER[0]+.35)) * (1 - ease(seg(t, T_ARV[0], T_ARV[0]+.4)))
        texto_centro(d, 310, "Quanto você quer gastar?", F_H2, CREAM, al, PINE)
        x0, x1, y = 200, 880, 460
        cl = tuple(int(PINE[k] + (MUT[k]-PINE[k])*al) for k in range(3))
        d.line([(x0, y), (x1, y)], fill=cl, width=8)
        p = ease(seg(t, T_SLIDER[0]+.3, T_SLIDER[1]-.3)) * (500-200)/(1200-200)
        xp = x0 + (x1-x0) * p
        cg = tuple(int(PINE[k] + (GOLD[k]-PINE[k])*al) for k in range(3))
        d.line([(x0, y), (xp, y)], fill=cg, width=8)
        d.ellipse((xp-24, y-24, xp+24, y+24), fill=cg)
        val = 200 + p * 1000
        val = round(val / 10) * 10
        texto_centro(d, 500, f"R$ {brl(val)}", F_NUM, CREAM, al, PINE)
    # --- 3. árvore se desenha ---
    fa = ease(seg(t, T_ARV[0], T_ARV[1] - .3))
    if fa > 0:
        q = parcial(ARV, fa)
        if len(q) > 1: d.line(q, fill=GOLD2, width=5, joint="curve")
        ft = ease(seg(t, T_ARV[1]-.6, T_ARV[1]))
        q = parcial(TRONCO, ft)
        if len(q) > 1: d.line(q, fill=GOLD2, width=5)
        al = ease(seg(t, T_ARV[0]+.2, T_ARV[0]+.6)) * (1 - ease(seg(t, T_LUZ[0]-.3, T_LUZ[0])))
        texto_centro(d, 310, "Você diz o orçamento", F_H2, CREAM, al, PINE)
        texto_centro(d, 390, "e o tamanho da sala.", F_H2, GOLD, al, PINE)
    # --- 4. fio e luzes ---
    ff = ease(seg(t, T_LUZ[0], T_LUZ[1]-.4))
    if ff > 0:
        q = parcial(FIO, ff)
        if len(q) > 1: d.line(q, fill=(70, 96, 80), width=3)
        for j, (x, y) in enumerate(BULBOS):
            tj = T_LUZ[0] + .1 + j * (T_LUZ[1]-T_LUZ[0]-.5) / NB
            if t >= tj:
                c = CORES[j % 5]; pulso = 1 + .25 * math.exp(-(t-tj)*6)
                r = 11 * pulso
                d.ellipse((x-r, y-r, x+r, y+r), fill=c)
                g = 34 * pulso
                dl.ellipse((x/2-g, y/2-g, x/2+g, y/2+g), fill=c)
        # ponteira
        if t > T_LUZ[1] - .4:
            k = eob(seg(t, T_LUZ[1]-.4, T_LUZ[1]+.1)); s = 34 * k
            pts = [(CX + s*math.cos(math.pi/2 + a*math.pi/5) * (1 if a % 2 == 0 else .45),
                    TOP - 8 - s*math.sin(math.pi/2 + a*math.pi/5) * (1 if a % 2 == 0 else .45)) for a in range(10)]
            d.polygon(pts, fill=GOLD); dl.ellipse((CX/2-50*k, (TOP-8)/2-50*k, CX/2+50*k, (TOP-8)/2+50*k), fill=GOLD2)
        al = ease(seg(t, T_LUZ[0]+.2, T_LUZ[0]+.6)) * (1 - ease(seg(t, T_KIT[0]-.3, T_KIT[0])))
        texto_centro(d, 310, "O site monta o Natal", F_H2, CREAM, al, PINE)
        texto_centro(d, 390, "inteiro, combinando.", F_H2, GOLD, al, PINE)
    # --- 5. cards do kit ---
    if t >= T_KIT[0]:
        total = 0
        for j, (cid, nome, preco) in enumerate(KIT):
            tj = T_KIT[0] + .15 + j * .32
            k = eob(seg(t, tj, tj + .35))
            if k <= 0: continue
            total += preco * clamp((t - tj) / .35)
            col, row = j % 2, j // 2
            x = 600 + col * 0
            # coluna à direita da árvore
            cx_, cy_ = 800, 690 + j * 150
            s = int(120 * k)
            if s > 4:
                foto = FOTOS[cid].resize((s, s))
                im.paste(foto, (int(cx_ - 200 - s/2 + 60), int(cy_ - s/2)))
            if k > .6:
                d.text((cx_ - 70, cy_ - 42), nome, font=F_LB, fill=CREAM)
                d.text((cx_ - 70, cy_ + 2), f"R$ {preco}", font=F_PR, fill=GOLD)
        al = ease(seg(t, T_KIT[0]+.2, T_KIT[0]+.5)) * (1 - ease(seg(t, T_CTA[0], T_CTA[0]+.3)))
        texto_centro(d, 310, "Bem avaliado no", F_H2, CREAM, al, PINE)
        texto_centro(d, 390, "Mercado Livre.", F_H2, GOLD, al, PINE)
        if t < T_CTA[0] + .3:
            tt = min(total, 478) if t < T_KIT[0] + 1.9 else 478
            texto_centro(d, 1500, f"Total R$ {brl(tt)}", inter(76, "Bold"), CREAM, al, PINE)
            if t > T_KIT[0] + 1.9:
                a2 = ease(seg(t, T_KIT[0]+1.9, T_KIT[0]+2.2)) * al
                texto_centro(d, 1590, "sobrou R$ 22 do orçamento", F_SM, CREAM, a2, PINE)
    # --- 6. CTA ---
    if t >= T_CTA[0]:
        al = ease(seg(t, T_CTA[0], T_CTA[0]+.4))
        texto_centro(d, 310, "Monte o seu Natal", F_H1, CREAM, al, PINE)
        texto_centro(d, 390, "no orçamento.", F_H1i, GOLD, al, PINE)
        a2 = ease(seg(t, T_CTA[0]+.4, T_CTA[0]+.8))
        bw, bh, by = 820, 120, 1430
        cbtn = tuple(int(PINE[k] + (GOLD[k]-PINE[k])*a2) for k in range(3))
        d.rounded_rectangle(((W-bw)/2, by, (W+bw)/2, by+bh), 60, fill=cbtn)
        texto_centro(d, by + 34, "natal.ofertadorafa.com.br", F_URL, PINE, a2, cbtn)
        texto_centro(d, by + 160, "4 perguntas · 30 segundos", F_SM, MUT, a2, PINE)
    # glow
    luz = luz.filter(ImageFilter.GaussianBlur(22)).resize((W, H), Image.BILINEAR)
    arr = np.asarray(im).astype(np.int16) + (np.asarray(luz).astype(np.int16) * 0.7).astype(np.int16)
    im = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))
    # zoom lento
    z = 1 + 0.035 * (t / DUR)
    if z > 1.001:
        cw, ch = int(W / z), int(H / z)
        ox = (W - cw)//2 + int(8*math.sin(t*.7)); oy = (H - ch)//2 + int(6*math.cos(t*.5))
        im = im.crop((ox, oy, ox+cw, oy+ch)).resize((W, H), Image.BILINEAR)
    im = Image.blend(im, GRAOS[i % 6], 0.03)
    return im

# ---------- áudio sintetizado ----------
SR = 44100
def audio():
    n = int(SR * DUR); out = np.zeros(n); tt = np.arange(n) / SR
    rng = np.random.default_rng(1)
    def add(sig, t0, g=1.0):
        a = int(t0 * SR); b = min(n, a + len(sig)); out[a:b] += sig[:b-a] * g
    def env(L, att=.005, dec=.3):
        x = np.arange(int(L*SR)) / SR
        return np.minimum(1, x/att) * np.exp(-x/dec)
    # room tone
    nz = rng.standard_normal(n); k = np.ones(400)/400
    out += np.convolve(nz, k, "same") * .05
    # pisca queimado: zumbido 120 Hz com falhas
    L = 2.3; x = np.arange(int(L*SR))/SR
    buzz = np.sign(np.sin(2*np.pi*120*x)) * .5 + np.sin(2*np.pi*240*x)*.3
    gate = np.repeat((rng.random(int(L*14)+1) > .45).astype(float), SR//14 + 1)[:len(x)]
    gate = np.convolve(gate, np.ones(300)/300, "same")
    add(buzz * gate * .06, 0.0)
    # faísca + pop
    sp = rng.standard_normal(int(.12*SR)) * env(.12, .001, .025)
    add(sp * .5, 2.15)
    # ticks do slider (sobe o tom)
    for j in range(10):
        f = 900 + j * 90; L = .03; x = np.arange(int(L*SR))/SR
        add(np.sin(2*np.pi*f*x) * env(L, .001, .008) * .35, 2.75 + j * .13)
    add(np.sin(2*np.pi*1800*np.arange(int(.08*SR))/SR) * env(.08, .001, .03) * .3, 4.15)
    # lápis desenhando a árvore: ruído passa-banda
    L = 2.8; m = int(L*SR); w = rng.standard_normal(m)
    w = np.diff(np.concatenate([[0], w]))
    w = np.convolve(w, np.ones(6)/6, "same")
    trem = .5 + .5 * np.abs(np.sin(2*np.pi*3.3*np.arange(m)/SR))
    sw = np.minimum(1, np.arange(m)/(.2*SR)) * np.minimum(1, (m-np.arange(m))/(.3*SR))
    add(w * trem * sw * .09, 4.5)
    # caixinha de música: uma nota por lâmpada (arpejo original, pentatônica)
    escala = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5, 1174.66, 1318.51, 1567.98, 1760.0]
    ordem = [0, 2, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 9, 8, 6, 7, 8, 9]
    for j in range(NB):
        tj = T_LUZ[0] + .1 + j * (T_LUZ[1]-T_LUZ[0]-.5) / NB
        f = escala[ordem[j]]; L = 1.2; x = np.arange(int(L*SR))/SR
        nota = (np.sin(2*np.pi*f*x) + .35*np.sin(2*np.pi*f*2.76*x)*np.exp(-x*9) + .2*np.sin(2*np.pi*f*5.4*x)*np.exp(-x*16))
        add(nota * env(L, .002, .45) * .16, tj)
    # vidro: ting por card
    for j in range(5):
        tj = T_KIT[0] + .15 + j * .32; L = 1.0; x = np.arange(int(L*SR))/SR
        f = 2400 + j * 160
        ting = sum(np.sin(2*np.pi*f*r*x) * np.exp(-x*(5+3*q)) / (1+q) for q, r in enumerate([1, 2.32, 4.25, 6.63]))
        add(ting * .1, tj + .05)
    # contador
    for j in range(14):
        add(np.sin(2*np.pi*2600*np.arange(int(.015*SR))/SR) * env(.015, .001, .004) * .12, T_KIT[0] + .2 + j*.12)
    # acorde final (sino) + grave
    L = 2.6; x = np.arange(int(L*SR))/SR
    acorde = sum(np.sin(2*np.pi*f*x) * np.exp(-x*1.4) + .3*np.sin(2*np.pi*f*2.4*x)*np.exp(-x*4) for f in [261.63, 329.63, 392.0, 493.88, 523.25])
    add(acorde * .08, T_CTA[0])
    add(np.sin(2*np.pi*65.4*x) * np.minimum(1, x/.4) * np.exp(-x*1.1) * .25, T_CTA[0])
    # reverb simples
    ir_len = int(1.6*SR); ir = rng.standard_normal(ir_len) * np.exp(-np.arange(ir_len)/SR*3.2); ir[0] = 1
    from numpy.fft import rfft, irfft
    L2 = 1 << (n + ir_len).bit_length()
    wet = irfft(rfft(out, L2) * rfft(ir, L2), L2)[:n]
    mix = out * .8 + wet / np.max(np.abs(wet)) * np.max(np.abs(out)) * .35
    mix = mix / np.max(np.abs(mix)) * .89
    fade = np.ones(n); fade[-int(.4*SR):] = np.linspace(1, 0, int(.4*SR)); mix *= fade
    path = os.path.join(OUT, "sfx.wav")
    with wave.open(path, "wb") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((mix * 32767).astype(np.int16).tobytes())
    return path

if __name__ == "__main__":
    wav = audio()
    mp4 = os.path.join(OUT, "animatic_natal.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    thumbs = []
    for i in range(N):
        f = frame(i); ff.stdin.write(f.tobytes())
        if i in (30, 100, 190, 285, 360, 420): thumbs.append(f.resize((270, 480)))
    ff.stdin.close(); ff.wait()
    sheet = Image.new("RGB", (270*6 + 50, 500), (10, 20, 15))
    for k, th in enumerate(thumbs): sheet.paste(th, (10 + k*278, 10))
    sheet.save(os.path.join(OUT, "contato.png"))
    print(mp4)
