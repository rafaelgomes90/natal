/* Natal do Rafa — funções comuns: UTM, pixel e clique pro Mercado Livre */
(function(){
  var KEY='nr_utm';
  try{ var sp=new URLSearchParams(location.search), u={};
    ['utm_source','utm_medium','utm_campaign','utm_content'].forEach(function(k){ var v=sp.get(k); if(v) u[k]=v; });
    if(Object.keys(u).length) sessionStorage.setItem(KEY, JSON.stringify(u));
  }catch(e){}
  function utm(){ try{ var u=JSON.parse(sessionStorage.getItem(KEY)||'{}'), o={}; if(u.utm_campaign) o.utm_campaign=u.utm_campaign; if(u.utm_content) o.utm_content=u.utm_content; return o; }catch(e){ return {}; } }
  function merge(a,b){ a=a||{}; for(var k in b) a[k]=b[k]; return a; }
  var CSA = window.CSA = {
    track:function(ev,p){ try{ if(window.fbq) window.fbq('track',ev,merge(p,utm())); }catch(e){} },
    trackC:function(ev,p){ try{ if(window.fbq) window.fbq('trackCustom',ev,merge(p,utm())); }catch(e){} },
    brl:function(n){ return Number(n).toLocaleString('pt-BR',{maximumFractionDigits:0}); },
    esc:function(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); },
    byId:{}
  };
  (window.PRODUTOS||[]).forEach(function(p){ CSA.byId[p.id]=p; });

  // Qualquer <a data-ml="id"> (foto, nome ou botão) dispara os mesmos eventos antes de abrir o Mercado Livre
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('a[data-ml]'); if(!a) return;
    var p = CSA.byId[a.getAttribute('data-ml')]; if(!p) return;
    CSA.track('InitiateCheckout',{content_name:p.nome,content_ids:[p.id],content_type:'product',content_category:p.papel,value:p.precoAprox,currency:'BRL'});
    CSA.trackC('CliqueML',{produto:p.nome,produto_id:p.id,categoria:p.papel,etiqueta:p.etiqueta,origem:a.getAttribute('data-origem')||'',pagina:location.pathname});
  });

  // Página de produto: ViewContent do produto
  var pid = document.body.getAttribute('data-produto');
  if(pid && CSA.byId[pid]){ var p=CSA.byId[pid];
    CSA.track('ViewContent',{content_name:p.nome,content_ids:[p.id],content_type:'product',content_category:p.papel,value:p.precoAprox,currency:'BRL'});
  }

  // Contador de visitantes (painel): visita, "estou online" a cada 20s e clique pro ML
  var HIT='/api/hit', sid;
  try{ sid=sessionStorage.getItem('nr_sid'); if(!sid){ sid=Math.random().toString(36).slice(2)+Date.now().toString(36); sessionStorage.setItem('nr_sid',sid); } }catch(e){ sid='x'+Math.random().toString(36).slice(2); }
  function hit(t,prod){ try{
    var u={}; try{ u=JSON.parse(sessionStorage.getItem(KEY)||'{}'); }catch(e){}
    var body=JSON.stringify({t:t,sid:sid,p:location.pathname,prod:prod||'',src:u.utm_source||(document.referrer?new URL(document.referrer).hostname:''),ad:u.utm_content||''});
    if(navigator.sendBeacon) navigator.sendBeacon(HIT,new Blob([body],{type:'application/json'}));
    else fetch(HIT,{method:'POST',body:body,headers:{'Content-Type':'application/json'},keepalive:true});
  }catch(e){} }
  CSA.hit=hit;
  hit('view');
  setInterval(function(){ if(document.visibilityState==='visible') hit('ping'); },20000);
  document.addEventListener('visibilitychange',function(){ if(document.visibilityState==='visible') hit('ping'); });
  document.addEventListener('click',function(e){ var g=e.target.closest&&e.target.closest('a[data-grupo]'); if(!g) return;
    hit('click','Grupo WhatsApp'); CSA.track('Lead',{content_name:'Grupo Oferta do Rafa',origem:g.getAttribute('data-grupo'),pagina:location.pathname}); });
  document.addEventListener('click',function(e){ var a=e.target.closest&&e.target.closest('a[data-ml]'); if(!a) return; var p=CSA.byId[a.getAttribute('data-ml')]; hit('click',p?p.nome:a.getAttribute('data-ml')); });

  // Barra fixa do celular: aparece depois que o primeiro CTA sai da tela
  var flut=document.getElementById('flut'), alvo=document.querySelector('[data-flut-alvo]');
  if(flut && alvo && 'IntersectionObserver' in window){
    new IntersectionObserver(function(es){ var on=!(es[0]&&es[0].isIntersecting); flut.classList.toggle('on',on); flut.setAttribute('aria-hidden',String(!on)); }).observe(alvo);
  }
})();
