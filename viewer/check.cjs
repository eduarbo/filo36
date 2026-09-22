// Functional acceptance: offline loading, layers, camera, full reset, GLB and narrow viewport.
// SPDX-License-Identifier: GPL-3.0-or-later
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const crypto=require('node:crypto');
const {chromium}=require(process.env.FILO36_PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const hash=buffer=>crypto.createHash('sha256').update(buffer).digest('hex');
const html=fs.readFileSync(path.join(root,'docs/index.html'),'utf8');
const scene=JSON.parse(require('node:zlib').gunzipSync(Buffer.from(html.match(/<script id="scene-data" type="application\/octet-stream">([\s\S]*?)<\/script>/)[1],'base64')));
const target=process.env.FILO36_VIEWER_URL||pathToFileURL(path.join(root,'docs/index.html')).href;
const offline=target.startsWith('file:');

(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.FILO36_BROWSER?{executablePath:process.env.FILO36_BROWSER}:{})});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:960},acceptDownloads:true});
  const requests=[],errors=[];
  if(offline)await context.route(/^https?:/,route=>{requests.push(route.request().url());return route.abort();});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(target);await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('168'),null,{timeout:60000});
  await page.screenshot({path:path.join(root,'build/viewer-desktop.png')});
  const baseline=hash(await page.locator('#canvas').screenshot());
  const count=async()=>Number((await page.locator('#status').textContent()).match(/(\d+) visible components/)[1]);
  assert.equal(await count(),168);
  for(const group of new Set(scene.parts.map(p=>p.group))){
    await page.locator('#layer-'+group).uncheck();
    assert.equal(await count(),168-scene.parts.filter(p=>p.group===group).length,group);
    await page.locator('#layer-'+group).check();
  }
  await page.selectOption('#half','right');assert.equal(await count(),84);
  await page.selectOption('#half','left');assert.equal(await count(),84);
  await page.click('#stack');assert.equal(await page.locator('#explode').inputValue(),'55');
  await page.screenshot({path:path.join(root,'build/viewer-stack.png')});
  await page.selectOption('#view','bottom');await page.screenshot({path:path.join(root,'build/viewer-bottom.png')});
  await page.click('#reset');assert.equal(await count(),168);
  assert.equal(await page.locator('#half').inputValue(),'both');assert.equal(await page.locator('#explode').inputValue(),'0');
  assert.equal(hash(await page.locator('#canvas').screenshot()),baseline,'Full reset must restore the original rendered assembly');
  const box=await page.locator('#canvas').boundingBox();
  await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);await page.mouse.down();
  await page.mouse.move(box.x+box.width*.65,box.y+box.height*.65,{steps:8});await page.mouse.up();
  assert.notEqual(hash(await page.locator('#canvas').screenshot()),baseline,'Orbit drag must change view');
  await page.click('#reset');
  // Select an actual alternate mesh and orientation, then export that choice.
  await page.selectOption('#key-target','left:K30');
  await page.selectOption('#key-variant','choc_stem_mx_size_normal_90deg'); // gitleaks:allow -- public upstream STL variant ID, not a credential
  assert.equal(await page.locator('#key-rotation').inputValue(),'90');
  await page.click('#apply-keys');
  await page.selectOption('#frame-side','left');await page.selectOption('#frame-style','facet');
  await page.locator('#frame-color').fill('#ad7656');await page.click('#apply-frame');
  const configDownload=page.waitForEvent('download');await page.click('#save-config');
  const downloadedConfig=await configDownload;const configPath=path.join(root,'build/revG/viewer-config.json');await downloadedConfig.saveAs(configPath);
  const config=JSON.parse(fs.readFileSync(configPath));
  assert.equal(config.keycaps.left.K30.variant,'choc_stem_mx_size_normal_90deg');assert.equal(config.keycaps.left.K30.rotation_deg,90);
  assert.deepEqual(config.frames.left,{style:'facet',color:'#ad7656'});
  await page.click('#default-config');await page.locator('#load-config').setInputFiles(configPath);
  await page.waitForFunction(()=>document.querySelector('#config-status').textContent.includes('applied'));
  assert.notEqual(hash(await page.locator('#canvas').screenshot()),baseline,'Custom configuration changes the actual assembly');
  // An incompatible mixed configuration must not replace the current one.
  const invalid=JSON.parse(JSON.stringify(config));invalid.keycaps.left.K01={variant:'choc_stem_mx_size_normal',rotation_deg:0};
  await page.locator('#load-config').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(invalid))});
  await page.waitForFunction(()=>document.querySelector('#config-status').dataset.error==='true');
  const downloadPromise=page.waitForEvent('download');await page.click('#glb');const download=await downloadPromise;
  const glbPath=path.join(root,'build/viewer-export.glb');await download.saveAs(glbPath);const glb=fs.readFileSync(glbPath);
  assert.equal(glb.toString('ascii',0,4),'glTF');assert.equal(glb.readUInt32LE(4),2);assert.equal(glb.readUInt32LE(8),glb.length);
  const jsonLength=glb.readUInt32LE(12),gltf=JSON.parse(glb.toString('utf8',20,20+jsonLength));
  assert.equal(gltf.nodes.filter(n=>n.mesh!==undefined).length,168);
  assert.equal(gltf.nodes.filter(n=>n.name.includes('KLP ')).length,36);
  const assembly=gltf.nodes.find(n=>n.name==='Filo36 revG · nominal');assert.deepEqual(assembly.matrix.slice(0,3),[.001,0,0]);
  assert.ok(assembly.extras.attribution.includes('braindefender'));
  assert.deepEqual(assembly.extras.configuration,config);
  const customCap=gltf.nodes.find(n=>n.name==='left · KLP K30');assert.equal(customCap.extras.variant,config.keycaps.left.K30.variant);
  const customFrame=gltf.nodes.find(n=>n.extras?.side==='left'&&n.extras?.group==='lid');assert.equal(customFrame.extras.frame_style,'facet');
  assert.equal(download.suggestedFilename(),'Filo36-revG-assembled.glb');
  function positionBytes(node){
    const primitive=gltf.meshes[node.mesh].primitives[0],a=gltf.accessors[primitive.attributes.POSITION],v=gltf.bufferViews[a.bufferView];
    assert.equal(a.componentType,5126);assert.equal(a.type,'VEC3');assert.ok(!v.byteStride||v.byteStride===12);
    const binStart=20+jsonLength+8,at=binStart+(v.byteOffset||0)+(a.byteOffset||0);
    return glb.subarray(at,at+a.count*12);
  }
  const capPath=scene.catalog.variants.find(v=>v.id===config.keycaps.left.K30.variant).path;
  assert.deepEqual(positionBytes(customCap),Buffer.from(scene.geometries[capPath].positions,'base64'),'GLB must contain selected cap vertices');
  assert.deepEqual(positionBytes(customFrame),Buffer.from(scene.geometries['mechanical/revG/left-frame-facet.stl'].positions,'base64'),'GLB must contain selected frame vertices');
  await page.click('#default-config');await page.click('#reset');
  assert.equal(hash(await page.locator('#canvas').screenshot()),baseline,'Default config plus reset restores exact rendered assembly');
  await page.selectOption('#key-target','all');
  assert.equal(await page.locator('#key-variant option[value="choc_stem_mx_size_normal"]').evaluate(o=>o.disabled),true);
  await page.selectOption('#key-preset','saddle-sculpted');await page.click('#apply-preset');assert.equal(await page.locator('#config-status').getAttribute('data-error'),'false');
  await page.click('#default-config');
  const mobile=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true});
  if(offline)await mobile.route(/^https?:/,route=>{requests.push(route.request().url());return route.abort();});
  const phone=await mobile.newPage();phone.on('pageerror',e=>errors.push(e.message));await phone.goto(target);
  await phone.waitForFunction(()=>document.querySelector('#status').textContent.includes('168'));
  assert.equal(await phone.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'No horizontal overflow');
  await phone.locator('#inside').tap();assert.ok((await phone.locator('#status').textContent()).includes('components'));
  await phone.locator('#layer-panel summary').tap();await phone.locator('#layer-display').uncheck();
  await phone.locator('#reset').tap();assert.equal(await phone.locator('#explode').inputValue(),'0');
  await phone.evaluate(()=>scrollTo(0,0));await phone.evaluate(()=>new Promise(requestAnimationFrame));
  await phone.screenshot({path:path.join(root,'build/viewer-mobile.png'),fullPage:true});
  assert.deepEqual(errors,[]);if(offline)assert.deepEqual(requests,[],'Offline viewer must not request network resources');
  const receipt={viewer_sha256:hash(Buffer.from(html)),target:offline?'local file with all HTTP(S) requests blocked':'public URL',
    browser:await browser.version(),desktop:true,narrow_viewport_emulation:true,physical_phone_tested:false,
    all_12_layer_filters:true,half_filters:true,orbit_drag:true,bottom_view:true,full_reset_pixel_identical:true,
    keycap_variant_selection:true,frame_style_and_color:true,json_roundtrip:true,invalid_combination_rejected:true,glb_matches_custom_configuration:true,glb_selected_vertices_exact:true,glb_objects:168,glb_keycaps:36,glb_units:'metres',runtime_errors:errors,offline_network_requests:requests.length};
  fs.writeFileSync(path.join(root,'build/viewer-ui-check.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt,null,2));await mobile.close();await context.close();
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
