// SPDX-License-Identifier: GPL-3.0-or-later
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';

import {copy,check} from './config.js';

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
function render(){renderer.render(scene,camera);}
controls.addEventListener('change',render);
let halfHeight=100;
function resize(){
  const {width,height}=canvas.parentElement.getBoundingClientRect();
  renderer.setSize(width,height,false);const aspect=width/height;
  camera.left=-halfHeight*aspect;camera.right=halfHeight*aspect;camera.top=halfHeight;camera.bottom=-halfHeight;
  camera.updateProjectionMatrix();render();
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
  for(const o of objects){
    o.visible=state.layers[o.userData.group]&&(state.half==='both'||state.half===o.userData.side);
    o.position.fromArray(o.userData.base);o.position.y+=o.userData.explode*state.explode;
  }
  $('half').value=state.half;$('view').value=state.view;$('explode').value=Math.round(state.explode*100);
  $('explosion').textContent=Math.round(state.explode*100)+' %';
  for(const key of Object.keys(labels))$('layer-'+key).checked=state.layers[key];
  const count=objects.filter(o=>o.visible).length;
  $('status').textContent=`Rev${data.revision} · ${count} visible components${state.explode?' · Exploded view':''}`;
  render();
}
function reset(){
  state.half='both';state.explode=0;state.view='iso';
  for(const key of Object.keys(labels))state.layers[key]=true;
  sync();fit(directions.iso);
}
$('layers').replaceChildren();
for(const [id,label] of Object.entries(labels)){
  const row=document.createElement('label');const input=document.createElement('input');
  input.type='checkbox';input.id='layer-'+id;input.checked=true;
  input.addEventListener('change',()=>{state.layers[id]=input.checked;sync();});
  row.append(input,document.createTextNode(label));$('layers').append(row);
}
$('half').addEventListener('change',e=>{state.half=e.target.value;sync();fit();});
$('view').addEventListener('change',e=>{state.view=e.target.value;fit(directions[state.view]);});
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
      const f=next.frames[side];o.geometry=geometryFor(`mechanical/revG/${side}-frame-${f.style}.stl`);o.material=material(f.color);o.userData.frame_style=f.style;
    }
  }
  configuration=copy(next);sync();updateChoices();message('Configuration applied. Save it for FreeCAD.');
}
$('key-target').onchange=updateChoices;$('key-variant').onchange=updateChoices;$('key-rotation').onchange=updateChoices;
$('apply-keys').onclick=()=>{try{applyConfiguration(candidate($('key-variant').value,Number($('key-rotation').value)));}catch(e){message(e.message,true);}};
for(const [id,label] of Object.entries(catalog.frame_styles))$('frame-style').add(new Option(label,id));
$('frame-style').value='bevel';
$('apply-frame').onclick=()=>{
 const cfg=copy(configuration);for(const side of ['left','right'])if($('frame-side').value==='both'||$('frame-side').value===side)cfg.frames[side]={style:$('frame-style').value,color:$('frame-color').value};
 try{applyConfiguration(cfg);}catch(e){message(e.message,true);}
};
for(const [id,label] of [['default','Original'],['normal-sculpted','Sculpted Normal'],['saddle-sculpted','Sculpted Saddle']])$('key-preset').add(new Option(label,id));
$('apply-preset').onclick=()=>{const cfg=copy(configuration);cfg.keycaps=copy(data.presets[$('key-preset').value].keycaps);try{applyConfiguration(cfg);}catch(e){message(e.message,true);}};
function downloadJSON(){const url=URL.createObjectURL(new Blob([JSON.stringify(configuration,null,2)+'\n'],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='Filo36-config.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}
$('save-config').onclick=downloadJSON;
$('load-config').onchange=async e=>{try{const f=e.target.files[0];if(f){if(f.size>100000)throw Error('File too large. Choose a configuration JSON.');applyConfiguration(JSON.parse(await f.text()));}}catch(error){message(error.message,true);}finally{e.target.value='';}};
$('default-config').onclick=()=>applyConfiguration(catalog.default_configuration);
applyConfiguration(configuration);

if(matchMedia('(max-width:760px)').matches)$('layer-panel').open=false;
resize();reset();

}
start().catch(error=>{document.getElementById('error').hidden=false;document.getElementById('error').textContent='Could not open the viewer: '+error.message;console.error(error);});
