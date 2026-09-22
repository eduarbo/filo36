// SPDX-License-Identifier: GPL-3.0-or-later
// Verify real raised features, geometry preservation and bounded material groups.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'build/viewer-multicolor');fs.mkdirSync(out,{recursive:true});
require('esbuild').buildSync({entryPoints:[path.join(__dirname,'finishes.js')],bundle:true,platform:'node',format:'cjs',outfile:path.join(out,'finishes.cjs')});
const {createFrameFinishes,finishes}=require(path.join(out,'finishes.cjs')),THREE=require('three');
const scene=JSON.parse(fs.readFileSync(path.join(root,'build/viewer-scene.json')));
const decode=(s,Type)=>{const b=Buffer.from(s,'base64');return new Type(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));};
const geometryFor=p=>{const s=scene.geometries[p],g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(decode(s.positions,Float32Array),3));g.setAttribute('normal',new THREE.BufferAttribute(decode(s.normals,Float32Array),3));g.setIndex(new THREE.BufferAttribute(decode(s.indices,Uint32Array),1));g.computeBoundingBox();return g;};
const make=createFrameFinishes(geometryFor,color=>({color}));
const probes={handheld:[[117,55,1,'D-pad'],[129.3,53.5,2,'Button A'],[125.7,56.1,2,'Button B'],[119.5,64,3,'Speaker']],tv:[[114.5,30,1,'CRT bezel'],[120,17.5,1,'Upper bezel'],[128.9,55.1,2,'Tuning knob'],[117,52.9,3,'Speaker']],cyberpunk:[[113.8,54,1,'Vent'],[129,52.2,2,'Trace'],[122,64,3,'Panel'],[128.1,61,3,'Node']]};
function triangleSet(g){const ids=Array.from(g.index.array),t=[];for(let i=0;i<ids.length;i+=3)t.push(ids.slice(i,i+3).join(','));return t.sort();}
function topRole(g,x,z){const p=g.attributes.position;for(const group of g.groups)for(let i=group.start;i<group.start+group.count;i+=3){const a=[0,1,2].map(j=>g.index.getX(i+j));if(a.some(n=>Math.abs(p.getY(n)-17.2)>.001))continue;const sides=a.map((v,j)=>{const w=a[(j+1)%3];return (p.getX(w)-p.getX(v))*(z-p.getZ(v))-(p.getZ(w)-p.getZ(v))*(x-p.getX(v));});if(sides.every(n=>n>=-1e-5)||sides.every(n=>n<=1e-5))return group.materialIndex;}return null;}
const checked=[];
for(const style of ['smooth','bevel','facet','handheld','tv','cyberpunk'])for(const side of ['left','right']){
 const id=`mechanical/revH/${side}-frame-${style}.stl`,source=geometryFor(id),f=make(style,side),g=f.geometry;
 assert.deepEqual(g.attributes.position.array,source.attributes.position.array);assert.deepEqual(g.attributes.normal.array,source.attributes.normal.array);assert.deepEqual(triangleSet(g),triangleSet(source));
 assert.equal(g.groups.length,finishes.styles[style]?4:1);let offset=0;
 for(const group of g.groups){assert.equal(group.start,offset);offset+=group.count;if(group.materialIndex){for(let i=group.start;i<offset;i+=3){const ids=[0,1,2].map(j=>g.index.getX(i+j));assert.ok(ids.every(n=>g.attributes.position.getY(n)>=16.6-1e-4),'Accents never extend into walls, cavity, roof or holes');}}}assert.equal(offset,g.index.count);
 for(const [x,z,role,label] of probes[style]||[])assert.equal(topRole(g,side==='right'?160-x:x,z),role,`${side} ${style}: ${label}`);
 const override=make(style,side,'#abcdef');assert.equal(override.material[0].color,'#abcdef');assert.equal(override.geometry,g,'Reuse geometry across body changes');
 checked.push({side,style,triangles:g.index.count/3,groups:g.groups.length,feature_probes:(probes[style]||[]).length});
}
const report={original_vertices_normals_and_triangles:true,raised_feature_probes:true,no_extra_geometry:true,max_material_groups:4,geometry_cached:true,checked};
fs.writeFileSync(path.join(out,'geometry.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
