/* Natal do Rafa — quiz + montador de kit dentro do orçamento */
(function(){
  var P = window.PRODUTOS || [], CSA = window.CSA || {track:function(){},trackC:function(){},brl:function(n){return n},esc:function(s){return s}};
  var brl = function(n){ return Number(Math.round(n)).toLocaleString('pt-BR'); };
  var esc = CSA.esc;
  var ORC = [200, 350, 500, 800, 1200];
  var NOME_PAPEL = {arvore:'Árvore', luzes:'Pisca-pisca', bolas:'Bolas', ponteira:'Ponteira', saia:'Saia da árvore', festao:'Festão',
    lacos:'Laços', destaque:'Bolas de destaque', guirlanda:'Guirlanda da porta', janela:'Luz da janela', mesa:'Mesa da ceia', almofadas:'Sala', papai:'Peça de destaque'};
  var OBRIG = ['arvore','luzes','bolas','ponteira','saia'];
  var EXTRAS = ['festao','lacos','guirlanda','destaque','janela','mesa','almofadas','papai'];
  var ESTILO_TXT = {classico:'clássico vermelho e dourado', nevado:'nevado, branco e prata', dourado:'dourado, champagne e rosê', tanto:'o mais bonito pelo preço'};
  var COR_DICA = {classico:'vermelho e dourado', nevado:'prata e branco', dourado:'dourado ou champagne', tanto:'a que combinar com a sua sala'};

  var PERGUNTAS = [
    {k:'orc', t:'Quanto você quer gastar na decoração?', s:'Valor total, somando tudo.', op:ORC.map(function(v){ return {v:v, l:'Até R$ '+brl(v), d:v<=200?'kit essencial':v<=500?'árvore + tudo o que precisa':v<=800?'árvore caprichada + porta e mesa':'casa toda no clima'}; })},
    {k:'tam', t:'Onde a árvore vai ficar?', s:'Isso define a altura.', op:[
      {v:'P', l:'Cantinho ou apartamento pequeno', d:'árvore de 1,20 a 1,50 m'},
      {v:'M', l:'Sala normal', d:'árvore de 1,80 m'},
      {v:'G', l:'Sala grande ou pé-direito alto', d:'árvore de 2,10 a 2,40 m'}]},
    {k:'est', t:'Qual estilo combina com a sua casa?', s:'As cores das bolas a gente indica em cada item.', op:[
      {v:'classico', l:'Clássico', d:'verde, vermelho e dourado', sw:['#1F5A3D','#B3261E','#E9B949']},
      {v:'nevado', l:'Nevado', d:'branco, prata e um toque de vermelho', sw:['#EEF2F0','#B9C4C9','#B3261E']},
      {v:'dourado', l:'Dourado elegante', d:'dourado, champagne e rosê', sw:['#E9B949','#E8D3B0','#D9A5A0']},
      {v:'tanto', l:'Tanto faz', d:'quero o mais bonito pelo preço', sw:['#1F5A3D','#E9B949','#FBF7EF']}]},
    {k:'tem', t:'Você já tem alguma coisa?', s:'Marque o que não precisa comprar.', multi:true, op:[
      {v:'arvore', l:'Já tenho a árvore'}, {v:'luzes', l:'Já tenho pisca-pisca'}, {v:'bolas', l:'Já tenho bolas e enfeites'}]}
  ];

  var R = {orc:null, tam:null, est:null, tem:[]}, passo = 0;
  var corpo = document.getElementById('q-corpo'), bar = document.getElementById('q-bar'), quiz = document.getElementById('quiz'), kitEl = document.getElementById('kit');
  if(!corpo) return;

  // orçamento vindo do anúncio: ?orc=500
  try{ var o = +new URLSearchParams(location.search).get('orc'); if(ORC.indexOf(o) >= 0){ R.orc = o; passo = 1; } }catch(e){}

  function render(){
    var q = PERGUNTAS[passo];
    bar.style.width = (100 * passo / PERGUNTAS.length) + '%';
    var h = '<p class="q-n">Pergunta '+(passo+1)+' de '+PERGUNTAS.length+'</p><h2>'+q.t+'</h2><p class="q-s">'+q.s+'</p><div class="q-op'+(q.k=='orc'?' orc':'')+'">';
    q.op.forEach(function(o){
      var on = q.multi ? R.tem.indexOf(o.v) >= 0 : R[q.k] === o.v;
      h += '<button type="button" class="op'+(on?' on':'')+'" data-v="'+o.v+'" aria-pressed="'+on+'">'+
        (o.sw ? '<span class="sw">'+o.sw.map(function(c){return '<i style="background:'+c+'"></i>';}).join('')+'</span>' : '')+
        '<b>'+o.l+'</b>'+(o.d?'<small>'+o.d+'</small>':'')+'</button>';
    });
    h += '</div><div class="q-nav">'+(passo>0?'<button type="button" class="volta">← Voltar</button>':'<span></span>')+
      (q.multi?'<button type="button" class="segue">'+(R.tem.length?'Montar meu kit':'Não tenho nada, montar tudo')+' →</button>':'')+'</div>';
    corpo.innerHTML = h;
  }

  corpo.addEventListener('click', function(ev){
    var b = ev.target.closest('button'); if(!b) return;
    var q = PERGUNTAS[passo];
    if(b.classList.contains('volta')){ passo--; render(); return; }
    if(b.classList.contains('segue')){ concluir(); return; }
    var v = b.getAttribute('data-v'); if(!v) return;
    if(q.multi){
      var i = R.tem.indexOf(v); if(i >= 0) R.tem.splice(i,1); else R.tem.push(v);
      if(R.tem.length === 3){ R.tem = ['arvore','luzes','bolas']; }
      render(); return;
    }
    R[q.k] = q.k == 'orc' ? +v : v;
    if(q.k == 'orc') CSA.trackC('QuizOrcamento', {faixa:'ate_'+v});
    passo++; render();
  });

  // ------------------------------------------------------------ montador
  function score(p){
    var s = p.nota*10 + Math.log(p.avaliacoes+1)/Math.LN10*4 + p.comissao*0.5;
    if(p.estilo && R.est !== 'tanto' && p.estilo.indexOf(R.est) >= 0) s += 12;
    if(p.papel !== 'arvore' && R.orc >= 500) s += p.precoAprox*0.12;
    if(p.selo) s += 2;
    return s;
  }
  var ALT = {P:[1.2,1.5], M:[1.8], G:[2.1,2.4]};
  function ledsNec(alt){ return Math.ceil(alt*150/100)*100; }
  function bolasNec(alt){ return Math.ceil(alt*30/10)*10; }
  function qtd(p, alt){
    if(p.papel === 'luzes' && p.leds) return Math.min(4, Math.ceil(ledsNec(alt)/p.leds));
    if(p.papel === 'bolas' && p.qtd) return Math.min(4, Math.ceil(bolasNec(alt)/p.qtd));
    return 1;
  }
  function custo(p, alt){ return p.precoAprox * qtd(p, alt); }
  function porPapel(papel){ return P.filter(function(p){ return p.papel === papel; }).sort(function(a,b){ return score(b)-score(a); }); }

  function montar(){
    var orc = R.orc, alt = R.tam === 'P' ? 1.5 : R.tam === 'M' ? 1.8 : 2.1, aviso = '';
    var precisa = OBRIG.filter(function(r){ return R.tem.indexOf(r) < 0; });
    var kit = [], gasto = 0;
    function minRest(papeis, a){ return papeis.reduce(function(s,r){ var c = porPapel(r).map(function(p){ return custo(p,a); }); return s + (c.length ? Math.min.apply(null,c) : 0); }, 0); }
    function semCobertos(papeis, item){ return papeis.filter(function(r){ return !(item.cobre && item.cobre.indexOf(r) >= 0); }); }

    if(precisa.indexOf('arvore') >= 0){
      var tamanhos = ALT[R.tam], tentativas = [tamanhos].concat(R.tam==='G'?[ALT.M,ALT.P]:R.tam==='M'?[ALT.P]:[]), escolhida = null;
      for(var t=0; t<tentativas.length && !escolhida; t++){
        var cands = porPapel('arvore').filter(function(p){ return tentativas[t].indexOf(p.altura) >= 0; });
        var viaveis = cands.filter(function(p){ return p.precoAprox + minRest(semCobertos(precisa.slice(1), p), p.altura) <= orc; });
        if(!viaveis.length) continue;
        // a árvore pode levar até ~55% do orçamento (a já decorada, mais); acima disso, só se nada couber
        var dentro = viaveis.filter(function(p){ return p.precoAprox <= orc*(p.cobre && p.cobre.indexOf('luzes')>=0 ? 0.85 : 0.55); });
        var lista = dentro.length ? dentro : viaveis;
        lista.sort(function(a,b){ return (score(b) + 15*b.precoAprox/orc + (b.cobre && orc>=500 ? -25 : 0)) - (score(a) + 15*a.precoAprox/orc + (a.cobre && orc>=500 ? -25 : 0)); });
        escolhida = lista[0];
        if(t > 0) aviso = 'Com R$ '+brl(orc)+' não coube uma árvore do tamanho que você pediu com todo o resto, então escolhemos uma de '+escolhida.altura.toFixed(2).replace('.',',')+' m. Se preferir a maior, troque a árvore abaixo.';
      }
      if(!escolhida){ escolhida = porPapel('arvore').sort(function(a,b){ return a.precoAprox-b.precoAprox; })[0]; aviso = 'O orçamento ficou apertado; montamos o mais barato possível.'; }
      alt = escolhida.altura;
      kit.push({p:escolhida, q:1}); gasto += escolhida.precoAprox;
      precisa = semCobertos(precisa.slice(1), escolhida);
    } else { precisa = precisa.filter(function(r){ return r !== 'arvore'; }); }

    // demais itens obrigatórios: melhor nota que ainda deixa espaço pros próximos
    for(var i=0; i<precisa.length; i++){
      var r = precisa[i], resto = precisa.slice(i+1);
      var ok = porPapel(r).filter(function(p){ return gasto + custo(p,alt) + minRest(semCobertos(resto,p), alt) <= orc; });
      var esc2 = ok[0] || porPapel(r).sort(function(a,b){ return custo(a,alt)-custo(b,alt); })[0];
      if(!esc2) continue;
      kit.push({p:esc2, q:qtd(esc2,alt)}); gasto += custo(esc2,alt);
      if(esc2.cobre){ precisa = precisa.slice(0,i+1).concat(semCobertos(resto, esc2)); }
    }
    // extras pela ordem de impacto, enquanto couber
    EXTRAS.forEach(function(r){
      var ok = porPapel(r).filter(function(p){ return gasto + p.precoAprox <= orc; });
      if(ok.length){ kit.push({p:ok[0], q:1, extra:true}); gasto += ok[0].precoAprox; }
    });
    return {itens:kit, alt:alt, aviso:aviso};
  }

  var KIT = null;
  function total(){ return KIT.itens.reduce(function(s,it){ return s + it.p.precoAprox*it.q; }, 0); }

  function itemHTML(it, idx){
    var p = it.p, alts = porPapel(p.papel).length;
    var dica = p.dica ? '<span class="dica">Dica: '+p.dica.replace('no anúncio','')+'<b>'+COR_DICA[R.est]+'</b> no anúncio</span>' : '';
    var inclui = p.cobre ? '<span class="dica">Já inclui '+p.cobre.map(function(c){ return NOME_PAPEL[c].toLowerCase(); }).join(' e ')+'</span>' : '';
    return '<li class="it" data-i="'+idx+'">'+
      '<a class="it-foto" href="'+esc(p.link)+'" target="_blank" rel="noopener sponsored" data-ml="'+p.id+'" data-origem="kit-foto"><img src="'+esc(p.imagem)+'" alt="" loading="lazy"></a>'+
      '<div class="it-tx"><span class="papel">'+NOME_PAPEL[p.papel]+(it.q>1?' · '+it.q+' unidades':'')+'</span>'+
      '<a class="it-nome" href="'+esc(p.link)+'" target="_blank" rel="noopener sponsored" data-ml="'+p.id+'" data-origem="kit-nome">'+esc(p.nome)+'</a>'+
      '<span class="it-aval">★ '+String(p.nota.toFixed(1)).replace('.',',')+' · '+brl(p.avaliacoes)+' avaliações</span>'+inclui+dica+
      '<div class="it-pr"><b>R$ '+brl(p.precoAprox*it.q)+'</b>'+(it.q>1?'<small>'+it.q+' × R$ '+brl(p.precoAprox)+'</small>':'')+'</div>'+
      '<div class="it-bt"><a class="ml" href="'+esc(p.link)+'" target="_blank" rel="noopener sponsored" data-ml="'+p.id+'" data-origem="kit-botao">Comprar no Mercado Livre</a>'+
      (alts>1?'<button type="button" class="troca" data-i="'+idx+'">Trocar</button>':'')+
      (it.extra?'<button type="button" class="tira" data-i="'+idx+'" aria-label="Tirar do kit">Tirar</button>':'')+'</div></div></li>';
  }

  function desenhar(){
    var t = total(), sobra = R.orc - t;
    var temTxt = R.tem.length ? ' · já tem '+R.tem.map(function(r){ return NOME_PAPEL[r].toLowerCase(); }).join(', ') : '';
    kitEl.innerHTML =
      '<div class="kit-topo"><p class="eyebrow">'+(KIT.compartilhado?'Kit de Natal que te mandaram':'Seu Natal montado')+'</p><h2>Kit '+ESTILO_TXT[R.est]+', árvore de '+KIT.alt.toFixed(2).replace('.',',')+' m</h2>'+
      '<p class="kit-meta">Orçamento de R$ '+brl(R.orc)+temTxt+'</p></div>'+
      (KIT.aviso?'<p class="aviso">'+KIT.aviso+'</p>':'')+
      '<div class="soma"><div><small>Total aproximado</small><b>R$ '+brl(t)+'</b></div><div><small>'+(sobra>=0?'Sobra do orçamento':'Passou do orçamento')+'</small><b class="'+(sobra>=0?'ok':'neg')+'">R$ '+brl(Math.abs(sobra))+'</b></div><div><small>Itens</small><b>'+KIT.itens.length+'</b></div></div>'+
      '<ol class="itens">'+KIT.itens.map(itemHTML).join('')+'</ol>'+
      '<p class="como">Cada item abre no Mercado Livre: confira o preço do dia, coloque no carrinho e pague tudo junto lá. Preços mudam todo dia (às vezes caem com cupom).</p>'+
      '<div class="kit-acoes"><button type="button" class="refaz">Refazer com outro orçamento</button><button type="button" class="compartilha">Mandar o kit no WhatsApp</button></div>'+
      '<p class="salva"><button type="button" class="salva-img">Salvar a imagem do kit</button></p>';
    prepararImagem();
  }

  kitEl.addEventListener('click', function(ev){
    var b = ev.target.closest('button'); if(!b) return;
    if(b.classList.contains('refaz')){ kitEl.hidden = true; quiz.hidden = false; passo = 0; render(); quiz.scrollIntoView({behavior:'smooth', block:'start'}); return; }
    if(b.classList.contains('compartilha')){ compartilhar(); return; }
    if(b.classList.contains('salva-img')){ salvarImagem(); return; }
    var i = +b.getAttribute('data-i'), it = KIT.itens[i]; if(!it) return;
    if(b.classList.contains('tira')){ KIT.itens.splice(i,1); desenhar(); return; }
    if(b.classList.contains('troca')){
      var lista = porPapel(it.p.papel);
      if(it.p.papel === 'arvore'){ lista = lista.sort(function(a,b){ return a.altura-b.altura || a.precoAprox-b.precoAprox; }); }
      var j = (lista.indexOf(it.p) + 1) % lista.length, novo = lista[j];
      it.p = novo; it.q = qtd(novo, KIT.alt);
      if(novo.papel === 'arvore'){ KIT.alt = novo.altura; KIT.itens.forEach(function(x){ x.q = qtd(x.p, KIT.alt); }); }
      CSA.trackC('TrocouItem', {papel:novo.papel, produto_id:novo.id});
      desenhar();
      var li = kitEl.querySelector('.it[data-i="'+i+'"]'); if(li){ li.classList.add('novo'); }
    }
  });

  // ------------------------------------------------------------ WhatsApp: imagem do kit + texto formatado
  var EMOJI = {arvore:'🌲', luzes:'✨', bolas:'🔴', ponteira:'⭐', saia:'🎁', festao:'🌿', lacos:'🎀', destaque:'💎', guirlanda:'🚪', janela:'🪟', mesa:'🍽️', almofadas:'🛋️', papai:'🎅'};
  var SITE = location.origin + '/';
  function textoKit(comSiteNoTopo, linkKit){
    var t = Math.round(total()), l = [];
    if(linkKit) l.push('🎄 Olha o kit de Natal que eu montei: '+linkKit, '');
    else if(comSiteNoTopo) l.push('Monte o seu: '+SITE, '');
    l.push('🎄 *Meu kit de Natal*', 'Árvore de '+KIT.alt.toFixed(2).replace('.',',')+' m · estilo '+ESTILO_TXT[R.est].split(',')[0], '💰 *Total: ~R$ '+brl(t)+'*', '');
    KIT.itens.forEach(function(it){
      var p = it.p;
      l.push(EMOJI[p.papel]+' *'+NOME_PAPEL[p.papel]+'* · R$ '+brl(p.precoAprox*it.q)+(it.q>1?' ('+it.q+'x)':''));
      l.push(p.nome);
      l.push('👉 '+p.link, '');
    });
    l.push('_Preços aproximados do Mercado Livre; o valor do dia aparece no anúncio._');
    if(!comSiteNoTopo || linkKit) l.push('', 'Monte o seu em 30 segundos:', SITE);
    return l.join('\n');
  }
  var IMG_KIT = null, IMG_DATA = null, IMG_SEQ = 0, KIT_ID = null;
  function carregar(src){ return new Promise(function(ok){ var im = new Image(); im.onload = function(){ ok(im); }; im.onerror = function(){ ok(null); }; im.src = src; }); }
  function rr(c, x, y, w, h, r){ c.beginPath(); c.moveTo(x+r,y); c.arcTo(x+w,y,x+w,y+h,r); c.arcTo(x+w,y+h,x,y+h,r); c.arcTo(x,y+h,x,y,r); c.arcTo(x,y,x+w,y,r); c.closePath(); }
  function prepararImagem(){
    var seq = ++IMG_SEQ; IMG_KIT = null; IMG_DATA = null; KIT_ID = null;
    if(!window.HTMLCanvasElement || !window.Promise) return;
    var itens = KIT.itens.slice(0, 6), resto = KIT.itens.length - itens.length;
    var fontes = document.fonts ? Promise.all(['600 60px Fraunces','italic 500 60px Fraunces','700 40px Inter','600 30px Inter'].map(function(f){ return document.fonts.load(f).catch(function(){}); })) : Promise.resolve();
    Promise.all([fontes].concat(itens.map(function(it){ return carregar(it.p.imagem); }))).then(function(r){
      if(seq !== IMG_SEQ) return;
      var fotos = r.slice(1), W = 1080, H = 1350, cv = document.createElement('canvas'); cv.width = W; cv.height = H;
      var c = cv.getContext('2d');
      var g = c.createRadialGradient(W*.85, 0, 50, W*.85, 0, W*1.1); g.addColorStop(0,'#24503D'); g.addColorStop(.6,'#10291F'); c.fillStyle = g; c.fillRect(0,0,W,H);
      // fio de luz
      c.strokeStyle = '#2A3B31'; c.lineWidth = 4; c.beginPath();
      var cores = ['#E9B949','#F6DE9A','#C94F3D','#E9B949','#9CC9A8'];
      for(var i=0;i<13;i++){ var x = i*90, y = 24 + (i%2?22:0); i ? c.lineTo(x,y) : c.moveTo(x,y); } c.stroke();
      for(i=0;i<13;i++){ x = i*90; y = 24 + (i%2?22:0); c.save(); c.shadowColor = cores[i%5]; c.shadowBlur = 30; c.fillStyle = cores[i%5]; c.beginPath(); c.ellipse(x, y+28, 12, 19, 0, 0, 7); c.fill(); c.restore(); c.fillStyle = '#2A3B31'; c.fillRect(x-7, y, 14, 11); }
      c.textBaseline = 'alphabetic';
      c.fillStyle = '#E9B949'; c.font = '700 26px Inter, sans-serif'; c.fillText('MEU KIT DE NATAL', 60, 150);
      c.fillStyle = '#FBF7EF'; c.font = '600 60px Fraunces, Georgia, serif'; c.fillText('Árvore de '+KIT.alt.toFixed(2).replace('.',',')+' m', 60, 222);
      c.fillStyle = '#F6DE9A'; c.font = 'italic 500 50px Fraunces, Georgia, serif'; c.fillText('estilo '+ESTILO_TXT[R.est].split(',')[0], 60, 284);
      // cartão
      var cx = 60, cy = 320, cw = W-120, ch = 870; c.fillStyle = '#FBF7EF'; rr(c, cx, cy, cw, ch, 34); c.fill();
      var cols = itens.length > 4 ? 3 : 2, rows = Math.ceil(itens.length/cols), gap = 18, pad = 28;
      var tw = Math.min((cw - 2*pad - gap*(cols-1))/cols, (ch - 2*pad - 110 - rows*78 - (rows-1)*gap)/rows);
      var gx = cx + (cw - (cols*tw + (cols-1)*gap))/2;
      itens.forEach(function(it, k){
        var linha = Math.floor(k/cols), nrow = Math.min(cols, itens.length - linha*cols), off = (cols - nrow)*(tw+gap)/2;
        var x = gx + off + (k%cols)*(tw+gap), y = cy + pad + linha*(tw+78+gap), f = fotos[k];
        c.save(); rr(c, x, y, tw, tw, 18); c.clip(); c.fillStyle = '#fff'; c.fillRect(x, y, tw, tw);
        if(f){ var esc = Math.max(tw/f.width, tw/f.height); c.drawImage(f, x + (tw - f.width*esc)/2, y + (tw - f.height*esc)/2, f.width*esc, f.height*esc); }
        c.restore();
        c.fillStyle = '#2F7D4F'; c.font = '700 22px Inter, sans-serif'; c.fillText(NOME_PAPEL[it.p.papel].toUpperCase()+(it.q>1?' · '+it.q+'x':''), x+2, y+tw+32);
        c.fillStyle = '#1B2A22'; c.font = '700 32px Inter, sans-serif'; c.fillText('R$ '+brl(it.p.precoAprox*it.q), x+2, y+tw+68);
      });
      var ly = cy + ch - 100; c.fillStyle = '#E4DCCB'; c.fillRect(cx+pad, ly, cw-2*pad, 2);
      c.fillStyle = '#5E6B62'; c.font = '600 28px Inter, sans-serif'; c.fillText('Total aproximado'+(resto>0?' (+'+resto+' itens)':''), cx+pad, ly+62);
      c.fillStyle = '#B3261E'; c.font = '700 50px Inter, sans-serif'; c.textAlign = 'right'; c.fillText('R$ '+brl(total()), cx+cw-pad, ly+66); c.textAlign = 'left';
      c.fillStyle = '#E9B949'; rr(c, 60, 1218, W-120, 84, 24); c.fill();
      c.fillStyle = '#1B2A22'; c.font = '700 32px Inter, sans-serif'; c.textAlign = 'center'; c.fillText('Monte o seu: natal.ofertadorafa.com.br', W/2, 1271); c.textAlign = 'left';
      try{ IMG_DATA = cv.toDataURL('image/jpeg', .82); }catch(e){ IMG_DATA = null; }
      cv.toBlob(function(bl){ if(seq === IMG_SEQ && bl) IMG_KIT = new File([bl], 'meu-kit-de-natal.jpg', {type:'image/jpeg'}); }, 'image/jpeg', .9);
    });
  }
  function metaKit(){
    var t = Math.round(total());
    return {orc:R.orc, tam:R.tam, est:R.est, tem:R.tem, alt:KIT.alt, total:t,
      itens:KIT.itens.map(function(it){ return {id:it.p.id, q:it.q}; }),
      titulo:'Meu kit de Natal: árvore de '+KIT.alt.toFixed(2).replace('.',',')+' m por ~R$ '+brl(t),
      resumo:KIT.itens.map(function(it){ return NOME_PAPEL[it.p.papel]; }).join(', ')+'. Monte o seu no Natal do Rafa.'};
  }
  function salvarKit(){
    if(KIT_ID) return Promise.resolve(KIT_ID);
    if(!IMG_DATA || !window.fetch) return Promise.reject();
    return fetch('/api/kit', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({img:IMG_DATA, kit:metaKit()})})
      .then(function(r){ if(!r.ok) throw r.status; return r.json(); }).then(function(d){ KIT_ID = d.id; return d.id; });
  }
  function compartilhar(){
    CSA.trackC('CompartilhouKit', {total:Math.round(total())});
    var celular = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    var janela = celular ? null : window.open('about:blank', '_blank');
    var bt = kitEl.querySelector('.compartilha'); if(bt){ bt.disabled = true; bt.textContent = 'Abrindo o WhatsApp…'; }
    function ir(texto){
      var u = 'https://wa.me/?text='+encodeURIComponent(texto);
      if(janela){ janela.location = u; } else { location.href = u; }
      setTimeout(function(){ if(bt){ bt.disabled = false; bt.textContent = 'Mandar o kit no WhatsApp'; } }, 1500);
    }
    salvarKit().then(function(id){ ir(textoKit(false, location.origin+'/api/k/'+id)); }, function(){ ir(textoKit(true)); });
  }
  function salvarImagem(){
    var dados = IMG_KIT ? {files:[IMG_KIT]} : null;
    if(dados && navigator.canShare && navigator.canShare(dados)){ navigator.share(dados).catch(function(){}); return; }
    if(IMG_DATA){ var a = document.createElement('a'); a.href = IMG_DATA; a.download = 'meu-kit-de-natal.jpg'; document.body.appendChild(a); a.click(); a.remove(); }
  }
  function abrirWa(){ window.open('https://wa.me/?text='+encodeURIComponent(textoKit(true)), '_blank', 'noopener'); }

  // kit aberto por link compartilhado: /?kit=xxxxxxxx
  function abrirKitCompartilhado(id){
    fetch('/api/k/'+id+'.json').then(function(r){ if(!r.ok) throw 0; return r.json(); }).then(function(m){
      var by = {}; P.forEach(function(p){ by[p.id] = p; });
      var itens = (m.itens||[]).filter(function(i){ return by[i.id]; }).map(function(i){ return {p:by[i.id], q:i.q}; });
      if(!itens.length) throw 0;
      R.orc = ORC.indexOf(m.orc) >= 0 ? m.orc : 500; R.tam = m.tam || 'M'; R.est = ESTILO_TXT[m.est] ? m.est : 'tanto'; R.tem = m.tem || [];
      KIT = {itens:itens, alt:m.alt || 1.8, aviso:'', compartilhado:true};
      desenhar(); quiz.hidden = true; kitEl.hidden = false;
      CSA.trackC('AbriuKitCompartilhado', {total:m.total||0});
      if(CSA.hit) CSA.hit('quiz', 'Kit compartilhado aberto');
    }).catch(function(){ render(); });
  }

  function concluir(){
    bar.style.width = '100%';
    KIT = montar();
    desenhar();
    quiz.hidden = true; kitEl.hidden = false;
    kitEl.scrollIntoView({behavior:'smooth', block:'start'});
    var t = Math.round(total());
    CSA.trackC('QuizConcluido', {faixa:'ate_'+R.orc, tamanho:R.tam, estilo:R.est, total:t});
    CSA.track('ViewContent', {content_name:'Kit de Natal ate R$ '+R.orc, content_ids:KIT.itens.map(function(it){ return it.p.id; }), content_type:'product_group', value:t, currency:'BRL'});
    if(CSA.hit) CSA.hit('quiz', 'Até R$ '+brl(R.orc)+' · '+({P:'pequena',M:'média',G:'grande'})[R.tam]+' · '+R.est);
  }

  var kitParam = null; try{ kitParam = new URLSearchParams(location.search).get('kit'); }catch(e){}
  if(kitParam && /^[0-9a-f]{8}$/.test(kitParam)) abrirKitCompartilhado(kitParam); else render();
})();
