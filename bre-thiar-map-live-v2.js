'use strict';
const BUILD='hypnobius-map-v2.1';
const $=id=>document.getElementById(id), canvas=$('g'), ctx=canvas.getContext('2d');
ctx.imageSmoothingEnabled=false;
let VW=innerWidth,VH=innerHeight,DPR=1,run=false,ready=false,last=0;
let map=null, manifest=null, worldAtlases={}, charImgs={};
let held=new Set(), toastTimer=0;
let player={x:690,y:540,f:'down',cls:'wayfarer',gender:'male',hp:100};
let collisions=[], triggers=[], worldObjects=[], party=[];
const classLabels={wayfarer:'Wayfarer',iron_warden:'Iron Warden',trail_ranger:'Trail Ranger',runekeeper:'Runekeeper'};

function asset(p){return p+'?v='+BUILD}
async function loadJSON(p){const r=await fetch(asset(p),{cache:'no-store'});if(!r.ok)throw new Error(p+' '+r.status);return r.json()}
function loadImage(p){return new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=()=>rej(new Error('Image decode failed: '+p));i.src=asset(p)})}
function resize(){VW=innerWidth;VH=innerHeight;DPR=Math.min(3,devicePixelRatio||1);canvas.width=Math.round(VW*DPR);canvas.height=Math.round(VH*DPR);ctx.setTransform(DPR,0,0,DPR,0,0);ctx.imageSmoothingEnabled=false}
addEventListener('resize',resize,{passive:true});resize();

async function load(){
 try{
  $('status').textContent='Loading Bré Thiar village map…';
  manifest=await loadJSON('bre-thiar-assets-v2.json');
  map=await loadJSON(manifest.map);
  for(const [name,a] of Object.entries(manifest.worldAtlases)) worldAtlases[name]=await loadImage(a.path);
  for(const [cls,meta] of Object.entries(manifest.characters)){
    charImgs[cls]={};
    charImgs[cls].male=await loadImage(meta.male);
    charImgs[cls].female=await loadImage(meta.female);
  }
  parseMap();restore();setupClassMenu();
  ready=true;$('enter').disabled=false;$('status').textContent='Ready — Bré Thiar village hub';
 }catch(e){console.error(e);$('status').textContent='Load failed — '+e.message}
}

function layer(name){return map.layers.find(l=>l.name===name)}
function parseMap(){
 const worldFirst=(map.tilesets.find(t=>String(t.source||'').includes('world_objects'))||{firstgid:6}).firstgid;
 worldObjects=(layer('World Objects')?.objects||[]).map(o=>({...o,localId:o.gid-worldFirst}));
 collisions=(layer('Collision')?.objects||[]).map(o=>({x:o.x,y:o.y,w:o.width,h:o.height,name:o.name}));
 triggers=(layer('Spawns & Triggers')?.objects||[]);
 const spawn=triggers.find(o=>o.name==='Player Spawn');if(spawn){player.x=spawn.x;player.y=spawn.y}
 party=[
  {name:'Brannoc',cls:'iron_warden',gender:'male',x:610,y:448,f:'down'},
  {name:'Eira',cls:'trail_ranger',gender:'female',x:835,y:445,f:'left'},
  {name:'Siofra',cls:'runekeeper',gender:'female',x:700,y:665,f:'up'},
  {name:'Maelíth',cls:'wayfarer',gender:'female',x:515,y:610,f:'right'}
 ];
}

function setupClassMenu(){
 const panel=document.querySelector('#sheet .panel');
 if(!panel||document.getElementById('appearance'))return;
 const box=document.createElement('div');box.id='appearance';box.innerHTML='<h3 style="color:#d7b85e;margin:14px 0 7px">Appearance QA</h3><div style="font:12px/1.4 system-ui;color:#cfc4a8;margin-bottom:6px">All eight current class/gender assets are live here. Movement uses the real four-direction static rows; walk/combat animation is not faked.</div>';
 for(const cls of Object.keys(classLabels)){
   const b=document.createElement('button');b.textContent=classLabels[cls];b.dataset.cls=cls;b.style.marginRight='6px';
   b.addEventListener('click',()=>{player.cls=cls;save();updateIdentity();toast(classLabels[cls]+' selected')});box.appendChild(b);
 }
 const gb=document.createElement('button');gb.textContent='Toggle Male / Female';gb.addEventListener('click',()=>{player.gender=player.gender==='male'?'female':'male';save();updateIdentity();toast(player.gender)});box.appendChild(gb);
 panel.insertBefore(box,$('reset'));updateIdentity();
}
function updateIdentity(){const pill=document.querySelector('.top .pill');if(pill)pill.textContent='Aedric · '+classLabels[player.cls]+' · '+player.gender}
function restore(){try{const q=JSON.parse(localStorage.getItem('bre-thiar-hypnobius-v2')||'null');if(q)player={...player,...q}}catch(_){}updateIdentity()}
function save(){localStorage.setItem('bre-thiar-hypnobius-v2',JSON.stringify({x:player.x,y:player.y,f:player.f,cls:player.cls,gender:player.gender,hp:player.hp}))}

function blocked(x,y){
 const hw=14, top=8, bot=5;
 if(x-hw<0||x+hw>map.width*map.tilewidth||y-top<0||y+bot>map.height*map.tileheight)return true;
 return collisions.some(r=>x+hw>r.x&&x-hw<r.x+r.w&&y+bot>r.y&&y-top<r.y+r.h);
}
function move(dt){
 let dx=0,dy=0;if(held.has('left'))dx--;if(held.has('right'))dx++;if(held.has('up'))dy--;if(held.has('down'))dy++;
 if(!dx&&!dy)return;if(dx&&dy){dx*=0.7071;dy*=0.7071}
 const sp=126*dt,nx=player.x+dx*sp,ny=player.y+dy*sp;
 if(Math.abs(dx)>Math.abs(dy))player.f=dx<0?'left':'right';else player.f=dy<0?'up':'down';
 if(!blocked(nx,player.y))player.x=nx;if(!blocked(player.x,ny))player.y=ny;save();checkTriggers();
}
function checkTriggers(){for(const t of triggers){if(t.type!=='exit')continue;if(Math.hypot(player.x-t.x,player.y-t.y)<45){toast(t.name.replace(' Exit','')+' road — zone connection retained for next map pass');break}}}

function zoom(){return VH>VW?1.22:Math.max(.92,Math.min(1.08,VH/720))}
function camera(){const z=zoom(),mw=map.width*map.tilewidth,mh=map.height*map.tileheight,w=VW/z,h=VH/z;return{z,w,h,x:Math.max(0,Math.min(mw-w,player.x-w/2)),y:Math.max(0,Math.min(mh-h,player.y-h/2))}}
function screen(x,y,c){return[(x-c.x)*c.z,(y-c.y)*c.z]}
function drawShadow(x,y,w,c,a=.24){const[sx,sy]=screen(x,y,c);ctx.save();ctx.fillStyle=`rgba(0,0,0,${a})`;ctx.beginPath();ctx.ellipse(sx,sy,Math.max(10,w*.19)*c.z,Math.max(4,w*.035)*c.z,0,0,Math.PI*2);ctx.fill();ctx.restore()}
function drawTerrain(c){
 const ts=map.tilewidth,fc=Math.max(0,Math.floor(c.x/ts)),lc=Math.min(map.width-1,Math.ceil((c.x+c.w)/ts)),fr=Math.max(0,Math.floor(c.y/ts)),lr=Math.min(map.height-1,Math.ceil((c.y+c.h)/ts));
 const im=worldAtlases.props,[ax,ay]=manifest.terrain.rect,sw=manifest.terrain.sourceTileWidth,sh=manifest.terrain.sourceTileHeight;
 for(const lname of ['Ground','Swamp','Roads']){const L=layer(lname);if(!L)continue;for(let ty=fr;ty<=lr;ty++)for(let tx=fc;tx<=lc;tx++){
  const gid=L.data[ty*map.width+tx];if(!gid)continue;const id=gid-1,sx=ax+(id%manifest.terrain.columns)*sw,sy=ay+Math.floor(id/manifest.terrain.columns)*sh;const[dx,dy]=screen(tx*ts,ty*ts,c);ctx.drawImage(im,sx,sy,sw,sh,Math.floor(dx),Math.floor(dy),Math.ceil(ts*c.z)+1,Math.ceil(ts*c.z)+1);
 }}
}
function drawWorldObject(o,c){const meta=manifest.worldTiles[String(o.localId)];if(!meta)return;const atlasMeta=manifest.worldAtlases[meta.atlas],im=worldAtlases[meta.atlas],r=atlasMeta.rects[meta.key];if(!im||!r)return;const w=o.width,h=o.height;const[x,y]=screen(o.x-w/2,o.y-h,c);drawShadow(o.x,o.y,w,c,.18);ctx.drawImage(im,r[0],r[1],r[2],r[3],Math.round(x),Math.round(y),Math.round(w*c.z),Math.round(h*c.z))}
function drawCharacter(ent,c,controlled=false){
 const im=charImgs[ent.cls]?.[ent.gender];if(!im)return;const row=manifest.directionRows[ent.f||'down'],cw=128,ch=160;const[x,y]=screen(ent.x-cw/2,ent.y-156,c);drawShadow(ent.x,ent.y,64,c,.32);ctx.drawImage(im,0,row*ch,cw,ch,Math.round(x),Math.round(y),Math.round(cw*c.z),Math.round(ch*c.z));
 if(!controlled){const[sx,sy]=screen(ent.x,ent.y-172,c);ctx.font=`${Math.max(10,12*c.z)}px Georgia`;ctx.textAlign='center';ctx.fillStyle='#f2e7c9';ctx.strokeStyle='#08100a';ctx.lineWidth=3;ctx.strokeText(ent.name,sx,sy);ctx.fillText(ent.name,sx,sy)}
}
function render(){if(!ready)return;const c=camera();ctx.setTransform(DPR,0,0,DPR,0,0);ctx.clearRect(0,0,VW,VH);ctx.fillStyle='#071009';ctx.fillRect(0,0,VW,VH);ctx.save();ctx.imageSmoothingEnabled=false;drawTerrain(c);const items=[];for(const o of worldObjects)items.push({y:o.y,k:'o',v:o});for(const p of party)items.push({y:p.y,k:'c',v:p});items.push({y:player.y,k:'p',v:player});items.sort((a,b)=>a.y-b.y);for(const it of items){if(it.k==='o')drawWorldObject(it.v,c);else drawCharacter(it.v,c,it.k==='p')}ctx.restore()}
function frame(t){if(!run)return;const dt=Math.min(.034,(t-last)/1000||0);last=t;move(dt);render();requestAnimationFrame(frame)}

function nearestTalkable(){const candidates=[...party.map(n=>({name:n.name,x:n.x,y:n.y,text:n.cls==='iron_warden'?'The east road has been quiet. Too quiet.':n.cls==='trail_ranger'?'The Rowanwood trail begins beyond the village roads.':n.cls==='runekeeper'?'The old altar in the swamp is awake again.':'Every road through Bré Thiar carries a story.'})),...triggers.filter(t=>t.type==='poi').map(t=>({name:t.name,x:t.x,y:t.y,text:t.name==='Swamp Shrine Trigger'?'The stones hum beneath the black water.':'Bré Thiar gathers around these crossroads.'}))];let best=null,bd=1e9;for(const n of candidates){const d=Math.hypot(player.x-n.x,player.y-n.y);if(d<bd){bd=d;best=n}}return bd<165?best:null}
function talk(){const n=nearestTalkable();if(!n){toast('No one close enough to talk to.');return}$('dn').textContent=n.name;$('dt').textContent=n.text;$('dialog').classList.remove('hide')}
function attack(){toast(classLabels[player.cls]+' combat animation set is not authored yet.')}
function toast(s){const el=$('toast');el.textContent=s;el.classList.remove('hide');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.add('hide'),1500)}
function bindDir(el){const d=el.dataset.d,on=e=>{e.preventDefault();held.add(d)},off=e=>{e.preventDefault();held.delete(d)};el.addEventListener('pointerdown',on);el.addEventListener('pointerup',off);el.addEventListener('pointercancel',off);el.addEventListener('pointerleave',off)}
document.querySelectorAll('[data-d]').forEach(bindDir);
addEventListener('keydown',e=>{const k={ArrowUp:'up',KeyW:'up',ArrowDown:'down',KeyS:'down',ArrowLeft:'left',KeyA:'left',ArrowRight:'right',KeyD:'right'}[e.code];if(k){e.preventDefault();held.add(k)}});
addEventListener('keyup',e=>{const k={ArrowUp:'up',KeyW:'up',ArrowDown:'down',KeyS:'down',ArrowLeft:'left',KeyA:'left',ArrowRight:'right',KeyD:'right'}[e.code];if(k)held.delete(k)});
$('talk').addEventListener('click',talk);$('atk').addEventListener('click',attack);$('menu').addEventListener('click',()=>$('sheet').classList.remove('hide'));$('close').addEventListener('click',()=>$('sheet').classList.add('hide'));$('dc').addEventListener('click',()=>$('dialog').classList.add('hide'));
$('oldworld')?.addEventListener('click',()=>location.href='legacy-world.html');
$('reset').addEventListener('click',()=>{const s=triggers.find(o=>o.name==='Player Spawn');player.x=s?.x||690;player.y=s?.y||540;player.f='down';save();$('sheet').classList.add('hide');toast('Position reset')});
$('enter').addEventListener('click',()=>{if(!ready)return;$('splash').classList.add('hide');run=true;last=performance.now();requestAnimationFrame(frame)});
load();
