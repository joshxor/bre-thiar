'use strict';
const HIST='https://raw.githubusercontent.com/joshxor/bre-thiar/bb602d354f9a7daa06774345d3a220c43847b325/';
const BG_PARTS=['mobile/vb_00.txt','mobile/vb_01.txt','mobile/vb_02.txt','mobile/vb_03.txt','mobile/vb_04.txt','mobile/vb_05.txt','mobile/vb_06.txt'].map(x=>HIST+x);
const NPCS=[
{id:'maelith',name:'Maelíth',role:'Storyteller',x:577,y:1566,file:'assets/mobile/maelith.webp'},
{id:'eira',name:'Eira',role:'Path Guide',x:895,y:1548,file:'assets/mobile/eira.webp'},
{id:'brannoc',name:'Brannoc',role:'Town Warden',x:573,y:1758,file:'assets/mobile/brannoc.webp'},
{id:'siofra',name:'Siofra',role:'Shrine Keeper',x:854,y:1856,file:'assets/mobile/siofra.webp'}];
const COL='/////////////////////5///////wf//////wf//////wf+////DwD+////BwD+////B4D/////A8D/////A/D/////B/j//2PwAcD//wHgAQD+/wHgAAD+/wPgAAD+/wdg4A/+/x8g8P///38A8P////8OiP////8PBP////8PAv7///8PAP7///8HAP7///8DAP7///8DAP////8DiP////8D+P////8H+P////8H/P////8P/v////8P/v////8P/v////8f/P////8f/P////8P+P////8P8P////8P8P//AQAAAAD8AQAAAAD8AQAAAAD8AQDwHwD8AQDwHwD8AQDwHwD8wT/wHwD8wT8AAAD8wT8AAAD8wT8AAAD8AQAAwAP8AQAAwAP8AfwAwAP8AfwAAAD8AfwAgH/8AQAAgH/8eQAAgH/8eQAAgH/8eQAAAAD8AQAAAAD8AQAAAAD88QMAAAD88QMAAAD88QMAAAD8AfAP/gH8AfAP/gH8AfAP/gH8AfAP/gH8AQAA/gH8AQAAAOD/AQAAAOD/AQAAAOD/////////';
const WORLD={x:124,y:1400,w:1280,h:900},SPAWN={x:764,y:2058,f:'up'},ROW={down:0,left:1,right:2,up:3};
const $=id=>document.getElementById(id),canvas=$('g'),ctx=canvas.getContext('2d');
let VW=innerWidth,VH=innerHeight,DPR=1,running=false,last=0,walk=0,frame=0,held=new Set(),p={...SPAWN},bg=null,playerImg=null,npcImgs={},ready=false;
const bits=Uint8Array.from(atob(COL),c=>c.charCodeAt(0));
function blocked(tx,ty){if(tx<0||ty<0||tx>=48||ty>=72)return true;const i=ty*48+tx;return !!(bits[i>>3]&(1<<(i&7)));}
function valid(x,y){if(x<WORLD.x+10||x>WORLD.x+WORLD.w-10||y<WORLD.y+10||y>WORLD.y+WORLD.h-6)return false;return [[x-8,y-3],[x+8,y-3],[x-8,y+4],[x+8,y+4]].every(([a,b])=>!blocked(a/32|0,b/32|0));}
function image(src){return new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=()=>rej(new Error('Could not load '+src));i.src=src;});}
async function chunkImage(parts){let s='';for(const f of parts){const r=await fetch(f,{cache:'force-cache'});if(!r.ok)throw new Error('Asset '+r.status);s+=(await r.text()).trim();}return image('data:image/webp;base64,'+s);}
async function load(){try{$('status').textContent='Loading Bré Thiar production art…';bg=await chunkImage(BG_PARTS);let i=0;for(const n of NPCS){npcImgs[n.id]=await image(n.file);$('status').textContent='Loading village entities… '+(++i)+'/4';}try{playerImg=await image('assets/mobile/player.webp');}catch(_){playerImg=npcImgs.brannoc;}$('status').textContent='Ready — tap Enter Bré Thiar';$('enter').disabled=false;ready=true;}catch(e){console.error(e);$('status').textContent='Load failed — '+e.message;}}
function resize(){VW=innerWidth;VH=innerHeight;DPR=Math.min(3,devicePixelRatio||1);canvas.width=Math.round(VW*DPR);canvas.height=Math.round(VH*DPR);ctx.setTransform(DPR,0,0,DPR,0,0);}resize();addEventListener('resize',resize,{passive:true});
function zoom(){return VH>VW?1.12:.92;}
function camera(){const z=zoom(),ww=VW/z,wh=VH/z;return{z,ww,wh,x:Math.max(WORLD.x,Math.min(WORLD.x+WORLD.w-ww,p.x-ww/2)),y:Math.max(WORLD.y,Math.min(WORLD.y+WORLD.h-wh,p.y-wh/2))};}
function sourceRect(cam){return[(cam.x-WORLD.x)/WORLD.w*bg.width,(cam.y-WORLD.y)/WORLD.h*bg.height,cam.ww/WORLD.w*bg.width,cam.wh/WORLD.h*bg.height];}
function drawWorld(cam){const s=sourceRect(cam);ctx.imageSmoothingEnabled=false;ctx.drawImage(bg,s[0],s[1],s[2],s[3],0,0,VW,VH);}
function screen(x,y,cam){return[(x-cam.x)*cam.z,(y-cam.y)*cam.z];}
function label(t,x,y,color='#f7e8b8'){ctx.save();ctx.textAlign='center';ctx.font='11px system-ui';ctx.lineWidth=3;ctx.strokeStyle='#000d';ctx.strokeText(t,x,y);ctx.fillStyle=color;ctx.fillText(t,x,y);ctx.restore();}
function drawNPC(n,cam){const im=npcImgs[n.id],[x,y]=screen(n.x,n.y,cam);if(!im)return;const s=cam.z*1.08,w=im.width*s,h=im.height*s;ctx.drawImage(im,x-w/2,y-h,w,h);label(n.name,x,y-h-5);}
function drawPlayer(cam){if(!playerImg)return;const[x,y]=screen(p.x,p.y,cam);let sx=0,sy=0,sw=playerImg.width,sh=playerImg.height;if(sw>=192&&sh>=224){sw=96;sh=112;sx=(frame%4)*96;sy=(ROW[p.f]||0)*112;}const w=58*cam.z,h=68*cam.z;ctx.drawImage(playerImg,sx,sy,sw,sh,x-w/2,y-h,w,h);label('Aedric',x,y-h-5,'#fff');}
// These are authored roof/tree masses. We repaint their exact production pixels after entities,
// preserving walk-behind occlusion without a second degraded mobile art layer.
const OCC=[[160,1400,345,275],[495,1400,330,250],[885,1400,350,275],[145,1670,325,285],[900,1660,355,295],[235,1990,335,270],[940,1970,350,285],[124,1400,120,900],[1280,1400,124,900]];
function repaint(r,cam){const ix=Math.max(r[0],cam.x),iy=Math.max(r[1],cam.y),ax=Math.min(r[0]+r[2],cam.x+cam.ww),ay=Math.min(r[1]+r[3],cam.y+cam.wh);if(ax<=ix||ay<=iy)return;const sx=(ix-WORLD.x)/WORLD.w*bg.width,sy=(iy-WORLD.y)/WORLD.h*bg.height,sw=(ax-ix)/WORLD.w*bg.width,sh=(ay-iy)/WORLD.h*bg.height;ctx.drawImage(bg,sx,sy,sw,sh,(ix-cam.x)*cam.z,(iy-cam.y)*cam.z,(ax-ix)*cam.z,(ay-iy)*cam.z);}
function nearest(){let b=null,d=78;for(const n of NPCS){const q=Math.hypot(p.x-n.x,p.y-n.y);if(q<d){b=n;d=q;}}return b;}
function render(){if(!ready)return;const cam=camera();drawWorld(cam);const ents=[...NPCS.map(n=>({y:n.y,n})),{y:p.y,p:true}].sort((a,b)=>a.y-b.y);for(const e of ents)e.p?drawPlayer(cam):drawNPC(e.n,cam);for(const r of OCC)repaint(r,cam);const n=nearest();$('prompt').classList.toggle('hide',!n);if(n)$('prompt').textContent='Talk to '+n.name;}
function step(dt){let d=null;for(const k of['up','down','left','right'])if(held.has(k))d=k;if(!d){frame=0;return;}p.f=d;const v=86,dx=d==='left'?-v*dt:d==='right'?v*dt:0,dy=d==='up'?-v*dt:d==='down'?v*dt:0,nx=p.x+dx,ny=p.y+dy;if(valid(nx,ny)){p.x=nx;p.y=ny;walk+=Math.hypot(dx,dy);frame=(walk/8|0)%4;localStorage.setItem('breThiarVillageQA',JSON.stringify(p));}}
function loop(t){if(!running)return;const dt=Math.min(.05,(t-last)/1000||0);last=t;step(dt);render();requestAnimationFrame(loop);}
document.querySelectorAll('[data-d]').forEach(b=>{const d=b.dataset.d,on=e=>{e.preventDefault();held.add(d);p.f=d},off=e=>{if(e)e.preventDefault();held.delete(d)};b.addEventListener('pointerdown',on);b.addEventListener('pointerup',off);b.addEventListener('pointercancel',off);b.addEventListener('pointerleave',off);});
function toast(t){$('toast').textContent=t;$('toast').classList.remove('hide');clearTimeout(toast.t);toast.t=setTimeout(()=>$('toast').classList.add('hide'),1900);}
$('talk').onclick=()=>{const n=nearest();if(!n)return toast('No one close enough to talk to.');const lines={maelith:'The old roads remember every traveler.',eira:'Every Path begins with a choice.',brannoc:'Keep your blade ready beyond the village fences.',siofra:'Listen to the stones before you speak.'};$('dn').textContent=n.name+' · '+n.role;$('dt').textContent=lines[n.id];$('dialog').classList.remove('hide');};
$('atk').onclick=()=>toast('Combat unlocks with the Rowanwood mobile slice.');$('menu').onclick=()=>$('sheet').classList.remove('hide');$('close').onclick=()=>$('sheet').classList.add('hide');$('dc').onclick=()=>$('dialog').classList.add('hide');$('reset').onclick=()=>{p={...SPAWN};localStorage.removeItem('breThiarVillageQA');$('sheet').classList.add('hide');toast('Position reset.');};
$('enter').onclick=()=>{if(!ready)return;try{const s=JSON.parse(localStorage.getItem('breThiarVillageQA'));if(s&&valid(s.x,s.y))p={...p,...s};}catch(_){}$('splash').classList.add('hide');running=true;last=performance.now();requestAnimationFrame(loop);};load();