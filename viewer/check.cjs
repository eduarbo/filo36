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
const scene=JSON.parse(html.match(/<script id="scene-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const target=process.env.FILO36_VIEWER_URL||pathToFileURL(path.join(root,'docs/index.html')).href;
const offline=target.startsWith('file:');

(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.FILO36_BROWSER?{executablePath:process.env.FILO36_BROWSER}:{})});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:960},acceptDownloads:true});
  const requests=[],errors=[];
  if(offline)await context.route(/^https?:/,route=>{requests.push(route.request().url());return route.abort();});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(target);await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('166'),null,{timeout:20000});
  await page.screenshot({path:path.join(root,'build/viewer-desktop.png')});
  const baseline=hash(await page.locator('#canvas').screenshot());
  const count=async()=>Number((await page.locator('#status').textContent()).match(/(\d+) componentes/)[1]);
  assert.equal(await count(),166);
  for(const group of new Set(scene.parts.map(p=>p.group))){
    await page.locator('#layer-'+group).uncheck();
    assert.equal(await count(),166-scene.parts.filter(p=>p.group===group).length,group);
    await page.locator('#layer-'+group).check();
  }
  await page.selectOption('#half','right');assert.equal(await count(),83);
  await page.selectOption('#half','left');assert.equal(await count(),83);
  await page.click('#stack');assert.equal(await page.locator('#explode').inputValue(),'55');
  await page.screenshot({path:path.join(root,'build/viewer-stack.png')});
  await page.selectOption('#view','bottom');await page.screenshot({path:path.join(root,'build/viewer-bottom.png')});
  await page.click('#reset');assert.equal(await count(),166);
  assert.equal(await page.locator('#half').inputValue(),'both');assert.equal(await page.locator('#explode').inputValue(),'0');
  assert.equal(hash(await page.locator('#canvas').screenshot()),baseline,'Full reset must restore the original rendered assembly');
  const box=await page.locator('#canvas').boundingBox();
  await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);await page.mouse.down();
  await page.mouse.move(box.x+box.width*.65,box.y+box.height*.65,{steps:8});await page.mouse.up();
  assert.notEqual(hash(await page.locator('#canvas').screenshot()),baseline,'Orbit drag must change view');
  await page.click('#reset');
  const downloadPromise=page.waitForEvent('download');await page.click('#glb');const download=await downloadPromise;
  const glbPath=path.join(root,'build/viewer-export.glb');await download.saveAs(glbPath);const glb=fs.readFileSync(glbPath);
  assert.equal(glb.toString('ascii',0,4),'glTF');assert.equal(glb.readUInt32LE(4),2);assert.equal(glb.readUInt32LE(8),glb.length);
  const jsonLength=glb.readUInt32LE(12),gltf=JSON.parse(glb.toString('utf8',20,20+jsonLength));
  assert.equal(gltf.nodes.filter(n=>n.mesh!==undefined).length,166);
  assert.equal(gltf.nodes.filter(n=>n.name.includes('KLP ')).length,36);
  const assembly=gltf.nodes.find(n=>n.name==='Filo36 revE · nominal');assert.deepEqual(assembly.matrix.slice(0,3),[.001,0,0]);
  assert.ok(assembly.extras.attribution.includes('braindefender'));
  const mobile=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true});
  if(offline)await mobile.route(/^https?:/,route=>{requests.push(route.request().url());return route.abort();});
  const phone=await mobile.newPage();phone.on('pageerror',e=>errors.push(e.message));await phone.goto(target);
  await phone.waitForFunction(()=>document.querySelector('#status').textContent.includes('166'));
  assert.equal(await phone.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'No horizontal overflow');
  await phone.locator('#inside').tap();assert.ok((await phone.locator('#status').textContent()).includes('componentes'));
  await phone.locator('#layer-panel summary').tap();await phone.locator('#layer-display').uncheck();
  await phone.locator('#reset').tap();assert.equal(await phone.locator('#explode').inputValue(),'0');
  await phone.screenshot({path:path.join(root,'build/viewer-mobile.png'),fullPage:true});
  assert.deepEqual(errors,[]);if(offline)assert.deepEqual(requests,[],'Offline viewer must not request network resources');
  const receipt={viewer_sha256:hash(Buffer.from(html)),target:offline?'local file with all HTTP(S) requests blocked':'public URL',
    browser:await browser.version(),desktop:true,narrow_viewport_emulation:true,physical_phone_tested:false,
    all_12_layer_filters:true,half_filters:true,orbit_drag:true,bottom_view:true,full_reset_pixel_identical:true,
    glb_objects:166,glb_keycaps:36,glb_units:'metres',runtime_errors:errors,offline_network_requests:requests.length};
  fs.writeFileSync(path.join(root,'build/viewer-ui-check.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt,null,2));await mobile.close();await context.close();
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
