"""Plano B com a voz do Rafael ('Natal passado eu fiz assim...'): cada linha do cupom sai na palavra falada.
Uso: python3 video_natal_b_voz.py <voz.wav>  → video/natal_b_voz.mp4 (9:16) + _4x5.mp4"""
import os, sys, wave, subprocess
import numpy as np
from PIL import Image
import video_natal_b as B

VOZ = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/voz/baseB.wav"
with wave.open(VOZ) as w: SR = w.getframerate(); voz = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)/32768
voz = voz[:int(24.45*SR)]; voz = np.concatenate([voz, np.zeros(int(.9*SR))])
B.DUR = len(voz)/SR
# tempos tirados das palavras (faster-whisper)
B.T1 = [1.15, 1.35, 1.55, 2.30, 4.00, 5.50, 5.90, 6.30, 6.55, 6.75, 6.95, 7.10]
B.T2 = [11.20, 13.45, 13.80, 14.10, 15.42, 15.96, 16.55, 17.00, 17.66, 18.05, 18.32, 18.85, 19.35]
B.T_ESTOURO, B.T_CAI, B.T_TITULO2 = 7.62, 9.45, 10.40
B.T_CARIMBO = 19.75
B.T_CTA = 21.25
B.SUB_CTA = "toque em Saiba mais e monte o seu"
assert len(B.T1) == len(B.RUIM) and len(B.T2) == len(B.BOM)

efe = B.audio()  # grava sfx_b.wav com os tempos novos
pv = "/tmp/vozB.wav"
with wave.open(pv, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(voz, -1, 1)*32767).astype(np.int16).tobytes())
mp4 = os.path.join(B.OUT, "natal_b_voz.mp4")
filtro = ("[1:a]asplit=2[v1][v2];[2:a]volume=0.8[e];[e][v1]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=300[duck];"
          "[duck][v2]amix=inputs=2:weights='0.75 1':normalize=0,loudnorm=I=-15:TP=-1.5[a]")
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{B.W}x{B.H}", "-r", str(B.FPS), "-i", "-",
                       "-i", pv, "-i", efe, "-filter_complex", filtro, "-map", "0:v", "-map", "[a]",
                       "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                       "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
N = int(B.DUR * B.FPS); marcas = [int(x*B.FPS) for x in (5.0, 8.3, 9.9, 16.2, 20.4, 23.5)]; th = []
for i in range(N):
    f = B.frame(i); ff.stdin.write(f.tobytes())
    if i in marcas: th.append(f.resize((216, 384)))
ff.stdin.close(); ff.wait()
sh = Image.new("RGB", (226*len(th) + 10, 404), (20, 6, 5))
for k, t in enumerate(th): sh.paste(t, (10 + k*226, 10))
sh.save(os.path.join(B.OUT, "contato_b_voz.png"))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf", "crop=1080:1350:0:285", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "22", "-c:a", "copy", "-movflags", "+faststart", mp4.replace(".mp4", "_4x5.mp4")])
print(mp4, round(B.DUR, 1))
