"""Plano B em three.js: papel 3D curvando saindo da impressora, fundo cetim, brilho, bloom. Textos em PIL por cima.
Uso: python3 video_natal_b_gl.py prep | comp"""
import os, sys, json, math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "video_natal_b_voz_el.py")).read().split("efe = B.audio()")[0]
_CMD = sys.argv[1]; sys.argv = [sys.argv[0]]
g = {"__name__": "setup"}; exec(compile(src, "bvoz_head", "exec"), g)
B = g["B"]; voz = g["voz"]; SR = g["SR"]
W, H, FPS = B.W, B.H, B.FPS; N = int(B.DUR * FPS)
TEX = "/tmp/glBtex"; os.makedirs(TEX, exist_ok=True)
clamp, ease, seg, eob = B.clamp, B.ease, B.seg, B.eob

def textura(pap):
    im = pap.convert("RGBA"); a = Image.new("L", im.size, 255); d = ImageDraw.Draw(a)
    for x in range(0, B.PW, 24): d.polygon([(x, 0), (x + 12, 10), (x + 24, 0)], fill=0)
    im.putalpha(a); return im

def estado(i, cache):
    t = i / FPS; F = dict(vis=True, slotVis=False, slotY=B.SLOT + 20, printing=any(tk <= t < tk + .16 for tk in B.T1 + B.T2), z=20)
    jit = random.Random(i).randint(-3, 3) if F["printing"] else 0
    if t < B.T_TITULO2:
        pap, n = B.papel_em(B.RUIM, B.T1, t); F["slotVis"] = True
        cai = ease(seg(t, B.T_CAI, B.T_TITULO2)) if t > B.T_CAI else 0
        if t > B.T_ESTOURO:
            k = eob(seg(t, B.T_ESTOURO, B.T_ESTOURO + .22)); ca = B.carimbo("ESTOUROU", "R$ 112 acima do orçamento", 9, 1.6 - .6 * k)
            pap = pap.convert("RGBA"); pap.alpha_composite(ca, ((B.PW - ca.width) // 2, max(0, pap.height - ca.height - 150))); pap = pap.convert("RGB")
        y = B.SLOT - pap.height + int(cai * 1300); s = 1.0; ang = cai * -14
        F.update(x=B.PX, y=y, s=s, ang=ang, jit=0 if cai else jit, fall=cai, rx=cai * .9, ry=cai * .35, z=20 + cai * 180, wave=1 if F["printing"] else 0)
    else:
        pap, n = B.papel_em(B.BOM, B.T2, t)
        if t > B.T_CARIMBO:
            k = eob(seg(t, B.T_CARIMBO, B.T_CARIMBO + .22)); ca = B.carimbo("DENTRO DO", "ORÇAMENTO · sobrou R$ 22", -7, 1.7 - .7 * k)
            pap = pap.convert("RGBA"); pap.alpha_composite(ca, (B.PW - ca.width - 20, max(0, pap.height - ca.height - 190))); pap = pap.convert("RGB")
        rasga = ease(seg(t, B.T_CTA, B.T_CTA + .55)); s = 1 - .4 * rasga
        y = (B.SLOT - pap.height) * (1 - rasga) + 610 * rasga
        F.update(x=(W - B.PW * s) / 2 if rasga > 0 else B.PX, y=y, s=s, ang=-4 * rasga, jit=jit if rasga == 0 else 0, fall=0, rx=-.12 * rasga, ry=0, wave=1 if F["printing"] else 0)
        F["slotVis"] = rasga < 1; F["slotY"] = B.SLOT + 20 + rasga * 400
    F["w"], F["h"] = pap.width, pap.height; F["bend"] = clamp(pap.height / 1300) * (1 - F["fall"])
    key = (t < B.T_TITULO2, n, round(pap.height), tuple(pap.getpixel((B.PW // 2, min(pap.height - 1, max(0, pap.height - 200)))) if pap.height > 1 else ()), round(t * 30) if (t > B.T_ESTOURO and t < B.T_ESTOURO + .3) or (t > B.T_CARIMBO and t < B.T_CARIMBO + .3) else 0)
    if cache.get("key") != key:
        p = os.path.join(TEX, f"p{i:05d}.png"); textura(pap).save(p); cache["key"] = key; cache["tex"] = p
    F["tex"] = cache["tex"]; return F

def prep():
    cache = {}; frames = [estado(i, cache) for i in range(N)]
    T = dict(estouro=B.T_ESTOURO, cai=B.T_CAI, titulo2=B.T_TITULO2, carimbo=B.T_CARIMBO, cta=B.T_CTA)
    json.dump(dict(T=T, dur=B.DUR, frames=frames), open("/tmp/glp_B.json", "w")); print("frames", N, "texturas", len(set(f["tex"] for f in frames)))

def txt(L, y, s, font, col, a):
    if a <= .01: return
    w = font.getlength(s); x = int((W - w) / 2); hh = int(font.size * 1.6)
    m = Image.new("L", (W, hh), 0); ImageDraw.Draw(m).text((x, 8), s, font=font, fill=int(170 * a)); m = m.filter(ImageFilter.GaussianBlur(12))
    s_ = Image.new("RGBA", (W, hh), (30, 0, 0, 0)); s_.putalpha(m); L.alpha_composite(s_, (0, y - 6))
    t = Image.new("RGBA", (W, hh), (0, 0, 0, 0)); ImageDraw.Draw(t).text((x, 8), s, font=font, fill=col + (int(255 * a),)); L.alpha_composite(t, (0, y - 6))

F_T1, F_T1i, F_URL, F_SM = B.F_T1, B.F_T1i, B.F_URL, B.F_SM
GOLD, CREAM, RED = B.GOLD, B.CREAM, B.RED
def overlay(base, i):
    t = i / FPS; L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < B.T_TITULO2: txt(L, 330, "Natal passado:", F_T1, CREAM, ease(seg(t, .05, .4)))
    else:
        txt(L, 330, "Este Natal:", F_T1i, GOLD, ease(seg(t, B.T_TITULO2, B.T_TITULO2 + .35)) * (1 - ease(seg(t, B.T_CTA - .2, B.T_CTA + .2))))
    if t >= B.T_CTA:
        a2 = ease(seg(t, B.T_CTA + .3, B.T_CTA + .7)); txt(L, 300, "Monte o seu Natal", B.fr(84, 600), CREAM, a2); txt(L, 392, "no orçamento.", B.fr(84, 500, True), GOLD, a2)
        a3 = ease(seg(t, B.T_CTA + .7, B.T_CTA + 1.1)); bw, bh, by = 840, 124, 1440
        gl = Image.new("RGBA", (W, bh + 160), (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle(((W - bw) / 2, 80, (W + bw) / 2, 80 + bh), 62, fill=GOLD + (int(140 * a3 * (.7 + .3 * math.sin(t * 5))),))
        L.alpha_composite(gl.filter(ImageFilter.GaussianBlur(26)), (0, by - 80))
        bt = Image.new("RGBA", (W, bh), (0, 0, 0, 0)); ImageDraw.Draw(bt).rounded_rectangle(((W - bw) / 2, 0, (W + bw) / 2, bh), 62, fill=GOLD + (int(255 * a3),)); L.alpha_composite(bt, (0, by))
        tt = Image.new("RGBA", (W, bh), (0, 0, 0, 0)); w = F_URL.getlength("natal.ofertadorafa.com.br"); ImageDraw.Draw(tt).text(((W - w) / 2, 34), "natal.ofertadorafa.com.br", font=F_URL, fill=RED + (int(255 * a3),)); L.alpha_composite(tt, (0, by))
        txt(L, by + 160, B.SUB_CTA, F_SM, CREAM, a3)
    im = base.convert("RGBA"); im.alpha_composite(L); return im.convert("RGB")

def comp():
    efe = B.audio(); pv = "/tmp/vozBgl.wav"
    with wave.open(pv, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(voz, -1, 1) * 32767).astype(np.int16).tobytes())
    mp4 = os.path.join(B.OUT, "natal_b_gl.mp4")
    filtro = ("[1:a]asplit=2[v1][v2];[2:a]volume=0.8[e];[e][v1]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=300[duck];"
              "[duck][v2]amix=inputs=2:weights='0.75 1':normalize=0,loudnorm=I=-15:TP=-1.5[a]")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", pv, "-i", efe,
                           "-filter_complex", filtro, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                           "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    th = []; marcas = [int(x * FPS) for x in (5.0, 9.5, 11.5, 18.0, 23.5, 27.0)]
    for i in range(N):
        f = overlay(Image.open(f"/tmp/glf_B/f{i:05d}.jpg").convert("RGB"), i); ff.stdin.write(f.tobytes())
        if i in marcas: th.append(f.resize((216, 384)))
    ff.stdin.close(); ff.wait()
    sh = Image.new("RGB", (226 * len(th) + 10, 404), (20, 6, 5))
    for k, t_ in enumerate(th): sh.paste(t_, (10 + k * 226, 10))
    sh.save(os.path.join(B.OUT, "contato_b_gl.png"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf", "crop=1080:1350:0:285", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "copy", "-movflags", "+faststart", mp4.replace(".mp4", "_4x5.mp4")])
    print(mp4, round(B.DUR, 1))

if __name__ == "__main__":
    {"prep": prep, "comp": comp}[_CMD]()
