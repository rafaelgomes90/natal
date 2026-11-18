"""Vídeo final com a voz do Rafael — 'A sala que se monta sozinha', uma versão por faixa (200/500/1200).
Uso: python3 video_natal_voz.py <pasta_voz>   (pasta com base.wav, f200.wav, f500.wav, f1200.wav já tratados)
Saída: video/natal_voz_<faixa>.mp4 (1080x1920) + video/natal_voz_<faixa>_4x5.mp4 (1080x1350)."""
import os, sys, math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw
import video_natal as B   # sala, fundo, fontes, helpers
from video_natal import W, H, FPS, PINE, CREAM, GOLD, GOLD2, MUT, RED, clamp, ease, eob, seg, brl, parcial, fr, inter

VOZ = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/voz"
SR = 44100

# ---------- voz: base + final da faixa + CTA ----------
def ler(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

# cortes (s) na gravação base, achados com faster-whisper + silencedetect
CORTE_A = 18.30          # fim de "...dentro do seu orçamento."
CORTE_B = (18.45, 22.45) # "Monta o seu no site Natal do Rafa, link aqui embaixo."
FINAIS = {200: ("f200.wav", .25, 2.85), 500: ("f500.wav", .50, 3.90), 1200: ("f1200.wav", .00, 4.35)}

FAIXAS = {
    200: dict(kit=[("arvore-120-com-enfeites", "Árvore 1,20 m c/ enfeites", 78), ("cordao-300-leds-30m", "300 LEDs, 30 m", 59),
                   ("ponteira-glitter", "Ponteira estrela", 26), ("saia-papai-noel", "Saia da árvore", 30)],
              esc=.78, nb=12, frase=("Com R$ 200", "já dá.")),
    500: dict(kit=[("arvore-180-800-galhos", "Árvore 1,80 m", 206), ("cordao-300-leds-30m", "300 LEDs, 30 m", 59),
                   ("bolas-kit-100", "Kit 100 bolas", 143), ("ponteira-led", "Ponteira LED", 40), ("saia-papai-noel", "Saia da árvore", 30)],
              esc=1.0, nb=18, frase=("Árvore de 1,80 m com", "tudo, até R$ 500.")),
    1200: dict(kit=[("arvore-240-luvinco", "Árvore 2,40 m", 485), ("cordao-300-leds-30m", "2× 300 LEDs", 118),
                    ("bolas-kit-100", "Kit 100 bolas", 143), ("saia-tapete", "Saia tapete", 79), ("guirlanda-led", "Guirlanda LED", 70),
                    ("festao-10m", "Festão 10 m", 30), ("lacos-veludo-6", "6 laços", 45), ("papai-noel-dourado", "Papai Noel", 171)],
               esc=1.05, nb=24, frase=("A casa inteira no clima,", "até R$ 1.200.")),
}

def montar_audio(faixa):
    base = ler(os.path.join(VOZ, "base.wav"))
    fn, a, b = FINAIS[faixa]; fim = ler(os.path.join(VOZ, fn))[int(a*SR):int(b*SR)]
    pausa = np.zeros(int(.25*SR))
    parte1 = base[:int(CORTE_A*SR)]
    parte2 = base[int(CORTE_B[0]*SR):int(CORTE_B[1]*SR)]
    v = np.concatenate([parte1, pausa, fim, pausa, parte2, np.zeros(int(.9*SR))])
    t_fim = len(parte1)/SR + .25
    t_cta = t_fim + len(fim)/SR + .25
    return v, t_fim, t_cta

# ---------- geometria por faixa ----------
CX, TOP0, BASEY = B.CX, B.TOP, 1240 + B.DY
def escala_pts(pts, e): return [(CX + (x-CX)*e, BASEY - (BASEY-y)*e) for x, y in pts]

class Cena:
    def __init__(s, faixa, T):
        cfg = FAIXAS[faixa]; s.f = faixa; s.T = T; e = cfg["esc"]
        s.arv = escala_pts(B.ARV, e); s.tronco = escala_pts(B.TRONCO, e)
        top = BASEY - (BASEY - TOP0) * e; s.top = top
        fio = []
        for i in range(260):
            k = i/259; y = top + 70*e + k * (BASEY - 60 - top - 70*e)
            larg = (40 + (y-top)/(BASEY-top)*250) * e
            fio.append((CX + math.sin(k*math.pi*(5 + cfg["nb"]/6))*larg*.82, y))
        s.fio = fio; nb = cfg["nb"]
        s.bulbos = [fio[int(i*(len(fio)-1)/(nb-1))] for i in range(nb)]
        s.kit = cfg["kit"]; s.total = sum(p for *_, p in s.kit); s.sobra = faixa - s.total; s.frase = cfg["frase"]
        n = len(s.kit); s.passo = min(150, 820 // n); s.th = min(120, s.passo - 18)
        s.fotos = {}
        for cid, *_ in s.kit:
            im = Image.open(os.path.join(B.IMG, cid + ".webp")).convert("RGB"); sz = 240
            w, h = im.size; k = sz/max(w, h); im = im.resize((int(w*k), int(h*k)), Image.LANCZOS)
            c = Image.new("RGB", (sz, sz), (255, 255, 255)); c.paste(im, ((sz-im.width)//2, (sz-im.height)//2)); s.fotos[cid] = c

TXT = B.texto_centro
F_H1, F_H1i, F_H2, F_SM, F_NUM = B.F_H1, B.F_H1i, B.F_H2, B.F_SM, B.F_NUM
F_PR, F_LB, F_URL = inter(42, "Bold"), inter(32, "SemiBold"), B.F_URL
CORES = B.CORES

def legenda(d, t, a0, a1, l1, l2, f1=F_H2, f2=F_H2, c2=GOLD, y=310):
    al = ease(seg(t, a0, a0 + .3)) * (1 - ease(seg(t, a1 - .25, a1)))
    if al > 0:
        TXT(d, y, l1, f1, CREAM, al, PINE); TXT(d, y + 80 + (f1.size - 64), l2, f2, c2, al, PINE)

def frame(c, i):
    T = c.T; t = i / FPS
    im = B.BG.copy(); d = ImageDraw.Draw(im)
    luz = Image.new("RGB", (W//2, H//2), (0, 0, 0)); dl = ImageDraw.Draw(luz)
    # --- sala: aparece em "esse ano eu fiz diferente", pulsa em "sala" ---
    fsala = ease(seg(t, T["dif"], T["dif"] + 1.0))
    pulso = math.exp(-max(0, t - T["sala"]) * 3) if t >= T["sala"] else 0
    a_s = (.55 + .4 * pulso) if t < T["kit"] else .55 * (1 - seg(t, T["kit"], T["kit"] + .5)) + .18
    cl = tuple(int(PINE[k] + (GOLD2[k]-PINE[k]) * a_s) for k in range(3))
    for p, fecha in B.SALA:
        q = parcial(p + [p[0]] if fecha else p, fsala)
        if len(q) > 1: d.line(q, fill=cl, width=3 + int(2*pulso))
    # --- abertura: pisca queimado ---
    if t < T["dif"] + .4:
        apaga = ease(seg(t, T["dif"] - .2, T["dif"] + .4))
        pisca = [(540 + (j - 7) * 70, 760 + int(60*math.sin(j*.9))) for j in range(15)]
        corf = tuple(int(60 - 40*apaga) for _ in range(3))
        d.line(pisca, fill=(60, 80, 68), width=3)
        for j, (x, y) in enumerate(pisca):
            vivo = (j % 3 != 1) and (random.Random(int(t*12) + j*7).random() > .5) and t < T["queimado"] + .1 and apaga < .5
            if t < T["queimado"]: vivo = vivo or j % 4 == 0
            d.ellipse((x-12, y-12, x+12, y+12), fill=GOLD if vivo else (55, 70, 60))
            if vivo: dl.ellipse((x/2-26, y/2-26, x/2+26, y/2+26), fill=CORES[j % 5])
        if T["queimado"] < t < T["queimado"] + .18:
            dl.ellipse((540/2-70, 760/2-70, 540/2+70, 760/2+70), fill=(255, 240, 200))
        al = ease(seg(t, .4, .8)) * (1 - ease(seg(t, T["dif"] - .3, T["dif"])))
        TXT(d, 310, "Todo ano a mesma", F_H1, CREAM, al, PINE); TXT(d, 410, "novela de Natal.", F_H1i, GOLD, al, PINE)
        # palavras que ele fala aparecem riscadas
        for k, (pal, tk) in enumerate([("árvore torta", T["torta"]), ("pisca queimado", T["queimado"]), ("bola que não combina", T["combina"])]):
            a2 = ease(seg(t, tk - .2, tk + .1)) * (1 - ease(seg(t, T["dif"] - .3, T["dif"])))
            if a2 > 0:
                y = 1040 + k * 90; f = inter(46, "SemiBold")
                TXT(d, y, pal, f, MUT, a2, PINE)
                w = d.textlength(pal, font=f); r = ease(seg(t, tk + .1, tk + .45))
                if r > 0: d.line([((W-w)/2 - 10, y + 30), ((W-w)/2 - 10 + (w+20)*r, y + 30)], fill=RED, width=6)
    legenda(d, t, T["dif"], T["voce"], "Esse ano eu", "fiz diferente.", F_H1, F_H1i)
    # --- slider ---
    if T["voce"] - .1 < t < T["monta"] + .3:
        al = ease(seg(t, T["voce"], T["voce"] + .3)) * (1 - ease(seg(t, T["monta"] - .2, T["monta"] + .2)))
        TXT(d, 310, "Quanto você quer gastar?", F_H2, CREAM, al, PINE)
        x0, x1, y = 200, 880, 460
        clm = tuple(int(PINE[k] + (MUT[k]-PINE[k])*al) for k in range(3)); cg = tuple(int(PINE[k] + (GOLD[k]-PINE[k])*al) for k in range(3))
        d.line([(x0, y), (x1, y)], fill=clm, width=8)
        alvo = (c.f - 100) / (1200 - 100)
        p = ease(seg(t, T["gastar"] - .3, T["gastar"] + .5)) * alvo
        xp = x0 + (x1 - x0) * p
        d.line([(x0, y), (xp, y)], fill=cg, width=8); d.ellipse((xp-24, y-24, xp+24, y+24), fill=cg)
        val = round((100 + p * 1100) / 10) * 10
        TXT(d, 500, f"R$ {brl(val)}", F_NUM, CREAM, al, PINE)
        a2 = ease(seg(t, T["sala"] - .4, T["sala"])) * al
        TXT(d, 650, "e o tamanho da sala", B.F_H2, GOLD, a2, PINE)
    # --- árvore se desenha em "monta" ---
    fa = ease(seg(t, T["monta"], T["monta"] + 1.4))
    if fa > 0:
        q = parcial(c.arv, fa)
        if len(q) > 1: d.line(q, fill=GOLD2, width=5, joint="curve")
        q = parcial(c.tronco, ease(seg(t, T["monta"] + 1.1, T["monta"] + 1.5)))
        if len(q) > 1: d.line(q, fill=GOLD2, width=5)
    legenda(d, t, T["monta"] - .2, T["kit"], "O site monta o Natal", "inteiro, combinando.")
    # --- luzes em "combinando" ---
    t0, t1 = T["combinando"] - .5, T["combinando"] + 1.1
    ff = ease(seg(t, t0, t1))
    if ff > 0:
        q = parcial(c.fio, ff)
        if len(q) > 1: d.line(q, fill=(70, 96, 80), width=3)
        nb = len(c.bulbos)
        for j, (x, y) in enumerate(c.bulbos):
            tj = t0 + .05 + j * (t1 - t0) / nb
            if t >= tj:
                cor = CORES[j % 5]; pu = 1 + .25 * math.exp(-(t-tj)*6); r = 11*pu; g = 34*pu
                d.ellipse((x-r, y-r, x+r, y+r), fill=cor); dl.ellipse((x/2-g, y/2-g, x/2+g, y/2+g), fill=cor)
        if t > t1 - .2:
            k = eob(seg(t, t1 - .2, t1 + .3)); s_ = 34*k; ty = c.top - 8
            pts = [(CX + s_*math.cos(math.pi/2 + a*math.pi/5)*(1 if a % 2 == 0 else .45), ty - s_*math.sin(math.pi/2 + a*math.pi/5)*(1 if a % 2 == 0 else .45)) for a in range(10)]
            d.polygon(pts, fill=GOLD); dl.ellipse((CX/2-50*k, ty/2-50*k, CX/2+50*k, ty/2+50*k), fill=GOLD2)
    # --- cards: um por item, a partir de "item" ---
    if t >= T["item"] - .1:
        n = len(c.kit); passo, th = c.passo, c.th; y0 = 640
        span = max(1.2, T["orcamento"] - .3 - T["item"])
        acum = 0
        for j, (cid, nome, preco) in enumerate(c.kit):
            tj = T["item"] + j * span / n
            k = eob(seg(t, tj, tj + .35))
            if k <= 0: continue
            acum += preco * clamp((t - tj) / .35)
            cy = y0 + j * passo + passo/2; s_ = int(th * k)
            if s_ > 4: im.paste(c.fotos[cid].resize((s_, s_)), (int(745 - s_/2), int(cy - s_/2)))
            if k > .6:
                d.text((815, cy - 40), nome, font=F_LB, fill=CREAM)
                d.text((815, cy + 2), f"R$ {preco}", font=F_PR, fill=GOLD)
        legenda(d, t, T["item"] - .2, T["fim"] + .2, "Bem avaliado no", "Mercado Livre.")
        if t < T["cta"] + .2:
            al = ease(seg(t, T["item"], T["item"] + .3)) * (1 - ease(seg(t, T["cta"] - .1, T["cta"] + .2)))
            tot = c.total if t >= T["orcamento"] else min(acum, c.total)
            pz = 1 + .12 * math.exp(-max(0, t - T["fim"]) * 4) * (t >= T["fim"])
            TXT(d, 1510, f"Total R$ {brl(tot)}", inter(int(76 * pz), "Bold"), CREAM, al, PINE)
            a2 = ease(seg(t, T["orcamento"] - .1, T["orcamento"] + .2)) * al
            TXT(d, 1605, f"dentro dos R$ {brl(c.f)} · sobrou R$ {brl(c.sobra)}", F_SM, GOLD2, a2, PINE)
    # --- frase da faixa ---
    legenda(d, t, T["fim"], T["cta"] + .1, c.frase[0], c.frase[1], F_H2, F_H2)
    # --- CTA ---
    if t >= T["cta"]:
        al = ease(seg(t, T["cta"], T["cta"] + .4))
        TXT(d, 300, "Monte o seu Natal", F_H1, CREAM, al, PINE); TXT(d, 400, "no orçamento.", F_H1i, GOLD, al, PINE)
        a2 = ease(seg(t, T["link"] - .2, T["link"] + .2))
        bw, bh, by = 840, 124, 1460
        cb = tuple(int(PINE[k] + (GOLD[k]-PINE[k])*a2) for k in range(3))
        d.rounded_rectangle(((W-bw)/2, by, (W+bw)/2, by+bh), 62, fill=cb)
        TXT(d, by + 36, "natal.ofertadorafa.com.br", F_URL, PINE, a2, cb)
        if a2 > .9:  # setinha pra baixo
            yy = by + bh + 30 + 12 * math.sin(t * 7)
            d.polygon([(W/2 - 26, yy), (W/2 + 26, yy), (W/2, yy + 30)], fill=GOLD)
    # glow + câmera + grão
    luz = luz.filter(B.ImageFilter.GaussianBlur(22)).resize((W, H), Image.BILINEAR)
    arr = np.asarray(im).astype(np.int16) + (np.asarray(luz).astype(np.int16) * .7).astype(np.int16)
    im = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))
    z = 1 + .035 * (t / c.DUR); cw, ch = int(W/z), int(H/z)
    ox = (W-cw)//2 + int(8*math.sin(t*.7)); oy = (H-ch)//2 + int(6*math.cos(t*.5))
    im = im.crop((ox, oy, ox+cw, oy+ch)).resize((W, H), Image.BILINEAR)
    return Image.blend(im, B.GRAOS[i % 6], .03)

# ---------- efeitos ----------
def sfx(c, n):
    T = c.T; out = np.zeros(n); rng = np.random.default_rng(1)
    def add(sig, t0, g=1.):
        a = int(t0*SR); b = min(n, a + len(sig))
        if a < n: out[a:b] += sig[:b-a] * g
    def x_(L): return np.arange(int(L*SR))/SR
    def env(L, att, dec): x = x_(L); return np.minimum(1, x/att) * np.exp(-x/dec)
    out += np.convolve(rng.standard_normal(n), np.ones(400)/400, "same") * .04
    L = T["dif"]; x = x_(L)
    buzz = np.sign(np.sin(2*np.pi*120*x))*.5 + np.sin(2*np.pi*240*x)*.3
    gate = np.repeat((rng.random(int(L*12)+2) > .45).astype(float), SR//12 + 1)[:len(x)]
    add(buzz * np.convolve(gate, np.ones(300)/300, "same") * .05, 0)
    add(rng.standard_normal(int(.12*SR)) * env(.12, .001, .025), T["queimado"], .5)
    for tk in (T["torta"], T["queimado"], T["combina"]):  # risco vermelho
        w = np.diff(np.concatenate([[0], rng.standard_normal(int(.35*SR))])); add(w * env(.35, .01, .12) * .12, tk + .1)
    # "fiz diferente": sino de virada
    x = x_(1.6); add((np.sin(2*np.pi*1318.5*x) + .4*np.sin(2*np.pi*3560*x)*np.exp(-x*6)) * np.exp(-x*2.4) * .1, T["dif"])
    for j in range(10):
        f = 900 + j*90; x = x_(.03); add(np.sin(2*np.pi*f*x) * env(.03, .001, .008) * .3, T["gastar"] - .3 + j*.08)
    m = int(1.6*SR); w = np.convolve(np.diff(np.concatenate([[0], rng.standard_normal(m)])), np.ones(6)/6, "same")
    tr = .5 + .5*np.abs(np.sin(2*np.pi*3.3*np.arange(m)/SR)); sw = np.minimum(1, np.arange(m)/(.15*SR)) * np.minimum(1, (m-np.arange(m))/(.3*SR))
    add(w * tr * sw * .08, T["monta"])
    escala = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5, 1174.66, 1318.51, 1567.98, 1760.0]
    ordem = [0, 2, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 9, 8, 6, 7, 8, 9, 7, 8, 9, 8, 9, 9]
    t0, t1 = T["combinando"] - .5, T["combinando"] + 1.1; nb = len(c.bulbos)
    for j in range(nb):
        f = escala[ordem[j % len(ordem)]]; x = x_(1.0)
        nota = np.sin(2*np.pi*f*x) + .35*np.sin(2*np.pi*f*2.76*x)*np.exp(-x*9)
        add(nota * env(1.0, .002, .4) * .12, t0 + .05 + j*(t1-t0)/nb)
    span = max(1.2, T["orcamento"] - .3 - T["item"]); nk = len(c.kit)
    for j in range(nk):
        x = x_(.9); f = 2400 + j*120
        add(sum(np.sin(2*np.pi*f*r*x)*np.exp(-x*(5+3*q))/(1+q) for q, r in enumerate([1, 2.32, 4.25])) * .07, T["item"] + j*span/nk + .05)
    x = x_(1.4)
    for dd, f in [(0, 2093.0), (.09, 2637.0)]: add(np.sin(2*np.pi*f*x)*np.exp(-x*3.2)*.09, T["orcamento"] + dd)
    x = x_(2.6)
    add(sum(np.sin(2*np.pi*f*x)*np.exp(-x*1.4) for f in [261.63, 329.63, 392.0, 493.88, 523.25]) * .06, T["cta"])
    add(np.sin(2*np.pi*65.4*x) * np.minimum(1, x/.4) * np.exp(-x*1.1) * .2, T["cta"])
    L = int(1.4*SR); ir = rng.standard_normal(L)*np.exp(-np.arange(L)/SR*3.2); ir[0] = 1
    M = 1 << (n + L).bit_length(); wet = np.fft.irfft(np.fft.rfft(out, M)*np.fft.rfft(ir, M), M)[:n]
    mix = out*.8 + wet/np.max(np.abs(wet))*np.max(np.abs(out))*.3
    return mix / np.max(np.abs(mix)) * .7

def salvar(p, a):
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a, -1, 1)*32767).astype(np.int16).tobytes())

def tempos(t_fim, t_cta):
    # palavras na gravação base (faster-whisper), mesma escala de tempo do vídeo até CORTE_A
    T = dict(torta=2.55, queimado=3.5, combina=4.75, dif=5.6, voce=7.3, gastar=8.25, sala=9.7, monta=10.86,
             combinando=12.6, item=14.1, orcamento=17.45, fim=t_fim, cta=t_cta)
    T["link"] = t_cta + (21.34 - CORTE_B[0])
    T["kit"] = T["item"] - .2
    return T

def render(faixa):
    voz, t_fim, t_cta = montar_audio(faixa)
    T = tempos(t_fim, t_cta); c = Cena(faixa, T); c.DUR = len(voz)/SR
    n = len(voz); efe = sfx(c, n)
    pv, pe = f"/tmp/voz_{faixa}.wav", f"/tmp/sfx_{faixa}.wav"; salvar(pv, voz); salvar(pe, efe)
    OUT = os.path.join(B.OUT); mp4 = os.path.join(OUT, f"natal_voz_{faixa}.mp4")
    filtro = ("[1:a]asplit=2[v1][v2];[2:a][v1]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=300[duck];"
              "[duck][v2]amix=inputs=2:weights='0.8 1':normalize=0,loudnorm=I=-15:TP=-1.5[a]")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", pv, "-i", pe, "-filter_complex", filtro, "-map", "0:v", "-map", "[a]",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                           "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    N = int(c.DUR * FPS); thumbs = []
    marcas = [int(x*FPS) for x in (3.6, 6.2, 8.9, 13.3, T["orcamento"] + .5, T["fim"] + 1, T["cta"] + 1.5)]
    for i in range(N):
        f = frame(c, i); ff.stdin.write(f.tobytes())
        if i in marcas: thumbs.append(f.resize((216, 384)))
    ff.stdin.close(); ff.wait()
    sh = Image.new("RGB", (226*len(thumbs) + 10, 404), (8, 18, 13))
    for k, th in enumerate(thumbs): sh.paste(th, (10 + k*226, 10))
    sh.save(os.path.join(OUT, f"contato_voz_{faixa}.png"))
    # 4:5 pro feed: corte central 1080x1350
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf", "crop=1080:1350:0:285", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "22", "-c:a", "copy", "-movflags", "+faststart", mp4.replace(".mp4", "_4x5.mp4")])
    print(faixa, round(c.DUR, 1), "s", mp4)

if __name__ == "__main__":
    for f in (sys.argv[2:] and map(int, sys.argv[2:])) or (200, 500, 1200): render(f)
