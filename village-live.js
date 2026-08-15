'use strict';
const VER='native-migration-hotfix-1';
const BG_PARTS=['mobile/vb_00.txt','mobile/vb_01.txt','mobile/vb_02.txt','mobile/vb_03.txt','mobile/vb_04.txt','mobile/vb_05.txt','mobile/vb_06.txt'];
const NPCS=[
{id:'maelith',name:'Maelíth',role:'Storyteller',x:577,y:1566,file:'assets/mobile/maelith.webp'},
{id:'eira',name:'Eira',role:'Path Guide',x:895,y:1548,file:'assets/mobile/eira.webp'},
{id:'brannoc',name:'Brannoc',role:'Town Warden',x:573,y:1758,file:'assets/mobile/brannoc.webp'},
{id:'siofra',name:'Siofra',role:'Shrine Keeper',x:854,y:1856,file:'assets/mobile/siofra.webp'}];
// Exact 48x72 canonical collision bitset (432 bytes). Visual occlusion is NOT inferred from collision.
const COL='/////////////////////5///////wf//////wf//////wf+////DwD+////BwD+////B4D/////A8D/////A/D/////B/j//2PwAcD//wHgAQD+/wHgAAD+/wPgAAD+/wdg4A/+/x8g8P///38A8P////8OiP////8PBP////8PAv7///8PAP7///8HAP7///8DAP7///8DAP////8DiP////8D+P////8H+P////8H/P////8P/v////8P/v////8P/v////8f/P////8f/P////8P+P////8P8P////8P8P//AQAAAAD8AQAAAAD8AQAAAAD8AQAAAAD8AQDwHwD8AQDwHwD8AQDwHwD8wT/wHwD8wT8AAAD8wT8AAAD8wT8AAAD8AQAAwAP8AQAAwAP8AfwAwAP8AfwAAAD8AfwAgH/8AQAAgH/8eQAAgH/8eQAAgH/8eQAAAAD8AQAAAAD8AQAAAAD88QMAAAD88QMAAAD88QMAAAD8AfAP/gH8AfAP/gH8AfAP/gH8AfAP/gH8AQAA/gH8AQAAAOD/AQAAAOD/AQAAAOD/////////';
const WORLD={x:124,y:1400,w:1280,h:900},SPAWN={x:764,y:2058,f:'up'},ROW={down:0,left:1,right:2,up:3};
const $=id=>document.getElementById(id),canvas=$('g'),ctx=canvas.getContext('2d');
const bits=Uint8Array.from(atob(COL),c=>c.charCodeAt(0));
let VW=innerWidth,VH=innerHeight,DPR=1,running=false,last=0,walk=0,frame=0,held=new Set(),p={...SPAWN},bg=null,playerImg=null,npcImgs={},ready=false;
function asset(path){return path+'?v='+encodeURIComponent(VER)}
function status(t){const e=$('status');if(e)e.textContent=t}
function blocked(tx,ty){if(tx<0||ty<0||tx>=48||ty>=72)return true;const i=ty*48+tx;return !!(bits[i>>3]&(1<<(i&7)))}
function valid(x,y){if(x<WORLD.x+10||x>WORLD.x+WORLD.w-10||y<WORLD.y+10||y>WORLD.y+WORLD.h-6)return false;return [[x-8,y-3],[x+8,y-3],[x-8,y+4],[x+8,y+4]].every(([a,b])=>!blocked(a/32|0,b/32|0))}
function image(src){return new Promise((res,rej)=>{const im=new Image();im.onload=()=>res(im);im.onerror=()=>rej(new Error('Could not decode image asset'));im.src=src})}
function blobUrl(text){const bin=atob(text.replace(/\s+/g,'')),bytes=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);return URL.createObjectURL(new Blob([bytes],{type:'image/webp'}))}
async function fetchText(path){const r=await fetch(asset(path),{cache:'no-store'});if(!r.ok)throw new Error('Asset '+r.status+' '+path);return(await r.text()).trim()}
async function chunkImage(parts){let s='';for(let i=0;i<parts.length;i++){status('Loading temporary village cache… '+(i+1)+'/'+parts.length);s+=await fetchText(parts[i])}const u=blobUrl(s);try{return await image(u)}finally{setTimeout(()=>URL.revokeObjectURL(u),1000)}}
async function textImage(path){const u=blobUrl(await fetchText(path));try{return await image(u)}finally{setTimeout(()=>URL.revokeObjectURL(u),1000)}}
async function load(){try{bg=await chunkImage(BG_PARTS);for(const n of NPCS)npcImgs[n.id]=await image(asset(n.file));try{playerImg=await textImage('mobile/player_q85.b64')}catch{playerImg=npcImgs.brannoc}ready=true;status('Ready — temporary cache, native map renderer is being promoted');$('enter').disabled=false}catch(e){console.error(e);status('Load failed — '+(e.message||e))}}
function resize(){VW=innerWidth;VH=innerHeight;DPR=Math.min(3,devicePixelRatio||1);canvas.width=Math.max(1,Math.round(VW*DPR));canvas.height=Math.max(1,Math.round(VH*DPR));ctx.setTransform(DPR,0,0,DPR,0,0)}
resize();addEventListener('resize',resize,{passive:true});
function zoom(){return VH>VW?1.12:.92}
function camera(){const z=zoom(),ww=VW/z,wh=VH/z;return{z,ww,wh,x:Math.max(WORLD.x,Math.min(WORLD.x+WORLD.w-ww,p.x-ww/2)),y:Math.max(WORLD.y,Math.min(WORLD.y+WORLD.h-wh,p.y-wh/2))}}
function drawWorld(cam){const sx=(cam.x-WORLD.x)/WORLD.w*bg.width,sy=(cam.y-WORLD.y)/WORLD.h*bg.height,sw=cam.ww/WORLD.w*bg.width,sh=cam.wh/WORLD.h*bg.height;ctx.imageSmoothingEnabled=false;ctx.drawImage(bg,sx,sy,sw,sh,0,0,VW,VH)}
function screen(x,y,c){return[(x-c.x)*c.z,(y-c.y)*c.z]}
function label(t,x,y,color='#f7e8b8'){ctx.save();ctx.textAlign='center';ctx.font='11px system-ui';ctx.lineWidth=3;ctx.strokeStyle='#000d';ctx.strokeText(t,x,y);ctx.fillStyle=color;ctx.fillText(t,x,y);ctx.restore()}
function drawNPC(n,c){const im=npcImgs[n.id];if(!im)return;const[x,y]=screen(n.x,n.y,c),s=c.z*1.08,w=im.width*s,h=im.height*s;ctx.drawImage(im,x-w/2,y-h,w,h);label(n.name,x,y-h-5)}
function cell(im){if(im.width>=384&&im.height>=448)return[96,112];if(im.width>=192&&im.height>=224)return[48,56];return[im.width,im.height]}
function drawPlayer(c){if(!playerImg)return;const[x,y]=screen(p.x,p.y,c),[sw,sh]=cell(playerImg),sx=sw<playerImg.width?(frame%4)*sw:0,sy=sh<playerImg.height?(ROW[p.f]||0)*sh:0,w=58*c.z,h=68*c.z;ctx.drawImage(playerImg,sx,sy,sw,sh,x-w/2,y-h,w,h);label('Aedric',x,y-h-5,'#fff')}
function nearest(){let best=null,d=78;for(const n of NPCS){const q=Math.hypot(p.x-n.x,p.y-n.y);if(q<d){best=n;d=q}}return best}
function render(){if(!ready)return;const c=camera();drawWorld(c);const es=[...NPCS.map(n=>({y:n.y,n})),{y:p.y,p:true}].sort((a,b)=>a.y-b.y);for(const e of es)e.p?drawPlayer(c):drawNPC(e.n,c);/* No fake rectangle occlusion. Real roof/canopy foreground comes with native renderer. */const n=nearest();$('prompt').classList.toggle('hide',!n);if(n)$('prompt').textContent='Talk to '+n.name}
function dir(){for(const k of['up','down','left','right'])if(held.has(k))return k;return null}
function step(dt){const d=dir();if(!d){frame=0;return}p.f=d;const v=86,dx=d==='left'?-v*dt:d==='right'?v*dt:0,dy=d==='up'?-v*dt:d==='down'?v*dt:0,nx=p.x+dx,ny=p.y+dy;if(valid(nx,ny)){p.x=nx;p.y=ny;walk+=Math.hypot(dx,dy);frame=(walk/8|0)%4;localStorage.setItem('breThiarVillageQA',JSON.stringify(p))}}
function loop(t){if(!running)return;const dt=Math.min(.05,(t-last)/1000||0);last=t;step(dt);render();requestAnimationFrame(loop)}
document.querySelectorAll('[data-d]').forEach(b=>{const d=b.dataset.d,on=e=>{e.preventDefault();held.add(d);p.f=d},off=e=>{if(e)e.preventDefault();held.delete(d)};b.addEventListener('pointerdown',on);for(const ev of['pointerup','pointercancel','pointerleave'])b.addEventListener(ev,off)});
const KEY={ArrowUp:'up',w:'up',W:'up',ArrowDown:'down',s:'down',S:'down',ArrowLeft:'left',a:'left',A:'left',ArrowRight:'right',d:'right',D:'right'};
addEventListener('keydown',e=>{const d=KEY[e.key];if(d){e.preventDefault();held.add(d);p.f=d}if(e.key===' '){e.preventDefault();$('talk').click()}});addEventListener('keyup',e=>{const d=KEY[e.key];if(d)held.delete(d)});addEventListener('blur',()=>held.clear());
function toast(t){$('toast').textContent=t;$('toast').classList.remove('hide');clearTimeout(toast.t);toast.t=setTimeout(()=>$('toast').classList.add('hide'),1900)}
$('talk').onclick=()=>{const n=nearest();if(!n)return toast('No one close enough to talk to.');const lines={maelith:'The old roads remember every traveler.',eira:'Every Path begins with a choice.',brannoc:'Keep your blade ready beyond the village fences.',siofra:'Listen to the stones before you speak.'};$('dn').textContent=n.name+' · '+n.role;$('dt').textContent=lines[n.id];$('dialog').classList.remove('hide')};$('atk').onclick=()=>toast('Combat arrives with the Rowanwood map renderer.');$('menu').onclick=()=>$('sheet').classList.remove('hide');$('close').onclick=()=>$('sheet').classList.add('hide');$('dc').onclick=()=>$('dialog').classList.add('hide');$('reset').onclick=()=>{p={...SPAWN};walk=frame=0;localStorage.removeItem('breThiarVillageQA');$('sheet').classList.add('hide');toast('Position reset.')};$('enter').onclick=()=>{if(!ready)return;try{const s=JSON.parse(localStorage.getItem('breThiarVillageQA'));if(s&&valid(s.x,s.y))p={...p,...s}}catch{}$('splash').classList.add('hide');running=true;last=performance.now();requestAnimationFrame(loop)};
load();
