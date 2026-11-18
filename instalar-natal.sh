#!/usr/bin/env bash
# Natal do Rafa — publica natal.ofertadorafa.com.br no Caddy (Docker) do painel achadinhos,
# com contador de visitas próprio. Não mexe no app do painel nem no Casa Sem Apagão.
# Uso: curl -fsSL https://raw.githubusercontent.com/rafaelgomes90/natal/<SHA>/instalar-natal.sh | sudo bash
set -euo pipefail

SITE="${DOMINIO_SITE:-natal.ofertadorafa.com.br}"
PROJ="/home/rafael/achadinhos"
WWW="/var/www/natal"
REPO="https://github.com/rafaelgomes90/natal.git"
CADDYFILE="$PROJ/Caddyfile"
OVERRIDE="$PROJ/docker-compose.override.yml"
KEYFILE="$PROJ/.painel_key_natal"
TS=$(date +%Y%m%d%H%M%S)

cd "$PROJ"
if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi
[ -f "$CADDYFILE" ] || { echo "!! Não achei $CADDYFILE"; exit 1; }
[ -f "$OVERRIDE" ] || { echo "!! Não achei $OVERRIDE (rode antes o do Casa Sem Apagão)"; exit 1; }

echo "==> Baixando/atualizando o site em $WWW"
command -v git >/dev/null || { apt-get update -qq; DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git >/dev/null; }
git config --global --get-all safe.directory 2>/dev/null | grep -qx "$WWW" || git config --global --add safe.directory "$WWW"
if [ -d "$WWW/.git" ]; then git -C "$WWW" pull -q; else rm -rf "$WWW"; git clone -q "$REPO" "$WWW"; fi
chmod -R a+rX "$WWW"
echo "* * * * * root git -C $WWW pull -q >/dev/null 2>&1 && chmod -R a+rX $WWW" > /etc/cron.d/natal

echo "==> Chave do painel de visitas"
[ -s "$KEYFILE" ] || head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 20 > "$KEYFILE"
chmod 600 "$KEYFILE"; KEY=$(cat "$KEYFILE")
mkdir -p "$PROJ/visitas-natal-data"

echo "==> Backup"
cp "$CADDYFILE" "$CADDYFILE.bak-$TS"
cp "$OVERRIDE" "$OVERRIDE.bak-$TS"

desfazer() {
  echo "!! Algo deu errado — voltando a configuração anterior"
  cat "$CADDYFILE.bak-$TS" > "$CADDYFILE"
  cat "$OVERRIDE.bak-$TS" > "$OVERRIDE"
  docker rm -f achadinhos-visitas-natal-1 >/dev/null 2>&1 || true
  $DC up -d --no-deps caddy >/dev/null 2>&1 || true
  $DC exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null 2>&1 || $DC restart caddy
  exit 1
}

echo "==> Caddyfile: bloco do $SITE (editado no lugar)"
if ! grep -q "root \* /srv/natal" "$CADDYFILE"; then
  { cat "$CADDYFILE.bak-$TS"; cat <<CADDY

# Natal do Rafa (site estático + contador de visitas)
$SITE {
	root * /srv/natal
	reverse_proxy /api/* visitas-natal:8787
	encode gzip
	@bloqueado path /.git* *.sh *.md *.py
	respond @bloqueado 404
	@estaticos path *.svg *.webp *.png *.jpg *.mp4
	header @estaticos Cache-Control "public, max-age=604800"
	@paginas path / *.html *.js *.css *.json
	header @paginas Cache-Control "no-cache"
	file_server
}
CADDY
  } > "$CADDYFILE.novo"
  cat "$CADDYFILE.novo" > "$CADDYFILE"; rm -f "$CADDYFILE.novo"
fi

echo "==> docker-compose.override.yml: pasta do site no Caddy + contador do Natal"
if ! grep -q "/srv/natal" "$OVERRIDE"; then
  LINHA=$(grep -n "/srv/casasemapagao" "$OVERRIDE" | head -1 | cut -d: -f1)
  [ -n "$LINHA" ] || desfazer
  IND=$(sed -n "${LINHA}p" "$OVERRIDE" | sed -E 's/^( *).*/\1/')
  { head -n "$LINHA" "$OVERRIDE.bak-$TS"; echo "${IND}- $WWW:/srv/natal:ro"; tail -n +"$((LINHA+1))" "$OVERRIDE.bak-$TS"; } > "$OVERRIDE.novo"
  cat "$OVERRIDE.novo" > "$OVERRIDE"; rm -f "$OVERRIDE.novo"
fi
if ! grep -q "visitas-natal:" "$OVERRIDE"; then
  cat >> "$OVERRIDE" <<YML
  visitas-natal:
    image: python:3.12-alpine
    restart: unless-stopped
    command: python -u /app/server.py
    environment:
      - PAINEL_KEY=$KEY
      - DB=/data/visitas.db
      - TZ=America/Fortaleza
    volumes:
      - $WWW/painel:/app:ro
      - ./visitas-natal-data:/data
YML
fi
chown rafael:rafael "$CADDYFILE" "$OVERRIDE" 2>/dev/null || true

echo "==> Validando"
$DC config -q || desfazer
DOM=$(grep -E '^DOMINIO=' .env | head -1 | cut -d= -f2- | tr -d "\"' ")
docker run --rm -e DOMINIO="$DOM" -v "$CADDYFILE:/etc/caddy/Caddyfile:ro" caddy:2 caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null || desfazer

echo "==> Subindo o contador e o Caddy com a pasta nova (o app do painel não é tocado)"
$DC up -d --no-deps visitas-natal caddy || desfazer
sleep 4
if $DC exec -T caddy grep -q "/srv/natal" /etc/caddy/Caddyfile 2>/dev/null; then
  $DC exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile || $DC restart caddy
else
  echo "   Caddy com o arquivo antigo preso; reiniciando (uns segundos)"; $DC restart caddy
fi
sleep 5

echo "==> Conferindo"
P=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 --resolve "$DOM:443:127.0.0.1" "https://$DOM/" || echo 000)
E=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 --resolve "energia.ofertadorafa.com.br:443:127.0.0.1" "https://energia.ofertadorafa.com.br/" || echo 000)
echo "   painel achadinhos: HTTP $P · Casa Sem Apagão: HTTP $E"
[ "$P" = "000" ] && desfazer
S=000
for i in 1 2 3 4 5 6; do
  S=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 --resolve "$SITE:443:127.0.0.1" "https://$SITE/" || echo 000)
  [ "$S" = "200" ] && break; sleep 10
done
A=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 --resolve "$SITE:443:127.0.0.1" "https://$SITE/api/painel?k=$KEY" || echo 000)
echo "   Natal do Rafa: HTTP $S · contador: HTTP $A"
if [ "$S" = "200" ]; then
  echo
  echo "Pronto: https://$SITE"
  echo "Painel de visitas (guarde, tem a chave): https://$SITE/painel/#k=$KEY"
else
  echo "Tudo instalado. O certificado do $SITE ainda não saiu: confira se o DNS já aponta pro IP da VPS."
  echo "Ele sai sozinho quando o DNS propagar. Painel: https://$SITE/painel/#k=$KEY"
  echo "Log: sudo docker logs --tail 30 achadinhos-caddy-1"
fi
