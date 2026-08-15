'use strict';
const BG_PARTS=['mobile/vb_00.txt','mobile/vb_01.txt','mobile/vb_02.txt','mobile/vb_03.txt','mobile/vb_04.txt','mobile/vb_05.txt','mobile/vb_06.txt'];
const NPCS=[
 {id:'maelith',name:'Maelíth',role:'Storyteller',x:577,y:1566,file:'assets/mobile/maelith.webp'},
 {id:'eira',name:'Eira',role:'Path Guide',x:895,y:1548,file:'assets/mobile/eira.webp'},
 {id:'brannoc',name:'Brannoc',role:'Town Warden',x:573,y:1758,file:'assets/mobile/brannoc.webp'},
 {id:'siofra',name:'Siofra',role:'Shrine Keeper',x:854,y:1856,file:'assets/mobile/siofra.webp'}
];
const COL='/////////////////////5///////wf//////wf//////wf+////DwD+////BwD+////B4D/////A8D/////A/D/////B/j//2PwAcD//wHgAQD+/wHgAAD+/wPgAAD+/wdg4A/+/x8g8P///38A8P////8OiP////8PBP////8PAv7///8PAP7///8HAP7///8DAP7///8DAP////8DiP////8D+P////8H+P////8H/P////8P/v////8P/v////8P/v////8f/P////8f/P////8P+P////8P8P////8P8P//AQAAAAD8AQAAAAD8AQAAAAD8AQDwHwD8AQDwHwD8AQDwHwD8wT/wHwD8wT8AAAD8wT8AAAD8wT8AAAD8AQAAwAP8AQAAwAP8AfwAwAP8AfwAAAD8AfwAgH/8AQAAgH/8eQAAgH/8eQAAgH/8eQAAAAD8AQAAAAD8AQAAAAD88QMAAAD88QMAAAD88QMAAAD8AfAP/gH8AfAP/gH8AfAP/gH8AfAP/gH8AQAA/gH8AQAAAOD/AQAAAOD/AQAAAOD/////////';
const WORLD={x:124,y:1400,w:1280,h:900};
const SPAWN={x:764,y:2058,f:'up'};
const ROW={down:0,left:1,right:2,up:3};
const $=id=>document.getElementById(id), canvas=$('g'),ctx=canvas.getContext('2d');
let vw=innerWidth,vh=innerHeight,dpr=1,running=false,last=0,walk=0,frame=0,held=new Set();
let p={...SPAWN},bg=null,playerImg=null,npcImgs={},ready=false;
const bits=Uint8Array.from(atob(COL),c=>c.charCodeAt(0));
function blocked(tx,ty){if(tx<0||ty<0||tx>=48||ty>=72)return true;const i=ty*48+tx;return !!(bits[i>>3]&(1<<(i&7)));}
function valid(x,y){if(x<WORLD.x+10||x>WORLD.x+WORLD.w-10||y<WORLD.y+10||y>WORLD.y+WORLD.h-6)return false;return [[x-8,y-3],[x+8,y-3],[x-8,y+4],[x+8,y+4]].every(([a,b])=>!blocked(a/32|0,b/32|0));}
function image(src){return new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=()=>reject(new Error('Could not load '+src));i.src=src;});}
async function chunkImage(parts){let s='';for(const f of parts){const r=await fetch(f,{cache:'force-cache'});if(!r.ok)throw new Error(f+' '+r.status);s+=(await r.text()).trim();}return image('data:image/webp;base64,'+s);}
async function load(){try{
 $('status').textContent='Loading Bré Thiar production art…';
 bg=await chunkImage(BG_PARTS);
 let n=0;for(const q of NPCS){npcImgs[q.id]=await image(q.file);$('status').textContent='Loading village entities… '+(++n)+'/'+NPCS.length;}
 try{playerImg=await image('assets/mobile/player.webp');}catch(_){playerImg=npcImgs.brannoc;}
 ready=true;$('status').textContent='Ready — tap Enter Bré Thiar';$('enter').disabled=false;
 }catch(e){$('status').textContent='Load failed: '+e.message;console.error(e);}}
function resize(){vw=innerWidth;vh=innerHeight;dpr=Math.min(3,devicePixelRatio||1);canvas.width=Math.round(vw*dpr);canvas.height=Math.round(vh*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);} addEventListener('resize',resize,{passive:true});resize();
function zoom(){return vh>vw?1.14:0.92;}
function camera(){const z=zoom(),ww=vw/z,wh=vh/z;return {z,x:Math.max(WORLD.x,Math.min(WORLD.x+WORLD.w-ww,p.x-ww/2)),y:Math.max(WORLD.y,Math.min(WORLD.y+WORLD.h-wh,p.y-wh/2)),ww,wh};}
function drawWorld(cam){const sx=(cam.x-WORLD.x)/WORLD.w*bg.width,sy=(cam.y-WORLD.y)/WORLD.h*bg.height,sw=cam.ww/WORLD.w*bg.width,sh=cam.wh/WORLD.h*bg.height;ctx.imageSmoothingEnabled=false;ctx.drawImage(bg,sx,sy,sw,sh,0,0,vw,vh);}
function screen(wx,wy,cam){return [(wx-cam.x)*cam.z,(wy-cam.y)*cam.z];}
function label(t,x,y,color='#f7e8b8'){ctx.save();ctx.textAlign='center';ctx.font='11px system-ui';ctx.lineWidth=3;ctx.strokeStyle='#000b';ctx.strokeText(t,x,y);ctx.fillStyle=color;ctx.fillText(t,x,y);ctx.restore();}
function drawNPC(q,cam){const im=npcImgs[q.id], [x,y]=screen(q.x,q.y,cam);if(!im)return;const s=cam.z*1.08,w=im.width*s,h=im.height*s;ctx.drawImage(im,x-w/2,y-h,w,h);label(q.name,x,y-h-5);}
function drawPlayer(cam){const [x,y]=screen(p.x,p.y,cam);if(!playerImg)return;let sw=playerImg.width,sh=playerImg.height,sx=0,sy=0;if(sw>=192&&sh>=224){sw=96;sh=112;sx=(frame%4)*96;sy=(ROW[p.f]||0)*112;}const w=58*cam.z,h=68*cam.z;ctx.drawImage(playerImg,sx,sy,sw,sh,x-w/2,y-h,w,h);label('Aedric',x,y-h-5,'#fff');}
// Repaint exact production pixels over entities where roofs/tree canopies should occlude them.
const OCC=[
 [170,1420,335,265],[500,1415,300,245],[890,1420,330,260],
 [160,1690,300,260],[930,1680,330,275],[250,2020,310,230],[980,2000,300,245],
 [120,1400,180,900],[1220,1400,184,900]
];
function repaintRect(r,cam){const [wx,wy,ww,wh]=r;const ix=Math.max(wx,cam.x),iy=Math.max(wy,cam.y),ax=Math.min(wx+ww,cam.x+cam.ww),ay=Math.min(wy+wh,cam.y+cam.wh);if(ax<=ix||ay<=iy)return;const sx=(ix-WORLD.x)/WORLD.w*bg.width,sy=(iy-WORLD.y)/WORLD.h*bg.height,sw=(ax-ix)/WORLD.w*bg.width,sh=(ay-iy)/WORLD.h*bg.height;const dx=(ix-cam.x)*cam.z,dy=(iy-cam.y)*cam.z,dw=(ax-ix)*cam.z,dh=(ay-iy)*cam.z;ctx.drawImage(bg,sx,sy,sw,sh,dx,dy,dw,dh);}
function nearestNPC(){let best=null,d=72;for(const q of NPCS){const n=Math.hypot(p.x-q.x,p.y-q.y);if(n<d){d=n;best=q;}}return best;}
function render(){if(!ready)return;const cam=camera();drawWorld(cam);const entities=[...NPCS.map(q=>({y:q.y,kind:'npc',q})),{y:p.y,kind:'player'}].sort((a,b)=>a.y-b.y);for(const e of entities)e.kind==='player'?drawPlayer(cam):drawNPC(e.q,cam);for(const r of OCC)repaintRect(r,cam);const n=nearestNPC();$('prompt').classList.toggle('hide',!n);if(n)$('prompt').textContent='Talk to '+n.name;$('zone').textContent='Bré Thiar';}
function step(dt){let d=null;for(const k of ['up','down','left','right'])if(held.has(k))d=k;if(!d){frame=0;return;}p.f=d;const s=86,dx=d==='left'?-s*dt:d==='right'?s*dt:0,dy=d==='up'?-s*dt:d==='down'?s*dt:0,nx=p.x+dx,ny=p.y+dy;if(valid(nx,ny)){p.x=nx;p.y=ny;walk+=Math.hypot(dx,dy);frame=(walk/8|0)%4;localStorage.setItem('breThiarMobileVillage',JSON.stringify(p));}}
function loop(t){if(!running)return;const dt=Math.min(.05,(t-last)/1000||0);last=t;step(dt);render();requestAnimationFrame(loop);}
document.querySelectorAll('[data-d]').forEach(b=>{const d=b.dataset.d;const on=e=>{e.preventDefault();held.add(d);p.f=d};const off=e=>{e&&e.preventDefault();held.delete(d)};b.addEventListener('pointerdown',on);b.addEventListener('pointerup',off);b.addEventListener('pointercancel',off);b.addEventListener('pointerleave',off);});
$('talk').onclick=()=>{const n=nearestNPC();if(!n){toast('No one close enough to talk to.');return;}const lines={maelith:'The old roads remember every traveler.',eira:'Every Path begins with a choice.',brannoc:'Keep your blade ready beyond the village fences.',siofra:'Listen to the stones before you speak.'};$('dn').textContent=n.name+' · '+n.role;$('dt').textContent=lines[n.id];$('dialog').classList.remove('hide');};
$('atk').onclick=()=>toast('Combat comes with Rowanwood in the next mobile slice.');
$('menu').onclick=()=>$('sheet').classList.remove('hide');$('close').onclick=()=>$('sheet').classList.add('hide');$('dc').onclick=()=>$('dialog').classList.add('hide');$('reset').onclick=()=>{p={...SPAWN};localStorage.removeItem('breThiarMobileVillage');$('sheet').classList.add('hide');toast('Position reset.');};
function toast(t){$('toast').textContent=t;$('toast').classList.remove('hide');clearTimeout(toast.t);toast.t=setTimeout(()=>$('toast').classList.add('hide'),1900);}
$('enter').onclick=()=>{if(!ready)return;try{const s=JSON.parse(localStorage.getItem('breThiarMobileVillage'));if(s&&valid(s.x,s.y))p={...p,...s};}catch(_){}$('splash').classList.add('hide');running=true;last=performance.now();requestAnimationFrame(loop);};
load();