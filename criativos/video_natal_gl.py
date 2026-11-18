"""Versão three.js + shaders do vídeo A: mundo 3D renderizado em /home/claude/natal/gl (render.mjs), texto/cards em PIL por cima.
Uso: python3 video_natal_gl.py prep|comp <faixa ...>"""
import os, sys, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import video_natal_voz_el as V
from video_natal import W, H, FPS, PINE, CREAM, GOLD, GOLD2, MUT, RED, clamp, ease, eob, seg, brl, inter
import video_natal as B

V.VOZ = "/home/claude/tts/el2/c"
GL = "/home/claude/natal/gl"
EXTRA = {200: dict(nbolas=14, presentes=1, festao=False), 500: dict(nbolas=24, presentes=2, festao=False), 1200: dict(nbolas=34, presentes=5, festao=True)}
OUT = B.OUT

def txt(L, y, s, font, col, a, sh=True):
    if a <= .01: return
    w = font.getlength(s); x = int((W - w) / 2); hh = int(font.size * 1.6)
    if sh:
        m = Image.new("L", (W, hh), 0); ImageDraw.Draw(m).text((x, 8), s, font=font, fill=int(190 * a)); m = m.filter(ImageFilter.GaussianBlur(12))
        s_ = Image.new("RGBA", (W, hh), (0, 6, 3, 0)); s_.putalpha(m); L.alpha_composite(s_, (0, y - 6))
    t = Image.new("RGBA", (W, hh), (0, 0, 0, 0)); ImageDraw.Draw(t).text((x, 8), s, font=font, fill=col + (int(255 * a),)); L.alpha_composite(t, (0, y - 6))

def rr_mask(size, r):
    m = Image.new("L", size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), r, fill=255); return m

F_H1, F_H1i, F_H2, F_SM, F_NUM, F_PR, F_LB, F_URL = V.F_H1, V.F_H1i, V.F_H2, V.F_SM, V.F_NUM, V.F_PR, V.F_LB, V.F_URL

def legenda(L, t, a0, a1, l1, l2, f1=F_H2, f2=F_H2, c2=GOLD, y=310):
    al = ease(seg(t, a0, a0 + .3)) * (1 - ease(seg(t, a1 - .25, a1)))
    if al > 0: txt(L, y, l1, f1, CREAM, al); txt(L, y + 80 + (f1.size - 64), l2, f2, c2, al)

def compor(base, c, i):
    T = c.T; t = i / FPS; L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    # abertura
    if t < T["dif"] + .4:
        al = ease(seg(t, .4, .8)) * (1 - ease(seg(t, T["dif"] - .3, T["dif"])))
        txt(L, 250, "Todo ano a mesma", F_H1, CREAM, al); txt(L, 350, "novela de Natal.", F_H1i, GOLD, al)
        for k, (pal, tk) in enumerate([("árvore torta", T["torta"]), ("pisca queimado", T["queimado"]), ("bola que não combina", T["combina"])]):
            a2 = ease(seg(t, tk - .2, tk + .1)) * (1 - ease(seg(t, T["dif"] - .3, T["dif"])))
            if a2 > 0:
                y = 1480 + k * 90; f = inter(46, "SemiBold"); txt(L, y, pal, f, (190, 205, 196), a2)
                w = f.getlength(pal); r = ease(seg(t, tk + .1, tk + .45))
                if r > 0: d.line([((W - w) / 2 - 10, y + 36), ((W - w) / 2 - 10 + (w + 20) * r, y + 36)], fill=RED + (255,), width=6)
    legenda(L, t, T["dif"], T["voce"], "Esse ano eu", "fiz diferente.", F_H1, F_H1i)
    # slider
    if T["voce"] - .1 < t < T["monta"] + .3:
        al = ease(seg(t, T["voce"], T["voce"] + .3)) * (1 - ease(seg(t, T["monta"] - .2, T["monta"] + .2)))
        txt(L, 310, "Quanto você quer gastar?", F_H2, CREAM, al)
        x0, x1, y = 200, 880, 470
        d.rounded_rectangle((x0, y - 4, x1, y + 4), 4, fill=(150, 170, 158, int(170 * al)))
        alvo = (c.f - 100) / (1200 - 100); p = ease(seg(t, T["gastar"] - .3, T["gastar"] + .5)) * alvo; xp = x0 + (x1 - x0) * p
        d.rounded_rectangle((x0, y - 4, xp, y + 4), 4, fill=GOLD + (int(255 * al),))
        g = Image.new("RGBA", (W, 160), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((xp - 34, 80 - 34, xp + 34, 80 + 34), fill=GOLD + (int(120 * al),))
        L.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)), (0, y - 80)); d.ellipse((xp - 24, y - 24, xp + 24, y + 24), fill=GOLD + (int(255 * al),))
        val = round((100 + p * 1100) / 10) * 10
        txt(L, 520, f"R$ {brl(val)}", F_NUM, CREAM, al)
        txt(L, 690, "e o tamanho da sala", F_H2, GOLD, ease(seg(t, T["sala"] - .4, T["sala"])) * al)
    legenda(L, t, T["monta"] - .2, T["kit"], "O site monta o Natal", "inteiro, combinando.")
    # cards (vidro fosco)
    if t >= T["item"] - .1:
        n = len(c.kit); passo, th = c.passo, c.th; y0 = 640
        span = max(1.2, T["orcamento"] - .3 - T["item"]); acum = 0
        mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask); fotos = []
        for j, (cid, nome, preco) in enumerate(c.kit):
            tj = T["item"] + j * span / n; k = eob(seg(t, tj, tj + .35))
            if k <= 0: continue
            acum += preco * clamp((t - tj) / .35)
            cy = y0 + j * passo + passo / 2; hh = (passo - 12) / 2 * min(1, k)
            md.rounded_rectangle((668, cy - hh, 1052, cy + hh), 26, fill=int(255 * clamp(k)))
            fotos.append((cid, nome, preco, cy, k))
        if fotos:
            reg = base.filter(ImageFilter.GaussianBlur(16)); dark = Image.new("RGB", (W, H), (6, 22, 15)); reg = Image.blend(reg, dark, .42)
            base.paste(reg, (0, 0), mask)
            edge = mask.filter(ImageFilter.MaxFilter(3)); ed = Image.new("RGBA", (W, H), GOLD + (0,)); ed.putalpha(Image.fromarray((np.asarray(edge, np.int16) - np.asarray(mask, np.int16)).clip(0, 255).astype("uint8")).point(lambda v: int(v * .35)))
            L.alpha_composite(ed)
            for cid, nome, preco, cy, k in fotos:
                s_ = int(th * min(1, k))
                if s_ > 8:
                    ph = c.fotos[cid].resize((s_, s_), Image.LANCZOS); pm = rr_mask((s_, s_), max(6, s_ // 7)); ph = ph.convert("RGBA"); ph.putalpha(pm)
                    L.alpha_composite(ph, (int(715 - s_ / 2), int(cy - s_ / 2)))
                if k > .6:
                    a_ = clamp((k - .6) / .4); fn = F_LB if F_LB.getlength(nome) <= 252 else inter(max(22, int(34 * 252 / F_LB.getlength(nome))), "SemiBold"); d.text((792, cy - 42), nome, font=fn, fill=CREAM + (int(255 * a_),)); d.text((792, cy + 2), f"R$ {preco}", font=F_PR, fill=GOLD + (int(255 * a_),))
        legenda(L, t, T["item"] - .2, T["fim"] + .2, "Bem avaliado no", "Mercado Livre.")
        if t < T["cta"] + .2:
            al = ease(seg(t, T["item"], T["item"] + .3)) * (1 - ease(seg(t, T["cta"] - .1, T["cta"] + .2)))
            tot = c.total if t >= T["orcamento"] else min(acum, c.total)
            pz = 1 + .12 * math.exp(-max(0, t - T["fim"]) * 4) * (t >= T["fim"])
            txt(L, 1510, f"Total R$ {brl(tot)}", inter(int(76 * pz), "Bold"), CREAM, al)
            txt(L, 1605, f"dentro dos R$ {brl(c.f)} · sobrou R$ {brl(c.sobra)}", F_SM, GOLD2, ease(seg(t, T["orcamento"] - .1, T["orcamento"] + .2)) * al)
    legenda(L, t, T["fim"], T["cta"] + .1, c.frase[0], c.frase[1], F_H2, F_H2)
    if t >= T["cta"]:
        al = ease(seg(t, T["cta"], T["cta"] + .4))
        txt(L, 300, "Monte o seu Natal", F_H1, CREAM, al); txt(L, 400, "no orçamento.", F_H1i, GOLD, al)
        a2 = ease(seg(t, T["link"] - .2, T["link"] + .2)); bw, bh, by = 840, 124, 1460
        gl = Image.new("RGBA", (W, bh + 160), (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle(((W - bw) / 2, 80, (W + bw) / 2, 80 + bh), 62, fill=GOLD + (int(140 * a2 * (.7 + .3 * math.sin(t * 5))),))
        L.alpha_composite(gl.filter(ImageFilter.GaussianBlur(26)), (0, by - 80))
        bt = Image.new("RGBA", (W, bh), (0, 0, 0, 0)); ImageDraw.Draw(bt).rounded_rectangle(((W - bw) / 2, 0, (W + bw) / 2, bh), 62, fill=GOLD + (int(255 * a2),)); L.alpha_composite(bt, (0, by))
        tt = Image.new("RGBA", (W, bh), (0, 0, 0, 0)); w = F_URL.getlength("natal.ofertadorafa.com.br"); ImageDraw.Draw(tt).text(((W - w) / 2, 34), "natal.ofertadorafa.com.br", font=F_URL, fill=PINE + (int(255 * a2),)); L.alpha_composite(tt, (0, by))
        if a2 > .9:
            yy = by + bh + 30 + 12 * math.sin(t * 7); d.polygon([(W / 2 - 26, yy), (W / 2 + 26, yy), (W / 2, yy + 30)], fill=GOLD + (255,))
    im = base.convert("RGBA"); im.alpha_composite(L); return im.convert("RGB")

def prep(faixa):
    voz, t_fim, t_cta = V.montar_audio(faixa); T = V.tempos(t_fim, t_cta); c = V.Cena(faixa, T); c.DUR = len(voz) / V.SR
    cfg = V.FAIXAS[faixa]
    p = dict(T=T, dur=c.DUR, esc=cfg["esc"], nb=cfg["nb"], gain=1, **EXTRA[faixa])
    json.dump(p, open(f"/tmp/glp_{faixa}.json", "w")); return voz, T, c

def comp(faixa):
    voz, T, c = prep(faixa); n = len(voz); efe = V.sfx(c, n)
    pv, pe = f"/tmp/vozgl_{faixa}.wav", f"/tmp/sfxgl_{faixa}.wav"; V.salvar(pv, voz); V.salvar(pe, efe)
    mp4 = os.path.join(OUT, f"natal_gl_{faixa}.mp4")
    filtro = ("[1:a]asplit=2[v1][v2];[2:a][v1]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=300[duck];"
              "[duck][v2]amix=inputs=2:weights='0.8 1':normalize=0,loudnorm=I=-15:TP=-1.5[a]")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", pv, "-i", pe,
                           "-filter_complex", filtro, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    N = int(c.DUR * FPS); th = []
    marcas = [int(x * FPS) for x in (3.6, 6.2, 8.9, 13.3, T["orcamento"] + .5, T["fim"] + 1, T["cta"] + 1.5)]
    for i in range(N):
        base = Image.open(f"/tmp/glf_{faixa}/f{i:05d}.jpg").convert("RGB"); f = compor(base, c, i); ff.stdin.write(f.tobytes())
        if i in marcas: th.append(f.resize((216, 384)))
    ff.stdin.close(); ff.wait()
    sh = Image.new("RGB", (226 * len(th) + 10, 404), (8, 18, 13))
    for k, t_ in enumerate(th): sh.paste(t_, (10 + k * 226, 10))
    sh.save(os.path.join(OUT, f"contato_gl_{faixa}.png"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf", "crop=1080:1350:0:285", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "copy", "-movflags", "+faststart", mp4.replace(".mp4", "_4x5.mp4")])
    print(faixa, round(c.DUR, 1), mp4)

if __name__ == "__main__":
    cmd = sys.argv[1]; fx = [int(x) for x in sys.argv[2:]] or [200, 500, 1200]
    for f in fx: (prep if cmd == "prep" else comp)(f)
