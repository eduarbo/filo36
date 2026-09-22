// SPDX-License-Identifier: GPL-3.0-or-later
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';

import {copy,check} from './config.js';
import {createExplorer,partInfo} from './explorer.js';
import {createPreviewRenderer} from './previews.js';

async function start(){
const $=id=>document.getElementById(id);
const compressed=Uint8Array.from(atob($('scene-data').textContent),c=>c.charCodeAt(0));
const data=JSON.parse(await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).text());
const catalog=data.catalog;let configuration=copy(catalog.default_configuration);
const variants=new Map(catalog.variants.map(v=>[v.id,v]));
const labels={base:'Bases',plate:'Plates',lid:'Frames / covers',keycaps:'Keycaps',switches:'Switches',pcb:'PCB',battery:'Batteries',mcu:'Controllers',display:'Displays',connectors:'Connectors',supports:'Supports',fasteners:'Fasteners / feet'};
const state={half:'both',layers:Object.fromEntries(Object.keys(labels).map(k=>[k,true])),explode:0,view:'iso'};
const directions={iso:[.35,1.6,1.75],top:[0,1,.0001],front:[0,0,1],back:[0,0,-1],right:[1,0,0],left:[-1,0,0],bottom:[0,-1,.0001]};
const scene=new THREE.Scene();scene.background=new THREE.Color('#edf0e9');
const camera=new THREE.OrthographicCamera(-180,180,100,-100,.1,3000);
const canvas=$('canvas');
let renderer;
try{renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false});}
catch(error){$('error').hidden=false;$('error').textContent='WebGL 2 could not start. Use a current Safari, Chrome or Firefox browser, or download the STEP files from the guide.';throw error;}
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
renderer.outputColorSpace=THREE.SRGBColorSpace;
const controls=new OrbitControls(camera,canvas);
controls.enableDamping=false;controls.minZoom=.2;controls.maxZoom=14;
controls.minPolarAngle=0;controls.maxPolarAngle=Math.PI;
controls.touches.ONE=THREE.TOUCH.ROTATE;controls.touches.TWO=THREE.TOUCH.DOLLY_PAN;
scene.add(new THREE.HemisphereLight('#ffffff','#9cafa0',2));
for(const [pos,power] of [[[20,250,160],2.4],[[-220,100,-180],1.1],[[360,30,20],.7]]){
  const light=new THREE.DirectionalLight('#ffffff',power);light.position.fromArray(pos);scene.add(light);
}

function decode(text,Type){const bytes=Uint8Array.from(atob(text),c=>c.charCodeAt(0));return new Type(bytes.buffer);}
const geometries=new Map();
function geometryFor(id){
  if(!id)return undefined;
  if(geometries.has(id))return geometries.get(id);
  const g=data.geometries[id];if(!g)throw Error('Geometry unavailable: '+id);
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.BufferAttribute(decode(g.positions,Float32Array),3));
  geometry.setAttribute('normal',new THREE.BufferAttribute(decode(g.normals,Float32Array),3));
  geometry.setIndex(new THREE.BufferAttribute(decode(g.indices,Uint32Array),1));
  geometry.computeBoundingBox();geometries.set(id,geometry);return geometry;
}
const materials=new Map();
function material(color){
  if(!materials.has(color))materials.set(color,new THREE.MeshStandardMaterial({color,roughness:.78,metalness:0}));
  return materials.get(color);
}
const objects=[];
for(const part of data.parts){
  let geometry=geometryFor(part.geometry),mat=material(part.color);
  if(part.primitive){
    const p=part.primitive;
    if(p.kind==='cylinder')geometry=new THREE.CylinderGeometry(p.radius,p.radius,p.height,32);
    else if(p.kind==='box')geometry=new THREE.BoxGeometry(...p.size);
    else{
      geometry=new THREE.PlaneGeometry(p.size[0],p.size[2]);geometry.rotateX(-Math.PI/2);
      const art=document.createElement('canvas');art.width=128;art.height=300;
      const ctx=art.getContext('2d');ctx.fillStyle=part.color;ctx.fillRect(0,0,128,300);
      ctx.fillStyle='#294234';ctx.textAlign='center';ctx.font='23px monospace';
      p.text.split(' / ').forEach((text,i)=>ctx.fillText(text,64,65+i*87));
      const texture=new THREE.CanvasTexture(art);texture.colorSpace=THREE.SRGBColorSpace;
      mat=new THREE.MeshBasicMaterial({map:texture});
    }
  }
  const mesh=new THREE.Mesh(geometry,mat);mesh.name=part.name;
  mesh.position.fromArray(part.position);mesh.rotation.y=THREE.MathUtils.degToRad(part.angle_deg);
  mesh.userData={group:part.group,side:part.side,base:[...part.position],explode:part.explode_mm,key:part.key_ref};
  objects.push(mesh);scene.add(mesh);
}
// Runtime scene uses x=CAD x, y=CAD z, z=CAD y; right-hand meshes are not mirrored again.
let explorer,renderFrame=0;
function render(){if(renderFrame)return;renderFrame=requestAnimationFrame(()=>{renderFrame=0;explorer?.update();renderer.render(scene,camera);});}
let orbiting=false;
controls.addEventListener('start',()=>{orbiting=true;explorer?.motion(true);});controls.addEventListener('end',()=>{orbiting=false;explorer?.motion(false);});
controls.addEventListener('change',()=>{
  if(orbiting&&state.view!=='iso'&&camera.position.clone().sub(controls.target).normalize().distanceTo(new THREE.Vector3(...directions[state.view]).normalize())>.001){
    state.view='iso';$('view').value='iso';for(const button of document.querySelectorAll('[data-view]'))button.setAttribute('aria-pressed',String(button.dataset.view==='iso'));
  }
  if(!orbiting)explorer?.cameraChanged();
  render();
});
let halfHeight=100;
function resize(){
  const {width,height}=canvas.parentElement.getBoundingClientRect();
  renderer.setSize(width,height,false);const aspect=width/height;
  camera.left=-halfHeight*aspect;camera.right=halfHeight*aspect;camera.top=halfHeight;camera.bottom=-halfHeight;
  camera.updateProjectionMatrix();explorer?.layoutChanged();render();
}
new ResizeObserver(resize).observe(canvas.parentElement);

function visibleBounds(){
  const box=new THREE.Box3();for(const o of objects)if(o.visible)box.union(new THREE.Box3().setFromObject(o));
  if(box.isEmpty())box.set(new THREE.Vector3(0,0,0),new THREE.Vector3(300,20,98));
  return box;
}
function fit(direction){
  const box=visibleBounds(),center=box.getCenter(new THREE.Vector3());
  const d=direction?new THREE.Vector3(...direction):camera.position.clone().sub(controls.target);
  camera.position.copy(center).add(d.normalize().multiplyScalar(500));controls.target.copy(center);
  camera.zoom=1;controls.update();camera.updateMatrixWorld();
  const right=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0),up=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1);
  let w=0,h=0;
  for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){
    const v=new THREE.Vector3(x,y,z).sub(center);w=Math.max(w,Math.abs(v.dot(right)));h=Math.max(h,Math.abs(v.dot(up)));
  }
  const aspect=canvas.clientWidth/canvas.clientHeight;halfHeight=Math.max(h,w/aspect,10)*1.13;resize();
}
function sync(){
  explorer?.invalidate();
  for(const o of objects){
    o.visible=state.layers[o.userData.group]&&(state.half==='both'||state.half===o.userData.side);
    o.position.fromArray(o.userData.base);o.position.y+=o.userData.explode*state.explode;
  }
  $('half').value=state.half;$('view').value=state.view;$('explode').value=Math.round(state.explode*100);
  $('explosion').textContent=Math.round(state.explode*100)+' %';
  for(const key of Object.keys(labels))$('layer-'+key).checked=state.layers[key];
  const count=objects.filter(o=>o.visible).length;
  $('status').textContent=`Rev${data.revision} · ${count} visible components${state.explode?' · Exploded view':''}`;
  for(const button of document.querySelectorAll('[data-view]'))button.setAttribute('aria-pressed',String(button.dataset.view===state.view));
  const isComplete=state.half==='both'&&state.explode===0&&Object.values(state.layers).every(Boolean);
  $('complete').setAttribute('aria-pressed',String(isComplete));
  $('inside').setAttribute('aria-pressed',String(!state.layers.base&&!state.layers.lid&&state.layers.pcb));
  $('stack').setAttribute('aria-pressed',String(!state.layers.base&&!state.layers.pcb&&state.layers.mcu));
  render();
}
function reset(){
  state.half='both';state.explode=0;state.view='iso';
  for(const key of Object.keys(labels))state.layers[key]=true;
  sync();fit(directions.iso);
}
function setCollapsed(value){
  document.querySelector('main').classList.toggle('detail-collapsed',value);$('collapse-detail').setAttribute('aria-expanded',String(!value));$('collapse-detail').textContent=value?'›':'‹';explorer?.layoutChanged();
}
function openPanel(id,section=id){
  setCollapsed(false);
  for(const name of ['frames','keycaps','view','files','about'])$('panel-'+name).hidden=id!==name;
  for(const button of document.querySelectorAll('.part-item'))button.setAttribute('aria-expanded',String(button.dataset.group===section));
  for(const name of ['view','files','about'])$('nav-'+name).setAttribute('aria-expanded',String(name===section));
  $('inspector').scrollTop=0;
}
$('collapse-detail').onclick=()=>setCollapsed($('collapse-detail').getAttribute('aria-expanded')==='true');
for(const name of ['view','files','about'])$('nav-'+name).onclick=()=>{if(name!=='files')explorer?.clear();openPanel(name);};
$('layers').replaceChildren();
for(const [id,label] of Object.entries(labels)){
  const row=document.createElement('div');row.className='part-row';row.dataset.group=id;
  const button=document.createElement('button');button.type='button';button.className='part-item';button.dataset.group=id;button.id='part-'+id;button.setAttribute('aria-expanded',String(id==='lid'));button.setAttribute('aria-controls','inspector');button.title=partInfo[id].name;button.setAttribute('aria-label',partInfo[id].name);
  const item=objects.find(o=>o.userData.group===id),color='#'+item.material.color.getHexString();
  const dot=document.createElement('span');dot.className='part-anchor';dot.dataset.group=id;dot.style.setProperty('--part-color',color);
  const name=document.createElement('span');name.className='part-name';name.textContent=partInfo[id].short;button.append(dot,name);
  const ref=()=>({group:id,side:state.half==='both'?null:state.half});
  button.onpointerenter=e=>{if(e.pointerType!=='touch')explorer.highlight(ref());};button.onpointerleave=()=>explorer.highlight(null);
  button.onfocus=()=>explorer.highlight(ref());button.onblur=()=>explorer.highlight(null);button.onclick=()=>explorer.select(ref());
  const visibility=document.createElement('label');visibility.className='visibility';visibility.title='Show / hide '+label;
  const input=document.createElement('input');input.type='checkbox';input.id='layer-'+id;input.checked=true;input.setAttribute('aria-label','Show '+label);
  input.addEventListener('change',()=>{state.layers[id]=input.checked;sync();});
  const eye=document.createElement('span');eye.className='eye';eye.textContent='◉';eye.setAttribute('aria-hidden','true');visibility.append(input,eye);
  row.append(button,visibility);$('layers').append(row);
}
$('half').addEventListener('change',e=>{state.half=e.target.value;sync();fit();});
function chooseView(view){state.view=view;sync();fit(directions[view]);}
$('view').addEventListener('change',e=>chooseView(e.target.value));
for(const button of document.querySelectorAll('[data-view]'))button.onclick=()=>chooseView(button.dataset.view);
$('explode').addEventListener('input',e=>{state.explode=Number(e.target.value)/100;sync();fit();});
$('complete').onclick=reset;$('reset').onclick=reset;$('fit').onclick=()=>fit();
$('inside').onclick=()=>{reset();for(const k of ['base','plate','lid','keycaps','switches','fasteners'])state.layers[k]=false;sync();fit();};
$('stack').onclick=()=>{reset();state.half='left';state.explode=.55;for(const k of Object.keys(labels))state.layers[k]=['battery','mcu','display','supports','connectors'].includes(k);sync();fit();};
$('credits').onclick=()=>$('licenses').showModal();$('close-credits').onclick=()=>$('licenses').close();
canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();$('error').hidden=false;$('error').textContent='Graphics context lost. Reload the page to restore the viewer.';});
$('glb').onclick=async()=>{
  const button=$('glb');button.disabled=true;button.textContent='Preparing GLB…';
  try{
    const assembly=new THREE.Group();assembly.name=`Filo36 rev${data.revision} · nominal`;assembly.scale.setScalar(.001);
    for(const object of objects){const clone=object.clone();clone.visible=true;clone.position.fromArray(object.userData.base);assembly.add(clone);}
    assembly.userData={configuration:copy(configuration),units:'metres',source:'https://github.com/eduarbo/filo36',limitations:data.limits,
      attribution:'Filo36 / Eduardo Ruiz, derived from Piantor by beekeeb (GPL-3.0); KLP Lame keycaps by braindefender (CC-BY-SA-4.0), unchanged meshes, placed and coloured.',
      licenses:['https://www.gnu.org/licenses/gpl-3.0.html','https://creativecommons.org/licenses/by-sa/4.0/'],
      keycap_source:'https://github.com/braindefender/KLP-Lame-Keycaps/tree/4a67a824232d3054c61599ea047c56a340faaba2'};
    const buffer=await new GLTFExporter().parseAsync(assembly,{binary:true,onlyVisible:true});
    const url=URL.createObjectURL(new Blob([buffer],{type:'model/gltf-binary'}));const link=document.createElement('a');
    link.href=url;link.download=`Filo36-rev${data.revision}-assembled.glb`;link.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
    button.textContent='GLB downloaded';
  }catch(error){button.textContent='Export failed; use STEP files';console.error(error);}
  finally{button.disabled=false;}
};
const message=(text,error=false)=>{$('config-status').textContent=text;$('config-status').dataset.error=String(error);};
const targetKeys=()=>Object.entries(catalog.layout).flatMap(([side,keys])=>keys.filter(k=>{
  const t=$('key-target').value;
  return t==='all'||t==='thumbs'&&k.row===3||t===`row-${k.row}`||t===`${side}:${k.ref}`;
}).map(k=>[side,k]));
for(const [value,label] of [['all','All keys'],['row-0','Top row'],['row-1','Home row'],['row-2','Bottom row'],['thumbs','Thumbs']])$('key-target').add(new Option(label,value));
for(const [side,keys] of Object.entries(catalog.layout))for(const k of keys)$('key-target').add(new Option(`${side==='left'?'Left':'Right'} ${k.ref}`,`${side}:${k.ref}`));
for(const v of catalog.variants)$('key-variant').add(new Option(v.label+(v.status==='unqualified'?' · no qualified position':''),v.id));
$('key-variant').value='choc_stem_choc_size_normal';
function candidate(id,turn){const cfg=copy(configuration);for(const [side,k] of targetKeys())cfg.keycaps[side][k.ref]={variant:id,rotation_deg:turn};return cfg;}
function updateChoices(){
  const v=variants.get($('key-variant').value),old=Number($('key-rotation').value);
  $('key-rotation').replaceChildren(...v.rotations_deg.map(a=>new Option(a+'°',String(a))));
  if(v.rotations_deg.includes(old))$('key-rotation').value=String(old);
  const turn=Number($('key-rotation').value);
  for(const option of $('key-variant').options){
    const item=variants.get(option.value),rotation=item.rotations_deg.includes(turn)?turn:item.rotations_deg[0];
    // Fast reference-position gate, then exact combination check on Apply.
    option.disabled=!targetKeys().every(([side,k])=>item.qualified_reference_positions.some(p=>p.side===side&&p.key===k.ref&&p.rotation_deg===rotation));
  }
  const result=check(candidate(v.id,turn),catalog);$('apply-keys').disabled=result.errors.length>0;
  $('key-fit').textContent=result.errors.length?result.errors[0]:`Conservative clearance ≥ ${result.minimum.toFixed(2)} mm. Physical seating and travel untested.`;
}
function applyConfiguration(next){
  const result=check(next,catalog);if(result.errors.length)throw Error(result.errors[0]);
  for(const o of objects){
    const {side,key,group}=o.userData;
    if(group==='keycaps'){
      const choice=next.keycaps[side][key],v=variants.get(choice.variant),k=catalog.layout[side].find(k=>k.ref===key);
      o.geometry=geometryFor(v.path);o.rotation.y=THREE.MathUtils.degToRad(k.angle+choice.rotation_deg);o.userData.base[1]=v.seating_z_mm;
      o.userData.variant=v.id;o.userData.cap_rotation_deg=choice.rotation_deg;
    }
    if(group==='lid'){
      const f=next.frames[side];o.geometry=geometryFor(`mechanical/revH/${side}-frame-${f.style}.stl`);o.material=material(f.color);o.userData.frame_style=f.style;
    }
  }
  configuration=copy(next);sync();updateChoices();syncConfigurationUI();message('Configuration applied.');
}
function chooseKeyTarget(){
  const target=targetKeys();if(target.length===1){const [side,k]=target[0],choice=configuration.keycaps[side][k.ref];$('key-variant').value=choice.variant;updateChoices();$('key-rotation').value=String(choice.rotation_deg);}
  updateChoices();
}
$('key-target').onchange=chooseKeyTarget;$('key-variant').onchange=updateChoices;$('key-rotation').onchange=updateChoices;
$('apply-keys').onclick=()=>{try{applyConfiguration(candidate($('key-variant').value,Number($('key-rotation').value)));}catch(e){message(e.message,true);}};
let frameSide='both';
const preview=createPreviewRenderer(renderer,geometryFor);
function card(id,label,src){
  const button=document.createElement('button');button.type='button';button.className='preview-card';button.dataset.choice=id;button.setAttribute('aria-pressed','false');
  const img=document.createElement('img');img.src=src;img.alt='';img.width=220;img.height=220;const text=document.createElement('span');text.textContent=label;button.append(img,text);button.setAttribute('aria-label',label);return button;
}
function frameTargets(){return frameSide==='both'?['left','right']:[frameSide];}
function setFrameSide(side){frameSide=side;syncConfigurationUI();}
function applyFrame(change){
  const cfg=copy(configuration);for(const side of frameTargets())Object.assign(cfg.frames[side],change);
  try{
    applyConfiguration(cfg);
    // A new style must be visible even when coming from the internal stack study.
    if(change.style){const needsFit=state.explode>0||!state.layers.lid||frameSide==='both'&&state.half!=='both'||state.half!=='both'&&!frameTargets().includes(state.half);
      if(needsFit){for(const k of Object.keys(state.layers))state.layers[k]=true;state.explode=0;state.half=frameSide;sync();fit();}}
  }catch(e){message(e.message,true);}
}
for(const [id,label] of Object.entries(catalog.frame_styles)){
  const button=card(id,label,preview.image([{path:`mechanical/revH/left-frame-${id}.stl`}]));button.dataset.style=id;
  button.onclick=()=>applyFrame({style:id});$('frame-grid').append(button);
}
for(const button of $('frame-target').children)button.onclick=()=>setFrameSide(button.dataset.side);
for(const [color,label] of [['#304d4e','Deep teal'],['#ded8c6','Linen'],['#ad7656','Clay'],['#363b3b','Graphite']]){
  const button=document.createElement('button');button.type='button';button.dataset.color=color;button.title=label;button.setAttribute('aria-label',label);button.setAttribute('aria-pressed','false');button.style.setProperty('--swatch',color);button.onclick=()=>applyFrame({color});$('swatches').append(button);
}
$('frame-color').oninput=e=>applyFrame({color:e.target.value});
for(const [id,label] of [['default','Original'],['normal-sculpted','Sculpted Normal'],['saddle-sculpted','Sculpted Saddle']]){
  const entries=['K01','K11','K21'].map((key,i)=>({path:variants.get(data.presets[id].keycaps.left[key].variant).path,rotation:data.presets[id].keycaps.left[key].rotation_deg,center:[(i-1)*20,0,0]}));
  const button=card(id,label,preview.image(entries,[.5,1,2]));button.dataset.preset=id;
  button.onclick=()=>{const cfg=copy(configuration);cfg.keycaps=copy(data.presets[id].keycaps);try{applyConfiguration(cfg);}catch(e){message(e.message,true);}};$('key-presets').append(button);
}
preview.finish();
function syncConfigurationUI(){
  const frames=frameTargets().map(side=>configuration.frames[side]),styles=new Set(frames.map(f=>f.style)),colors=new Set(frames.map(f=>f.color.toLowerCase()));
  for(const button of $('frame-target').children)button.setAttribute('aria-pressed',String(button.dataset.side===frameSide));
  for(const button of $('frame-grid').children)button.setAttribute('aria-pressed',String(styles.size===1&&styles.has(button.dataset.style)));
  $('frame-current').textContent=styles.size===1?catalog.frame_styles[frames[0].style]:'Mixed styles';
  $('color-current').textContent=colors.size===1?[...colors][0]:'Mixed colors';
  for(const button of $('swatches').children)button.setAttribute('aria-pressed',String(colors.size===1&&colors.has(button.dataset.color)));
  // The color input has no mixed state: its visible companion explicitly names it.
  $('frame-color').value=frames[0].color;$('frame-color').setAttribute('aria-label',colors.size===1?'Custom frame color':'Custom frame color; mixed colors, changing this applies to both halves');
  for(const button of $('key-presets').children){const preset=data.presets[button.dataset.preset];const same=Object.entries(configuration.keycaps).every(([side,keys])=>Object.entries(keys).every(([ref,c])=>c.variant===preset.keycaps[side][ref].variant&&c.rotation_deg===preset.keycaps[side][ref].rotation_deg));button.setAttribute('aria-pressed',String(same));}
}
explorer=createExplorer({scene,camera,canvas,objects,requestRender:render,
  onSelect(ref){
    $('selection').hidden=false;$('selection').classList.toggle('compact',['lid','keycaps'].includes(ref.group));$('selection-meta').textContent=(ref.side?ref.side+' half':'Both halves')+(ref.key?' / '+ref.key:'');
    $('selection-title').textContent=partInfo[ref.group].name;$('selection-info').textContent=partInfo[ref.group].info;
    if(ref.group==='lid'){setFrameSide(ref.side||'both');openPanel('frames','lid');}
    else if(ref.group==='keycaps'){openPanel('keycaps','keycaps');$('key-details').open=true;if(ref.key)$('key-target').value=ref.side+':'+ref.key;else $('key-target').value='all';chooseKeyTarget();}
    else openPanel('none',ref.group);
  },onClear(){$('selection').hidden=true;}
});
$('load-trigger').onclick=()=>$('load-config').click();
function downloadJSON(){const url=URL.createObjectURL(new Blob([JSON.stringify(configuration,null,2)+'\n'],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='Filo36-config.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}
$('save-config').onclick=downloadJSON;
$('load-config').onchange=async e=>{try{const f=e.target.files[0];if(f){if(f.size>100000)throw Error('File too large. Choose a configuration JSON.');applyConfiguration(JSON.parse(await f.text()));}}catch(error){message(error.message,true);}finally{e.target.value='';}};
$('default-config').onclick=()=>applyConfiguration(catalog.default_configuration);
applyConfiguration(configuration);


resize();reset();openPanel('frames','lid');

}
start().catch(error=>{document.getElementById('error').hidden=false;document.getElementById('error').textContent='Could not open the viewer: '+error.message;console.error(error);});
