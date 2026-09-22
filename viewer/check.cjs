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

async function checkDirectory(page){
  await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  assert.equal(await page.locator('.callout,#callouts').count(),0,'No floating tags');
  const entries=await page.locator('.part-item,.section-links button,#collapse-detail').evaluateAll(nodes=>nodes.map(e=>{
    const r=e.getBoundingClientRect(),name=e.querySelector('.part-name'),text=name?.getBoundingClientRect();
    const at=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
    return{id:e.id,visible:r.width>0&&r.height>0&&r.x>=0&&r.y>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1&&!!at&&(e===at||e.contains(at)),textFits:!text||text.width>0&&name.scrollWidth<=name.clientWidth+1};
  }));
  assert.equal(entries.length,16);assert.ok(entries.every(e=>e.visible&&e.textFits),'All 12 components plus 4 section controls must be unclipped: '+JSON.stringify(entries.filter(e=>!e.visible||!e.textFits)));
}
async function checkLink(page,group){
  await page.waitForFunction(group=>{const p=document.querySelector('#part-link'),r=document.querySelector('main').getBoundingClientRect(),a=document.querySelector(`.part-anchor[data-group=${group}]`).getBoundingClientRect();return !p.hasAttribute('hidden')&&p.dataset.group===group&&Math.abs(Number(p.dataset.endX)+r.x-a.x-a.width/2)<1&&Math.abs(Number(p.dataset.endY)+r.y-a.y-a.height/2)<1},group);
  const info=await page.evaluate(group=>{const p=document.querySelector('#part-link'),r=document.querySelector('main').getBoundingClientRect(),a=document.querySelector(`.part-anchor[data-group=${group}]`).getBoundingClientRect();return{dx:Math.abs(Number(p.dataset.endX)+r.x-a.x-a.width/2),dy:Math.abs(Number(p.dataset.endY)+r.y-a.y-a.height/2)}},group);
  assert.ok(info.dx<1&&info.dy<1,'Line must end at its exact sidebar anchor: '+JSON.stringify(info));
}

(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.FILO36_BROWSER?{executablePath:process.env.FILO36_BROWSER}:{})});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:960},acceptDownloads:true});
  const requests=[],errors=[];
  if(offline)await context.route(/^https?:/,route=>{requests.push(route.request().url());return route.abort();});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(target);
  if(!offline){
    // Hash the actual loaded scene in the browser. Large document responses can
    // be evicted from Chromium's inspector cache; DOM data remains available.
    const delivered=await page.evaluate(async()=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(document.querySelector('#scene-data').textContent)))).map(n=>n.toString(16).padStart(2,'0')).join(''));
    const embedded=html.match(/<script id="scene-data" type="application\/octet-stream">([\s\S]*?)<\/script>/)[1];
    assert.equal(delivered,hash(Buffer.from(embedded)),'Public browser must load the exact current CAD scene');
  }
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('168'),null,{timeout:60000});
  await checkDirectory(page);
  await page.screenshot({path:path.join(root,'build/viewer-desktop.png')});
  // Compare WebGL output without the overlaid DOM controls or label borders.
  // Opacity keeps hover/focus active; the separate full-page captures include UI.
  const baseline=hash(await page.locator('#canvas').screenshot({style:'.stage > :not(canvas),#leader-lines{opacity:0!important}'}));
  const count=async()=>Number((await page.locator('#status').textContent()).match(/(\d+) visible components/)[1]);
  assert.equal(await count(),168);
  await page.click('#nav-view');
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
  assert.equal(hash(await page.locator('#canvas').screenshot({style:'.stage > :not(canvas),#leader-lines{opacity:0!important}'})),baseline,'Full reset must restore the original rendered assembly');
  const box=await page.locator('#canvas').boundingBox();
  await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);await page.mouse.down();
  await page.mouse.move(box.x+box.width*.65,box.y+box.height*.65,{steps:8});await page.mouse.up();
  assert.notEqual(hash(await page.locator('#canvas').screenshot({style:'.stage > :not(canvas),#leader-lines{opacity:0!important}'})),baseline,'Orbit drag must change view');
  assert.equal(await page.locator('#selection').isVisible(),false,'Orbit drag must not select a component');
  await page.click('#reset');
  // Select an actual alternate mesh and orientation, then export that choice.
  await page.click('#part-keycaps');if(!await page.locator('#key-details').evaluate(d=>d.open))await page.locator('#key-details summary').click();
  await page.selectOption('#key-target','left:K30');
  await page.selectOption('#key-variant','choc_stem_mx_size_normal_90deg'); // gitleaks:allow -- public upstream STL variant ID, not a credential
  assert.equal(await page.locator('#key-rotation').inputValue(),'90');
  await page.click('#apply-keys');
  await page.click('#part-lid');await page.click('#frame-target [data-side=left]');
  assert.equal(await page.locator('#frame-grid button').count(),6);
  assert.equal(new Set(await page.locator('#frame-grid img').evaluateAll(imgs=>imgs.map(i=>i.src))).size,6,'Six previews use distinct actual geometries');
  const themePixels=[];
  for(const theme of ['smooth','bevel','facet','handheld','tv','cyberpunk']){
    await page.click(`[data-style=${theme}]`);
    assert.equal(await page.locator(`[data-style=${theme}]`).getAttribute('aria-pressed'),'true');
    assert.equal(await page.locator('#config-status').getAttribute('data-error'),'false');
    themePixels.push(hash(await page.locator('#canvas').screenshot({style:'.stage > :not(canvas),#leader-lines{opacity:0!important}'})));
  }
  assert.equal(new Set(themePixels).size,6,'All six covers must change actual rendered geometry');
  await page.locator('#frame-color').fill('#ad7656');
  await page.click('#frame-target [data-side=right]');await page.click('[data-color="#ded8c6"]');
  await page.click('#frame-target [data-side=both]');
  assert.equal(await page.locator('#frame-current').textContent(),'Mixed styles');
  assert.equal(await page.locator('#color-current').textContent(),'Mixed colors');
  assert.equal(await page.locator('#frame-grid [aria-pressed=true]').count(),0);
  // Keyboard activation applies a complete theme; later body overrides stay independent.
  await page.locator('[data-style=tv]').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#frame-color').inputValue(),'#976044');
  await page.click('#frame-target [data-side=left]');await page.click('[data-style=cyberpunk]');
  assert.equal(await page.locator('#frame-color').inputValue(),'#303440');
  await page.locator('#frame-color').fill('#ad7656');
  await page.click('#frame-target [data-side=right]');await page.click('[data-color="#ded8c6"]');
  await page.click('#frame-target [data-side=left]');
  await page.click('#nav-files');
  const configDownload=page.waitForEvent('download');await page.click('#save-config');
  const downloadedConfig=await configDownload;const configPath=path.join(root,'build/revH/viewer-config.json');await downloadedConfig.saveAs(configPath);
  const config=JSON.parse(fs.readFileSync(configPath));
  assert.equal(config.keycaps.left.K30.variant,'choc_stem_mx_size_normal_90deg');assert.equal(config.keycaps.left.K30.rotation_deg,90);
  assert.deepEqual(config.frames.left,{style:'cyberpunk',color:'#ad7656'});
  assert.deepEqual(config.frames.right,{style:'tv',color:'#ded8c6'});
  await page.click('#default-config');await page.locator('#load-config').setInputFiles(configPath);
  await page.waitForFunction(()=>document.querySelector('[data-style=cyberpunk]').getAttribute('aria-pressed')==='true');
  assert.equal(await page.locator('[data-style=cyberpunk]').getAttribute('aria-pressed'),'true');
  assert.equal(await page.locator('#frame-color').inputValue(),'#ad7656');
  assert.notEqual(hash(await page.locator('#canvas').screenshot({style:'.stage > :not(canvas),#leader-lines{opacity:0!important}'})),baseline,'Custom configuration changes the actual assembly');
  // An incompatible mixed configuration must not replace the current one.
  const invalid=JSON.parse(JSON.stringify(config));invalid.keycaps.left.K01={variant:'choc_stem_mx_size_normal',rotation_deg:0};
  await page.locator('#load-config').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(invalid))});
  await page.waitForFunction(()=>document.querySelector('#config-status').dataset.error==='true');
  // Labels open contextual controls and highlights never enter the export.
  const frameLabel=page.locator('#part-lid');
  assert.equal(await frameLabel.isVisible(),true);
  await page.keyboard.press('Escape');
  const withoutHighlight=hash(await page.locator('#canvas').screenshot({style:'.stage > :not(canvas),#leader-lines{opacity:0!important}'}));
  await frameLabel.hover();
  assert.notEqual(hash(await page.locator('#canvas').screenshot({style:'.stage > :not(canvas),#leader-lines{opacity:0!important}'})),withoutHighlight,'Sidebar hover highlights geometry');
  await frameLabel.click();
  assert.equal(await page.locator('#selection-title').textContent(),'Display frame');
  assert.equal(await page.locator('#part-lid').getAttribute('aria-expanded'),'true');
  assert.equal(await page.locator('#frame-target [data-side=both]').getAttribute('aria-pressed'),'true');
  assert.equal(await frameLabel.getAttribute('aria-expanded'),'true');
  await checkLink(page,'lid');await page.click('#nav-files');
  const downloadPromise=page.waitForEvent('download');await page.click('#glb');const download=await downloadPromise;
  const glbPath=path.join(root,'build/viewer-export.glb');await download.saveAs(glbPath);const glb=fs.readFileSync(glbPath);
  assert.equal(glb.toString('ascii',0,4),'glTF');assert.equal(glb.readUInt32LE(4),2);assert.equal(glb.readUInt32LE(8),glb.length);
  const jsonLength=glb.readUInt32LE(12),gltf=JSON.parse(glb.toString('utf8',20,20+jsonLength));
  assert.equal(gltf.nodes.filter(n=>n.mesh!==undefined).length,168);
  assert.equal(gltf.nodes.filter(n=>n.name.includes('KLP ')).length,36);
  const assembly=gltf.nodes.find(n=>n.name==='Filo36 revH · nominal');assert.deepEqual(assembly.matrix.slice(0,3),[.001,0,0]);
  assert.ok(assembly.extras.attribution.includes('braindefender'));
  assert.deepEqual(assembly.extras.configuration,config);
  const customCap=gltf.nodes.find(n=>n.name==='left · KLP K30');assert.equal(customCap.extras.variant,config.keycaps.left.K30.variant);
  const customFrame=gltf.nodes.find(n=>n.extras?.side==='left'&&n.extras?.group==='lid');assert.equal(customFrame.extras.frame_style,'cyberpunk');
  const frameMaterial=gltf.materials[gltf.meshes[customFrame.mesh].primitives[0].material];
  const linear=n=>{n/=255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4;};
  const expected=[173,118,86].map(linear);
  frameMaterial.pbrMetallicRoughness.baseColorFactor.slice(0,3).forEach((n,i)=>assert.ok(Math.abs(n-expected[i])<1e-5,'Highlight must not affect exported frame color'));
  const palettes=JSON.parse(fs.readFileSync(path.join(root,'design/frame-finishes.json')));
  for(const node of gltf.nodes.filter(n=>n.extras?.group==='lid')){
    const primitives=gltf.meshes[node.mesh].primitives,style=node.extras.frame_style;
    assert.equal(primitives.length,4,'Themed GLB retains four surface colors');
    for(const [i,role] of palettes.roles.entries()){
      const hex=role==='body'?config.frames[node.extras.side].color:palettes.styles[style].colors[role];
      const expected=[1,3,5].map(at=>linear(parseInt(hex.slice(at,at+2),16)));
      const actual=gltf.materials[primitives[i].material].pbrMetallicRoughness.baseColorFactor;
      expected.forEach((n,j)=>assert.ok(Math.abs(n-actual[j])<1e-5,'GLB '+style+' '+role+' color'));
    }
  }
  assert.equal(download.suggestedFilename(),'Filo36-revH-assembled.glb');
  function positionBytes(node){
    const primitive=gltf.meshes[node.mesh].primitives[0],a=gltf.accessors[primitive.attributes.POSITION],v=gltf.bufferViews[a.bufferView];
    assert.equal(a.componentType,5126);assert.equal(a.type,'VEC3');assert.ok(!v.byteStride||v.byteStride===12);
    const binStart=20+jsonLength+8,at=binStart+(v.byteOffset||0)+(a.byteOffset||0);
    return glb.subarray(at,at+a.count*12);
  }
  const capPath=scene.catalog.variants.find(v=>v.id===config.keycaps.left.K30.variant).path;
  assert.deepEqual(positionBytes(customCap),Buffer.from(scene.geometries[capPath].positions,'base64'),'GLB must contain selected cap vertices');
  assert.deepEqual(positionBytes(customFrame),Buffer.from(scene.geometries['mechanical/revH/left-frame-cyberpunk.stl'].positions,'base64'),'GLB must contain selected frame vertices');
  await page.click('#default-config');await page.keyboard.press('Escape');await page.click('#reset');
  assert.equal(hash(await page.locator('#canvas').screenshot({style:'.stage > :not(canvas),#leader-lines{opacity:0!important}'})),baseline,'Default config plus reset restores exact rendered assembly');
  await page.click('#part-keycaps');
  await page.selectOption('#key-target','all');
  assert.equal(await page.locator('#key-variant option[value="choc_stem_mx_size_normal"]').evaluate(o=>o.disabled),true);
  await page.click('[data-preset=saddle-sculpted]');assert.equal(await page.locator('#config-status').getAttribute('data-error'),'false');
  await page.click('#nav-files');await page.click('#default-config');
  // The entire directory remains visible while inspector bodies change/scroll.
  await page.click('#nav-view');await page.click('#stack');
  await page.locator('#part-mcu').hover();await checkLink(page,'mcu');
  await page.click('#nav-view');await page.selectOption('#view','front');
  await page.locator('#part-mcu').hover();await checkLink(page,'mcu');
  await page.click('#part-lid');await page.click('[data-style=handheld]');
  assert.equal(await page.locator('#layer-lid').isChecked(),true,'A frame click reveals a previously hidden cover');
  assert.equal(await page.locator('#explode').inputValue(),'0');
  await page.click('#frame-target [data-side=both]');await page.click('[data-style=tv]');
  assert.equal(await page.locator('#half').inputValue(),'both','Both target reveals both halves');
  await page.click('#reset');await page.locator('#part-lid').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#selection-title').textContent(),'Display frame');
  await checkDirectory(page);await checkLink(page,'lid');
  await page.screenshot({path:path.join(root,'build/viewer-sidebar/desktop-linked.png')});
  await page.evaluate(()=>document.querySelector('#inspector').scrollTop=10000);await checkDirectory(page);await checkLink(page,'lid');
  await page.click('#collapse-detail');await checkDirectory(page);await checkLink(page,'lid');
  assert.equal(await page.locator('#inspector').isVisible(),false);
  await page.click('#collapse-detail');await checkDirectory(page);await checkLink(page,'lid');
  await page.click('#annotations');assert.equal(await page.locator('#part-link').isVisible(),false);
  await page.click('#annotations');await checkLink(page,'lid');
  const pick=await page.locator('#part-link-dot').evaluate(el=>{const r=el.closest('main').getBoundingClientRect();return{x:r.x+Number(el.getAttribute('cx')),y:r.y+Number(el.getAttribute('cy'))};});
  await page.mouse.click(pick.x,pick.y);assert.equal(await page.locator('#selection-title').textContent(),'Display frame');
  assert.equal(await page.locator('#frame-target [data-side=left]').getAttribute('aria-pressed'),'true');
  await page.keyboard.press('Escape');
  const mobile=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true});
  if(offline)await mobile.route(/^https?:/,route=>{requests.push(route.request().url());return route.abort();});
  const phone=await mobile.newPage();phone.on('pageerror',e=>errors.push(e.message));await phone.goto(target);
  await phone.waitForFunction(()=>document.querySelector('#status').textContent.includes('168'));
  assert.equal(await phone.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'No horizontal overflow');
  await phone.locator('[data-style=handheld]').tap();
  assert.equal(await phone.locator('[data-style=handheld]').getAttribute('aria-pressed'),'true');
  assert.ok((await phone.locator('#canvas').boundingBox()).y>=0,'Model stays visible while browsing cards');
  await phone.locator('#part-lid').tap();await checkLink(phone,'lid');await checkDirectory(phone);
  assert.equal(await phone.locator('#selection-title').textContent(),'Display frame');
  assert.equal(await phone.locator('#frame-target [data-side=both]').getAttribute('aria-pressed'),'true');
  await phone.locator('#clear-selection').tap();
  await phone.locator('#nav-view').tap();
  await phone.locator('#inside').tap();assert.ok((await phone.locator('#status').textContent()).includes('components'));
  await phone.locator('#layer-display').uncheck();
  await phone.locator('#part-display').tap();
  await phone.waitForTimeout(120);assert.equal(await phone.locator('#part-link').isVisible(),false,'Hidden layers have no line');
  await phone.locator('#reset').tap();assert.equal(await phone.locator('#explode').inputValue(),'0');
  await phone.locator('#part-lid').tap();
  await checkDirectory(phone);await checkLink(phone,'lid');
  await phone.evaluate(()=>{document.querySelector('#inspector').scrollTop=0;scrollTo(0,0);});await phone.evaluate(()=>new Promise(requestAnimationFrame));
  await phone.screenshot({path:path.join(root,'build/viewer-mobile.png'),fullPage:true,animations:'disabled'});
  await phone.locator('#clear-selection').tap();
  // Actual touch events: a one-finger orbit and two-finger gesture must not select.
  const cdp=await mobile.newCDPSession(phone),rect=await phone.locator('#canvas').boundingBox();
  const cx=rect.x+rect.width*.5,cy=rect.y+rect.height*.48;
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:cx,y:cy,id:1}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:cx+35,y:cy+20,id:1}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  assert.equal(await phone.locator('#selection').isVisible(),false,'Touch orbit does not select');
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:cx-30,y:cy,id:1},{x:cx+30,y:cy,id:2}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:cx-45,y:cy+6,id:1},{x:cx+45,y:cy+6,id:2}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  assert.equal(await phone.locator('#selection').isVisible(),false,'Pinch/pan does not select');
  await phone.setViewportSize({width:320,height:568});await phone.locator('#reset').tap();
  assert.equal(await phone.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'No overflow at 320px');
  await phone.locator('[data-style=tv]').tap();await checkDirectory(phone);
  await phone.locator('#part-lid').tap();await checkLink(phone,'lid');
  await phone.locator('#collapse-detail').tap();await checkDirectory(phone);
  await phone.locator('#collapse-detail').tap();await checkDirectory(phone);
  const stage=await phone.locator('.stage').boundingBox();assert.ok(stage.y>=0&&stage.y+stage.height<568,'3D view stays visible at the smallest tested viewport');
  await phone.screenshot({path:path.join(root,'build/viewer-ux/mobile-small.png'),animations:'disabled'});
  await phone.setViewportSize({width:844,height:390});await checkDirectory(phone);
  // Capture the actual designs and readable palette cards, including mobile.
  fs.mkdirSync(path.join(root,'build/viewer-multicolor'),{recursive:true});
  await page.click('#reset');await page.click('#part-lid');await page.click('#frame-target [data-side=both]');
  for(const style of ['handheld','tv','cyberpunk']){
    await page.click(`[data-style=${style}]`);await page.mouse.move(10,100);
    assert.equal(await page.locator('#frame-color').inputValue(),palettes.styles[style].colors.body);
    await page.screenshot({path:path.join(root,`build/viewer-multicolor/${style}.png`)});
  }
  await page.locator('#frame-color').fill('#ad7656');await page.click('#theme-colors');
  assert.equal(await page.locator('#frame-color').inputValue(),palettes.styles.cyberpunk.colors.body);
  await page.locator('#frame-grid').screenshot({path:path.join(root,'build/viewer-multicolor/previews.png')});
  await phone.setViewportSize({width:390,height:844});await phone.locator('#reset').tap();await phone.locator('#part-lid').tap();await phone.locator('[data-style=cyberpunk]').tap();
  await phone.evaluate(()=>document.querySelector('#inspector').scrollTop=0);await checkDirectory(phone);
  await phone.screenshot({path:path.join(root,'build/viewer-multicolor/mobile.png')});
  assert.deepEqual(errors,[]);if(offline)assert.deepEqual(requests,[],'Offline viewer must not request network resources');
  const receipt={viewer_sha256:hash(Buffer.from(html)),target:offline?'local file with all HTTP(S) requests blocked':'public URL',
    browser:await browser.version(),desktop:true,narrow_viewport_emulation:true,physical_phone_tested:false,public_embedded_scene_matches_current:!offline,
    all_12_layer_filters:true,half_filters:true,orbit_drag:true,bottom_view:true,full_reset_pixel_identical:true,
    persistent_component_directory:true,sidebar_line_endpoints:true,directory_visible_during_scroll_and_collapse:true,keyboard_component_selection:true,direct_canvas_picking:true,labels_follow_camera:true,frame_click_reveals_hidden_cover:true,annotation_toggle:true,orbit_does_not_select:true,touch_orbit_and_pinch_do_not_select:true,small_320px_viewport:true,
    six_preview_cards:true,multicolor_glb_roles:true,one_click_frames:true,keyboard_frame_activation:true,mixed_style_and_color_state:true,theme_applies_palette_and_body_overrides_roundtrip:true,sidebar_hover_highlight:true,sidebar_opens_frame_explorer:true,touch_frame_cards_and_sidebar:true,hidden_layer_links_removed:true,highlight_excluded_from_glb:true,
    keycap_variant_selection:true,frame_style_and_color:true,three_distinct_themed_geometries:true,json_roundtrip:true,invalid_combination_rejected:true,glb_matches_custom_configuration:true,glb_selected_vertices_exact:true,glb_objects:168,glb_keycaps:36,glb_units:'metres',runtime_errors:errors,offline_network_requests:requests.length};
  fs.writeFileSync(path.join(root,'build/viewer-ui-check.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt,null,2));await mobile.close();await context.close();
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
