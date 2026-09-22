// SPDX-License-Identifier: GPL-3.0-or-later
export const copy=x=>JSON.parse(JSON.stringify(x));
export function polygon(hull,key,turn){const a=(-key.angle-turn)*Math.PI/180,c=Math.cos(a),s=Math.sin(a);return hull.map(([x,y])=>[key.x+x*c-y*s,key.y+x*s+y*c]);}
export function gap(a,b){
 const xs=p=>p.map(v=>v[0]),ys=p=>p.map(v=>v[1]);
 let result=Math.max(Math.min(...xs(b))-Math.max(...xs(a)),Math.min(...xs(a))-Math.max(...xs(b)),Math.min(...ys(b))-Math.max(...ys(a)),Math.min(...ys(a))-Math.max(...ys(b)));
 if(result>=.2)return result;
 for(const p of [a,b])for(let i=0;i<p.length;i++){
   const [x,y]=p[i],[xx,yy]=p[(i+1)%p.length],l=Math.hypot(xx-x,yy-y);if(l<1e-8)continue;
   const nx=-(yy-y)/l,ny=(xx-x)/l,aa=a.map(([u,v])=>u*nx+v*ny),bb=b.map(([u,v])=>u*nx+v*ny);
   result=Math.max(result,Math.min(...bb)-Math.max(...aa),Math.min(...aa)-Math.max(...bb));
 }
 return result;
}
export function normalize(config,c){const result=copy(config);if(!('cases' in result))result.cases=copy(c.default_configuration.cases);return result;}
export function check(config,c){
 const errors=[],variants=new Map(c.variants.map(v=>[v.id,v]));let minimum=Infinity;
 if(config?.schema!=='filo36-config-1'||config?.revision!=='I')return {errors:['Unsupported configuration format or revision.']};
 if(Object.keys(config.keycaps||{}).sort().join()!=='left,right'||Object.keys(config.frames||{}).sort().join()!=='left,right')return {errors:['Both halves are required.']};
 if(Object.keys(config.batteries||{}).sort().join()!=='left,right')return {errors:['Select a battery for each half.']};
 if('cases' in config){if(Object.keys(config.cases||{}).sort().join()!=='left,right')return {errors:['Select a case for each half.']};for(const choice of Object.values(config.cases))if(typeof choice?.style!=='string'||!Object.hasOwn(c.case_styles,choice.style)||typeof choice?.cover!=='boolean')return {errors:['Invalid case or display cover option.']};}
 for(const [side,keys] of Object.entries(c.layout)){
   if(!c.battery_profiles[config.batteries[side]])errors.push('Unknown battery profile.');
   if(Object.keys(config.keycaps[side]||{}).sort().join()!==keys.map(k=>k.ref).sort().join())return {errors:['Missing keys or unknown positions.']};
   const f=config.frames[side];if(!c.frame_styles[f?.style]||!/^#[0-9a-f]{6}$/i.test(f?.color))errors.push('Invalid frame or color.');
   const shapes=[];
   for(const k of keys){
     const x=config.keycaps[side][k.ref],v=variants.get(x?.variant);
     if(!v||!v.rotations_deg.includes(x?.rotation_deg)||!v.qualified_reference_positions.length){errors.push(`${side} ${k.ref}: unqualified variant or orientation.`);continue;}
     const p=polygon(v.hull_xy_mm,k,x.rotation_deg);shapes.push([k.ref,p]);const d=gap(p,c.frame_envelopes[side]);minimum=Math.min(minimum,d);
     if(d<c.minimum_clearance_mm-1e-7)errors.push(`${side} ${k.ref}: violates the frame clearance.`);
   }
   for(let i=0;i<shapes.length;i++)for(let j=i+1;j<shapes.length;j++){
     const d=gap(shapes[i][1],shapes[j][1]);minimum=Math.min(minimum,d);
     if(d<c.minimum_clearance_mm-1e-7)errors.push(`${side} ${shapes[i][0]}/${shapes[j][0]}: insufficient keycap clearance.`);
   }
 }
 return {errors,minimum};
}
