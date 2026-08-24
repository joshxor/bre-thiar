'use strict';
const BUILD='hypnobius-world-v3.0';
const $=id=>document.getElementById(id),canvas=$('g'),ctx=canvas.getContext('2d');
ctx.imageSmoothingEnabled=false;
let VW=innerWidth,VH=innerHeight,DPR=1,run=false,ready=false,last=0,map=null,manifest=null,zoneId='bre_thiar';
let worldAtlases={},characterAtlases={},held=new Set(),toastTimer=0,transitioning=false,entryLock=0;
let player={x:690,y:540,f:'down',cls:'wayfarer',gender:'male',hp:100,zone:'bre_thiar'};
let collisions=[],triggers=[],worldObjects=[];
const classLabels={wayfarer:'Wayfarer',iron_warden:'Iron Warden',trail_ranger:'Trail Ranger',runekeeper:'Runekeeper'};
const zoneNPCDefinitions={
  bre_thiar:[
    {name:'Brannoc',cls:'iron_warden',gender:'male',x:610,y:448,f:'down',text:'The north road climbs into Rowanwood. Keep your blade close after dusk.'},
    {name:'Eira',cls:'trail_ranger',gender:'female',x:835,y:445,f:'left',text:'Follow the old stone road north and you will reach Rowanwood Verge.'},
    {name:'Siofra',cls:'runekeeper',gender:'female',x:700,y:665,f:'up',text:'The old altar in the swamp answers the stones beyond Rowanwood.'},
    {name:'Maelíth',cls:'wayfarer',gender:'female',x:515,y:610,f:'right',text:'Bré Thiar has always been a crossroads. Now the northern road is open again.'}
  ],
  rowanwood:[
    {name:'Eira',cls:'trail_ranger',gender:'female',x:520,y:1030,f:'right',text:'This is Rowanwood Verge. The old road crosses Blackwater and climbs toward the barrow.'},
    {name:'Cael',cls:'wayfarer',gender:'male',x:1170,y:1010,f:'left',text:'The trees thin near the northern rise. Nothing good waits beyond those drowned stones.'}
  ],
  old_barrow_approach:[
    {name:'Siofra',cls:'runekeeper',gender:'female',x:768,y:910,f:'up',text:'The seal is awake. The barrow interior still needs to be reclaimed before we cross this threshold.'}
  ]
};
function asset(p){return p+'?v='+BUILD}
async function text(p){const r=await fetch(asset(p),{cache:'no-store'});if(!r.ok)throw new Error(p+' '+r.status);return r.text()}
async function json(p){return JSON.parse(await text(p))}
function imgURL(url){return new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=()=>rej(new Error('Image decode failed'));i.src=url})}
async function cachedImage(spec){
  const paths=spec.parts||[spec.cache];let b64='';
  for(const p of paths)b64+=(await text(p)).replace(/\s/g,'');
  const bin=atob(b64),u=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);
  const url=URL.createObjectURL(new Blob([u],{type:spec.mime||'image/png'}));
  try{return await imgURL(url)}finally{setTimeout(()=>URL.revokeObjectURL(url),5000)}
}
function resize(){
  VW=innerWidth;VH=innerHeight;DPR=Math.min(3,devicePixelRatio||1);
  canvas.width=Math.round(VW*DPR);canvas.height=Math.round(VH*DPR);
  ctx.setTransform(DPR,0,0,DPR,0,0);ctx.imageSmoothingEnabled=false
}
addEventListener('resize',resize,{passive:true});resize();
function prop(o,k){const p=o.properties?.find(x=>x.name===k);return p?.value}
function layer(n){return map?.layers?.find(l=>l.name===n)}
function zoneInfo(){return manifest.zones[zoneId]}
function zoneNPCs(){return zoneNPCDefinitions[zoneId]||[]}
function facingFromSpawn(s){return prop(s,'facing')||'down'}
function spawnByName(name){return (layer('Spawns & Triggers')?.objects||[]).find(o=>o.type==='spawn'&&o.name===name)}
function parseMap(){
  const wf=(map.tilesets.find(t=>String(t.source||'').includes('world_objects'))||{firstgid:6}).firstgid;
  worldObjects=(layer('World Objects')?.objects||[]).map(o=>({...o,localId:o.gid-wf}));
  collisions=(layer('Collision')?.objects||[]).map(o=>({x:o.x,y:o.y,w:o.width,h:o.height,name:o.name,type:o.type}));
  triggers=layer('Spawns & Triggers')?.objects||[];
}
async function loadZone(id,spawnName=null,opts={}){
  if(!manifest.zones[id])throw new Error('Unknown zone '+id);
  transitioning=true;
  const spec=manifest.zones[id];
  map=await json(spec.map);zoneId=id;player.zone=id;parseMap();
  if(opts.position){
    player.x=opts.position.x;player.y=opts.position.y;player.f=opts.position.f||player.f;
  }else{
    const s=spawnByName(spawnName||spec.defaultSpawn);
    if(!s)throw new Error('Missing spawn '+(spawnName||spec.defaultSpawn)+' in '+id);
    player.x=s.x;player.y=s.y;player.f=facingFromSpawn(s);
  }
  entryLock=performance.now()+900;transitioning=false;save();updateIdentity();updateZoneLabel();
  if(!opts.silent)toast(spec.name)
}
function restoreState(){
  try{
    const q=JSON.parse(localStorage.getItem('bre-thiar-hypnobius-v3')||'null');
    if(q&&manifest.zones[q.zone])return q
  }catch(_){}
  return null
}
async function load(){
  try{
    $('status').textContent='Loading connected Bré Thiar world…';
    manifest=await json('bre-thiar-assets-v2.json');
    for(const[name,s]of Object.entries(manifest.worldAtlases))worldAtlases[name]=await cachedImage(s);
    for(const[name,s]of Object.entries(manifest.characterAtlases))characterAtlases[name]=await cachedImage(s);
    const saved=restoreState();
    if(saved){
      player={...player,...saved};
      await loadZone(saved.zone,null,{position:saved,silent:true});
      if(blocked(player.x,player.y)){
        await loadZone(saved.zone,manifest.zones[saved.zone].defaultSpawn,{silent:true});
      }
    }else{
      await loadZone(manifest.startZone||'bre_thiar',null,{silent:true});
    }
    setupClassMenu();setupWorldMenu();ready=true;$('enter').disabled=false;
    $('status').textContent='Ready — Bré Thiar → Rowanwood Verge → Old Barrow Approach'
  }catch(e){console.error(e);$('status').textContent='Load failed — '+e.message}
}
function setupClassMenu(){
  const panel=document.querySelector('#sheet .panel');
  if(!panel||document.getElementById('appearance'))return;
  const box=document.createElement('div');box.id='appearance';
  box.innerHTML='<h3 style="color:#d7b85e;margin:14px 0 7px">Appearance QA</h3><div style="font:12px/1.4 system-ui;color:#cfc4a8;margin-bottom:6px">All eight current class/gender assets are live. Movement uses their real four directions; walk/combat cycles are not faked.</div>';
  for(const cls of Object.keys(classLabels)){
    const b=document.createElement('button');b.textContent=classLabels[cls];
    b.addEventListener('click',()=>{player.cls=cls;save();updateIdentity();toast(classLabels[cls]+' selected')});box.appendChild(b)
  }
  const gb=document.createElement('button');gb.textContent='Toggle Male / Female';
  gb.addEventListener('click',()=>{player.gender=player.gender==='male'?'female':'male';save();updateIdentity();toast(player.gender)});box.appendChild(gb);
  panel.insertBefore(box,$('reset'));updateIdentity()
}
function setupWorldMenu(){
  const panel=document.querySelector('#sheet .panel');
  if(!panel||document.getElementById('worldjumps'))return;
  const box=document.createElement('div');box.id='worldjumps';
  box.innerHTML='<h3 style="color:#d7b85e;margin:14px 0 7px">World QA</h3>';
  for(const[id,s]of Object.entries(manifest.zones)){
    const b=document.createElement('button');b.textContent='Go to '+s.name;
    b.addEventListener('click',async()=>{held.clear();$('sheet').classList.add('hide');await loadZone(id,s.defaultSpawn)});box.appendChild(b)
  }
  panel.insertBefore(box,$('reset'))
}
function updateIdentity(){
  const p=document.querySelector('.top .pill');if(p)p.textContent='Aedric · '+classLabels[player.cls]+' · '+player.gender
}
function updateZoneLabel(){if($('zone'))$('zone').textContent=zoneInfo()?.name||zoneId}
function save(){
  localStorage.setItem('bre-thiar-hypnobius-v3',JSON.stringify({x:player.x,y:player.y,f:player.f,cls:player.cls,gender:player.gender,hp:player.hp,zone:zoneId}))
}
function blocked(x,y){
  const hw=14,top=8,bot=5,mw=map.width*map.tilewidth,mh=map.height*map.tileheight;
  if(x-hw<0||x+hw>mw||y-top<0||y+bot>mh)return true;
  return collisions.some(r=>x+hw>r.x&&x-hw<r.x+r.w&&y+bot>r.y&&y-top<r.y+r.h)
}
function nearestTrigger(type){
  let b=null,d=1e9;
  for(const t of triggers){
    if(type&&t.type!==type)continue;
    const q=Math.hypot(player.x-t.x,player.y-t.y);
    if(q<d){d=q;b=t}
  }
  return [b,d]
}
async function checkTriggers(){
  if(transitioning||performance.now()<entryLock)return;
  const [t,d]=nearestTrigger('exit');
  if(!t||d>=45)return;
  const dz=prop(t,'destination_zone'),ds=prop(t,'destination_spawn');
  if(dz&&manifest.zones[dz]){
    entryLock=performance.now()+1200;
    await loadZone(dz,ds||manifest.zones[dz].defaultSpawn);
  }else{
    entryLock=performance.now()+1200;
    toast((prop(t,'destination')||t.name)+' — future world connection')
  }
}
function move(dt){
  if(transitioning)return;
  let dx=0,dy=0;if(held.has('left'))dx--;if(held.has('right'))dx++;if(held.has('up'))dy--;if(held.has('down'))dy++;
  if(!dx&&!dy)return;if(dx&&dy){dx*=.7071;dy*=.7071}
  const sp=126*dt,nx=player.x+dx*sp,ny=player.y+dy*sp;
  if(Math.abs(dx)>Math.abs(dy))player.f=dx<0?'left':'right';else player.f=dy<0?'up':'down';
  if(!blocked(nx,player.y))player.x=nx;if(!blocked(player.x,ny))player.y=ny;save();checkTriggers()
}
function zoom(){return VH>VW?1.22:Math.max(.82,Math.min(1.08,VH/720))}
function camera(){
  const z=zoom(),mw=map.width*map.tilewidth,mh=map.height*map.tileheight,w=VW/z,h=VH/z;
  return{z,w,h,x:Math.max(0,Math.min(Math.max(0,mw-w),player.x-w/2)),y:Math.max(0,Math.min(Math.max(0,mh-h),player.y-h/2))}
}
function screen(x,y,c){return[(x-c.x)*c.z,(y-c.y)*c.z]}
function shadow(x,y,w,c,a=.24){
  const[sx,sy]=screen(x,y,c);ctx.save();ctx.fillStyle=`rgba(0,0,0,${a})`;ctx.beginPath();
  ctx.ellipse(sx,sy,Math.max(10,w*.19)*c.z,Math.max(4,w*.035)*c.z,0,0,Math.PI*2);ctx.fill();ctx.restore()
}
function drawTerrain(c){
  const ts=map.tilewidth,fc=Math.max(0,Math.floor(c.x/ts)),lc=Math.min(map.width-1,Math.ceil((c.x+c.w)/ts)),
    fr=Math.max(0,Math.floor(c.y/ts)),lr=Math.min(map.height-1,Math.ceil((c.y+c.h)/ts));
  const im=worldAtlases[manifest.terrain.atlas],[ax,ay]=manifest.terrain.rect,sw=manifest.terrain.sourceTileWidth,sh=manifest.terrain.sourceTileHeight;
  for(const lname of ['Ground','Swamp','Roads']){
    const L=layer(lname);if(!L)continue;
    for(let ty=fr;ty<=lr;ty++)for(let tx=fc;tx<=lc;tx++){
      const gid=L.data[ty*map.width+tx];if(!gid)continue;
      const id=gid-1,sx=ax+(id%manifest.terrain.columns)*sw,sy=ay+Math.floor(id/manifest.terrain.columns)*sh,[dx,dy]=screen(tx*ts,ty*ts,c);
      ctx.drawImage(im,sx,sy,sw,sh,Math.floor(dx),Math.floor(dy),Math.ceil(ts*c.z)+1,Math.ceil(ts*c.z)+1)
    }
  }
}
function drawWorld(o,c){
  const m=manifest.worldTiles[String(o.localId)];if(!m)return;
  const a=manifest.worldAtlases[m.atlas],im=worldAtlases[m.atlas],r=a.rects[m.key],w=o.width,h=o.height,[x,y]=screen(o.x-w/2,o.y-h,c);
  shadow(o.x,o.y,w,c,.18);ctx.drawImage(im,r[0],r[1],r[2],r[3],Math.round(x),Math.round(y),Math.round(w*c.z),Math.round(h*c.z))
}
function drawCharacter(e,c,controlled=false){
  const s=manifest.characters[e.cls]?.[e.gender];if(!s)return;
  const im=characterAtlases[s.atlas],r=s.rect,row=manifest.directionRows[e.f||'down'],cw=128,ch=160,[x,y]=screen(e.x-cw/2,e.y-156,c);
  shadow(e.x,e.y,64,c,.32);ctx.drawImage(im,r[0],r[1]+row*ch,cw,ch,Math.round(x),Math.round(y),Math.round(cw*c.z),Math.round(ch*c.z));
  if(!controlled){
    const[sx,sy]=screen(e.x,e.y-172,c);ctx.font=`${Math.max(10,12*c.z)}px Georgia`;ctx.textAlign='center';ctx.fillStyle='#f2e7c9';
    ctx.strokeStyle='#08100a';ctx.lineWidth=3;ctx.strokeText(e.name,sx,sy);ctx.fillText(e.name,sx,sy)
  }
}
function render(){
  if(!ready||!map)return;
  const c=camera();ctx.setTransform(DPR,0,0,DPR,0,0);ctx.clearRect(0,0,VW,VH);ctx.fillStyle='#071009';ctx.fillRect(0,0,VW,VH);ctx.imageSmoothingEnabled=false;
  drawTerrain(c);const items=[];
  for(const o of worldObjects)items.push({y:o.y,k:'o',v:o});
  for(const p of zoneNPCs())items.push({y:p.y,k:'c',v:p});
  items.push({y:player.y,k:'p',v:player});items.sort((a,b)=>a.y-b.y);
  for(const it of items)it.k==='o'?drawWorld(it.v,c):drawCharacter(it.v,c,it.k==='p')
}
function frame(t){if(!run)return;const dt=Math.min(.034,(t-last)/1000||0);last=t;move(dt);render();requestAnimationFrame(frame)}
function poiText(name){
  const d={
    'Village Center':'Bré Thiar gathers around these crossroads.',
    'Swamp Shrine Trigger':'The old stones hum beneath the black water.',
    'Ranger Lodge':'A weathered lodge watches the road into Rowanwood.',
    'Blackwater Crossing':'Cold black water moves beneath the old timber bridge.',
    'Old Rowan':'This rowan is older than the road. Red cords and small charms hang beneath its leaves.',
    'Barrow Threshold':'The seal answers with a low pulse. The Old Barrow interior is the next environment conversion target.',
    'Drowned Stones':'Dark stones vanish beneath the still water. Something has scratched marks into their upper faces.'
  };return d[name]||'The place feels older than the road around it.'
}
function nearestTalkable(){
  const c=[
    ...zoneNPCs().map(n=>({...n})),
    ...triggers.filter(t=>t.type==='poi').map(t=>({name:t.name,x:t.x,y:t.y,text:poiText(t.name)}))
  ];
  let b=null,d=1e9;for(const n of c){const q=Math.hypot(player.x-n.x,player.y-n.y);if(q<d){d=q;b=n}}return d<165?b:null
}
function talk(){
  const n=nearestTalkable();if(!n)return toast('Nothing close enough to inspect or talk to.');
  $('dn').textContent=n.name;$('dt').textContent=n.text;$('dialog').classList.remove('hide')
}
function attack(){toast(classLabels[player.cls]+' combat animation set is not authored yet.')}
function toast(s){const e=$('toast');e.textContent=s;e.classList.remove('hide');clearTimeout(toastTimer);toastTimer=setTimeout(()=>e.classList.add('hide'),1700)}
function bindDir(e){
  const d=e.dataset.d,on=x=>{x.preventDefault();held.add(d)},off=x=>{x.preventDefault();held.delete(d)};
  e.addEventListener('pointerdown',on);e.addEventListener('pointerup',off);e.addEventListener('pointercancel',off);e.addEventListener('pointerleave',off)
}
document.querySelectorAll('[data-d]').forEach(bindDir);
addEventListener('keydown',e=>{const k={ArrowUp:'up',KeyW:'up',ArrowDown:'down',KeyS:'down',ArrowLeft:'left',KeyA:'left',ArrowRight:'right',KeyD:'right'}[e.code];if(k){e.preventDefault();held.add(k)}});
addEventListener('keyup',e=>{const k={ArrowUp:'up',KeyW:'up',ArrowDown:'down',KeyS:'down',ArrowLeft:'left',KeyA:'left',ArrowRight:'right',KeyD:'right'}[e.code];if(k)held.delete(k)});
addEventListener('blur',()=>held.clear());
$('talk').addEventListener('click',talk);$('atk').addEventListener('click',attack);
$('menu').addEventListener('click',()=>$('sheet').classList.remove('hide'));
$('close').addEventListener('click',()=>$('sheet').classList.add('hide'));
$('dc').addEventListener('click',()=>$('dialog').classList.add('hide'));
$('oldworld')?.addEventListener('click',()=>location.href='legacy-world.html');
$('reset').addEventListener('click',async()=>{
  held.clear();localStorage.removeItem('bre-thiar-hypnobius-v3');$('sheet').classList.add('hide');
  await loadZone(manifest.startZone||'bre_thiar',manifest.zones[manifest.startZone||'bre_thiar'].defaultSpawn);toast('World position reset')
});
$('enter').addEventListener('click',()=>{if(!ready)return;$('splash').classList.add('hide');run=true;last=performance.now();requestAnimationFrame(frame)});
load();
