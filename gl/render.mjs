import http from 'http'; import fs from 'fs'; import path from 'path'; import puppeteer from 'puppeteer-core';
const [,, paramsFile, outDir, wArg='720', hArg='1280', fromArg='0', toArg='-1', stepArg='1'] = process.argv;
const P = JSON.parse(fs.readFileSync(paramsFile)); fs.mkdirSync(outDir,{recursive:true});
const root = path.dirname(new URL(import.meta.url).pathname);
const srv = http.createServer((q,r)=>{const u=decodeURIComponent(q.url.split('?')[0]);const f=u.startsWith('/tmp/')?u:path.join(root,u);fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}
  r.writeHead(200,{'Content-Type':f.endsWith('.js')||f.endsWith('.mjs')?'text/javascript':f.endsWith('.html')?'text/html':'application/octet-stream'});r.end(d);});}).listen(0);
const port = srv.address().port;
const b = await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:'new',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--enable-webgl','--disable-gpu-vsync','--disable-frame-rate-limit']});
const pg = await b.newPage(); await pg.setViewport({width:1080,height:1920,deviceScaleFactor:1});
pg.on('console',m=>console.log('[page]',m.text())); pg.on('pageerror',e=>console.log('[err]',e.message));
await pg.goto(`http://localhost:${port}/${process.env.SCENE||'scene.html'}?w=${wArg}&h=${hArg}`); await pg.waitForFunction('window.ready===true',{timeout:60000});
await pg.evaluate(p=>window.setup(p),P);
const N = Math.floor(P.dur*30); const from=+fromArg, to=(+toArg<0)?N:+toArg, step=+stepArg;
const t00=Date.now();
const LIST=process.env.FRAMES?process.env.FRAMES.split(",").map(Number):null;const ITER=LIST||Array.from({length:Math.max(0,Math.ceil((to-from)/step))},(_,k)=>from+k*step);
for(const i of ITER){ await pg.evaluate(async(i,fs)=>{await window.draw(i/30,fs,i);},i,P.frames?P.frames[i]:null);
  await pg.screenshot({path:path.join(outDir,`f${String(i).padStart(5,'0')}.jpg`),type:'jpeg',quality:93});
  if(i%30===0) console.log('frame',i,'/',N,((Date.now()-t00)/1000).toFixed(0)+'s'); }
await b.close(); srv.close(); console.log('ok');
