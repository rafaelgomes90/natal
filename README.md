# Natal do Rafa

Quiz que monta a decoração de Natal completa dentro do orçamento (5 faixas, R$ 200 a R$ 1.200), com produtos do Mercado Livre (links de afiliado). No ar em https://natal.ofertadorafa.com.br

- `produtos.json`: catálogo (papel no kit, altura, estilo, nota, comissão, link meli.la). Edite aqui e rode `python3 build.py`.
- `assets/quiz.js`: perguntas e montador do kit (1 item por papel obrigatório + extras até caber).
- `assets/app.js`: pixel (4651558238447028), UTM, cliques e contador de visitas.
- `painel/`: contador de visitas (Python puro + SQLite). Painel em `/painel/#k=CHAVE`.
- `instalar-natal.sh`: publica na VPS (Caddy em Docker do painel achadinhos). A VPS puxa o repo a cada minuto.
- Ao mudar CSS/JS, suba `V` no `build.py` (cache).
