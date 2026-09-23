// SPDX-License-Identifier: GPL-3.0-or-later
import * as THREE from 'three';
import finishes from '../design/frame-finishes.json';
import extensions from '../design/frame-extensions.json';
for(const [id,spec] of Object.entries(extensions.styles))finishes.styles[id]={colors:spec.colors,labels:spec.labels,zones:spec.zones};
export {finishes};

// Color the actual fused relief, without extra meshes or changes to its surface.
export function frameRole(style,side,x,height,y){
  const theme=finishes.styles[style];
  if(!theme||height<=finishes.roof_mm+1e-4)return 0;
  if(side==='right')x=160-x;
  const zone=theme.zones.find(z=>x>=z.xy[0]&&y>=z.xy[1]&&x<=z.xy[2]&&y<=z.xy[3]);
  return zone?finishes.roles.indexOf(zone.role):1;
}
export function framePalette(style,body,accents){
  const theme=finishes.styles[style];
  const p=theme?{...theme.colors,body:body||theme.colors.body}:{body:body||'#304d4e'};
  for(const role of ['detail','accent','secondary'])p[role]=accents?.[role]||p[role]||p.body;return p;
}
export function createFrameFinishes(geometryFor,material){
  const cache=new Map();
  return function frame(style,side,body,accents){
    const path=`mechanical/revI/${side}-frame-${style}.stl`;
    if(!cache.has(path)){
      const source=geometryFor(path),g=source.clone(),p=g.getAttribute('position'),buckets=finishes.roles.map(()=>[]);
      for(let i=0;i<source.index.count;i+=3){
        const ids=[0,1,2].map(j=>source.index.getX(i+j));
        const mean=axis=>ids.reduce((sum,id)=>sum+p.getComponent(id,axis),0)/3;
        buckets[frameRole(style,side,mean(0),mean(1),mean(2))].push(...ids);
      }
      g.clearGroups();let offset=0;
      for(let role=0;role<buckets.length;role++){const count=buckets[role].length;if(count)g.addGroup(offset,count,role);offset+=count;}
      g.setIndex(new THREE.BufferAttribute(new Uint32Array(buckets.flat()),1));cache.set(path,g);
    }
    const palette=framePalette(style,body,accents);
    return {geometry:cache.get(path),material:finishes.roles.map(role=>material(palette[role]||palette.body)),palette};
  };
}
