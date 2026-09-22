// SPDX-License-Identifier: GPL-3.0-or-later
import * as THREE from 'three';

export const partInfo={
  lid:{name:'Display frame',short:'Frame',info:'Interchangeable printed cover. Pick a frame below; the display support stays in place.'},
  keycaps:{name:'KLP Lamé keycaps',short:'Keycaps',info:'Original Choc-stem meshes. Choose a preset or edit a key, row or thumb cluster.'},
  display:{name:'nice!view display',short:'Display',info:'Low-power display reference. The board envelope and screen content are illustrative.'},
  base:{name:'Printed base',short:'Base',info:'Continuous case flank with subtly rounded corners. Native source is editable in FreeCAD.'},
  plate:{name:'Switch plate',short:'Plate',info:'Holds the 36 Piantor switch positions and angles. Nominal plate height: 7.6 mm.'},
  switches:{name:'Choc switches',short:'Switches',info:'Low-profile switch envelopes. Seating, travel and printed keycap stems need physical fit tests.'},
  pcb:{name:'PCB',short:'PCB',info:'Custom wireless board outline. Routing and DRC remain unfinished; this is not a manufacturing file.'},
  battery:{name:'LiPo battery',short:'Battery',info:'Recessed 100 mAh battery envelope. Final cell, connector, protection and clearances remain to be qualified.'},
  mcu:{name:'nice!nano controller',short:'Controller',info:'Wireless controller envelope in the stacked bay. Final connections and radio performance are untested.'},
  supports:{name:'Insulating supports',short:'Supports',info:'Cradle, display sled and controller supports. Retention is a nominal CAD proposal.'},
  connectors:{name:'Connectors & controls',short:'Connections',info:'Sockets, battery connector, reset and power-switch references. Final supplied dimensions and cabling remain open.'},
  fasteners:{name:'Fasteners & feet',short:'Fasteners',info:'Illustrative screws, washers and feet. Screw length, seating and printed fit require a physical trial.'}
};

export function createExplorer({scene,camera,canvas,objects,onSelect,onClear,requestRender}){
  const $=id=>document.getElementById(id),svg=$('leader-lines'),host=$('callouts');
  const ray=new THREE.Raycaster(),pointer=new THREE.Vector2(),overlay=new THREE.Group();
  // Never mutate canonical materials or put decoration under an exported mesh.
  scene.add(overlay);
  const glow=new THREE.MeshBasicMaterial({color:'#75bd86',transparent:true,opacity:.33,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-2});
  let selected=null,hovered=null,enabled=true,down=null,pointers=new Set(),pickFrame=0,pendingEvent=null;
  const buttons=new Map(),paths=new Map(),dots=new Map();
  const same=(a,b)=>a&&b&&a.group===b.group&&a.side===b.side;
  const match=(o,ref)=>ref&&o.userData.group===ref.group&&(!ref.side||o.userData.side===ref.side)&&(!ref.key||o.userData.key===ref.key);
  const groupObjects=group=>objects.filter(o=>o.visible&&o.userData.group===group);
  const refOf=o=>({group:o.userData.group,side:o.userData.side,key:o.userData.key});
  function highlight(ref){hovered=ref;requestRender();}
  function select(ref){selected=ref;hovered=null;onSelect(ref);requestRender();}
  function clear(){selected=null;hovered=null;onClear();requestRender();}
  for(const [group,info] of Object.entries(partInfo)){
    const button=document.createElement('button');button.type='button';button.className='callout';button.hidden=true;button.dataset.group=group;
    button.innerHTML=`${info.short}<small></small>`;host.append(button);buttons.set(group,button);
    button.onpointerenter=e=>{if(e.pointerType!=='touch')highlight(button.ref);};button.onpointerleave=()=>highlight(null);
    button.onfocus=()=>highlight(button.ref);button.onblur=()=>highlight(null);button.onclick=()=>select(button.ref);
    const path=document.createElementNS(svg.namespaceURI,'path'),dot=document.createElementNS(svg.namespaceURI,'circle');dot.setAttribute('r','2');svg.append(path,dot);paths.set(group,path);dots.set(group,dot);
  }
  function hit(event){
    const rect=canvas.getBoundingClientRect();pointer.set((event.clientX-rect.left)/rect.width*2-1,1-(event.clientY-rect.top)/rect.height*2);
    ray.setFromCamera(pointer,camera);return ray.intersectObjects(objects.filter(o=>o.visible),false)[0];
  }
  canvas.addEventListener('pointerdown',e=>{pointers.add(e.pointerId);if(pickFrame)cancelAnimationFrame(pickFrame);pickFrame=0;hovered=null;down=pointers.size===1?{id:e.pointerId,x:e.clientX,y:e.clientY,moved:false}:null;requestRender();});
  canvas.addEventListener('pointermove',e=>{
    if(down&&Math.hypot(e.clientX-down.x,e.clientY-down.y)>6)down.moved=true;
    if(pointers.size||e.pointerType==='touch')return;
    pendingEvent={clientX:e.clientX,clientY:e.clientY};
    if(!pickFrame)pickFrame=requestAnimationFrame(()=>{pickFrame=0;const found=hit(pendingEvent);hovered=found?refOf(found.object):null;canvas.style.cursor=found?'pointer':'';requestRender();});
  });
  canvas.addEventListener('pointerup',e=>{const tap=down&&down.id===e.pointerId&&!down.moved&&pointers.size===1;pointers.delete(e.pointerId);down=null;if(tap){const found=hit(e);if(found)select(refOf(found.object));else clear();}});
  canvas.addEventListener('pointercancel',e=>{pointers.delete(e.pointerId);down=null;});
  canvas.addEventListener('pointerleave',()=>{if(pickFrame)cancelAnimationFrame(pickFrame);pickFrame=0;hovered=null;canvas.style.cursor='';requestRender();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('licenses').open)clear();});
  $('clear-selection').onclick=clear;
  $('annotations').onclick=()=>{enabled=!enabled;$('annotations').setAttribute('aria-pressed',String(enabled));requestRender();};
  function surfaceAnchor(group){
    const list=groupObjects(group),preferred=(hovered?.group===group?hovered:selected?.group===group?selected:null);
    list.sort((a,b)=>Number(match(b,preferred))-Number(match(a,preferred))||a.userData.side.localeCompare(b.userData.side));
    for(const o of list.slice(0,4)){
      if(preferred?.side&&o.userData.side!==preferred.side)continue;
      const box=new THREE.Box3().setFromObject(o),center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());
      const points=[center.clone(),new THREE.Vector3(center.x-size.x*.42,box.max.y,center.z),new THREE.Vector3(center.x+size.x*.42,box.max.y,center.z),new THREE.Vector3(center.x,box.max.y,center.z+size.z*.42)];
      for(const point of points){
        const p=point.project(camera);if(Math.abs(p.x)>.96||Math.abs(p.y)>.82||Math.abs(p.z)>1)continue;
        ray.setFromCamera(new THREE.Vector2(p.x,p.y),camera);
        const found=ray.intersectObjects(objects.filter(o=>o.visible),false)[0];
        if(found&&found.object.userData.group===group&&found.object.userData.side===o.userData.side){
          return {point:found.point.clone().project(camera),ref:refOf(found.object)};
        }
      }
    }
    return null;
  }
  // Anchor projection is cached across hover-only redraws; recompute after geometry,
  // visibility, camera, explode or resize changes. No work runs while idle.
  let stamp='',anchors=[];
  function update(){
    scene.updateMatrixWorld(true);camera.updateMatrixWorld();
    overlay.clear();const active=hovered||selected;
    for(const o of objects)if(o.visible&&match(o,active)){const mesh=new THREE.Mesh(o.geometry,glow);mesh.position.copy(o.position);mesh.rotation.copy(o.rotation);mesh.scale.copy(o.scale);overlay.add(mesh);}
    if(selected){$('selection-visibility').textContent=objects.some(o=>o.visible&&match(o,selected))?'':'Hidden in this view. Show its layer in Parts.';}
    for(const item of document.querySelectorAll('.part-item'))item.setAttribute('aria-pressed',String(selected?.group===item.dataset.group));
    const width=canvas.clientWidth,height=canvas.clientHeight;
    const signature=[width,height,...camera.matrixWorld.elements,...camera.projectionMatrix.elements,...objects.flatMap(o=>[o.visible,o.position.y,o.rotation.y,o.geometry.id]),active?.group,active?.side].join(',');
    if(enabled&&signature!==stamp){
      stamp=signature;anchors=[];
      const groups=Object.keys(partInfo).sort((a,b)=>Number(active?.group===b)-Number(active?.group===a));
      for(const group of groups){const anchor=surfaceAnchor(group);if(anchor)anchors.push({group,...anchor});if(anchors.length>=(width<600?2:8))break;}
    }
    svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
    for(const [g,b] of buttons){b.hidden=true;paths.get(g).style.display='none';dots.get(g).style.display='none';}
    if(!enabled)return;
    const rails=[[],[]];
    for(const a of (width<600?[...anchors].sort((a,b)=>a.point.x-b.point.x):anchors)){a.x=(a.point.x+1)*width/2;a.y=(1-a.point.y)*height/2;rails[width<600?(rails[0].length?1:0):(a.x>width/2?1:0)].push(a);}
    for(const [right,rail] of rails.entries()){
      rail.sort((a,b)=>a.y-b.y);let previous=52;
      for(let i=0;i<rail.length;i++){
        const a=rail[i],button=buttons.get(a.group);button.hidden=false;button.ref=a.ref;button.dataset.side=a.ref.side;
        button.querySelector('small').textContent=a.ref.side==='left'?'L':'R';button.setAttribute('aria-label',`${partInfo[a.group].name}, ${a.ref.side} half`);
        button.setAttribute('aria-pressed',String(same(selected,a.ref)));button.classList.toggle('active',!!same(active,a.ref));
        const bw=button.offsetWidth,bh=button.offsetHeight,top=Math.round(Math.max(previous,Math.min(a.y-bh/2,height-83-(rail.length-i)*(bh+5)))*10)/10;
        const left=right?width-bw-10:10;button.style.left=left+'px';button.style.top=(width<600?58:top)+'px';previous=top+bh+5;
        const endX=right?left:left+bw,endY=(width<600?58:top)+bh/2,path=paths.get(a.group),dot=dots.get(a.group);
        path.style.display='';dot.style.display='';path.setAttribute('d',`M ${a.x.toFixed(1)} ${a.y.toFixed(1)} L ${(endX+(right?-12:12)).toFixed(1)} ${endY.toFixed(1)} L ${endX} ${endY.toFixed(1)}`);
        path.classList.toggle('active',!!same(active,a.ref));dot.setAttribute('cx',a.x.toFixed(1));dot.setAttribute('cy',a.y.toFixed(1));
      }
    }
  }
  return {update,highlight,select,clear,get selected(){return selected;}};
}
