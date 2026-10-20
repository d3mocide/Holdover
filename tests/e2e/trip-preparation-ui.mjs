// All-theme UI gate on disposable synthetic map fixtures; local journal rows are explicitly synthetic.
import {chromium} from 'playwright-core';import assert from 'node:assert/strict';import fs from 'node:fs/promises';
const BASE=process.env.BASE_URL??'http://localhost:8060',shots=process.env.SHOTS??'/tmp/holdover-trip-ui-shots';await fs.mkdir(shots,{recursive:true});const axe=await fs.readFile('node_modules/axe-core/axe.min.js','utf8');
const b=await chromium.launch({executablePath:process.env.CHROMIUM,args:['--no-sandbox','--use-gl=swiftshader','--enable-unsafe-swiftshader']});let checks=0;
const ok=(v,m)=>{assert.ok(v,m);console.log('PASS '+m);checks++;};
try{for(const[size,width,height]of[['phone',393,852],['tablet',768,1024],['desktop',1440,900]]){
 if(process.env.SIZE && process.env.SIZE!==size)continue;
 const ctx=await b.newContext({viewport:{width,height},serviceWorkers:'block'}),p=await ctx.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));await p.route('**/api/day/**',async route=>{const url=new URL(route.request().url());url.searchParams.set('refresh','false');const res=await route.fetch({url:url.href});await route.fulfill({response:res});});await p.goto(BASE);
 const nav=name=>p.getByRole('button',{name,exact:true}).first().click();
 const scan=async(label)=>{await p.evaluate(axe);assert.deepEqual(await p.evaluate(async()=>(await axe.run()).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))),[]);ok(true,`${size}/${label}: axe clean`);await p.screenshot({path:`${shots}/${size}-${label}.png`});};
 for(const[theme,label]of[['fir','Fir & Steelhead'],['redband','Redband'],['nightbite','Night Bite']]){
  await nav('Settings');await p.getByRole('radio',{name:label,exact:true}).check();await nav('Map');
  const explore=p.getByRole('region',{name:'Explore waters',exact:true});if(await p.getByRole('button',{name:'Show Explore waters',exact:true}).count())await p.getByRole('button',{name:'Show Explore waters',exact:true}).click();
  await explore.getByRole('button',{name:'Rivers',exact:true}).click();await explore.getByRole('button',{name:/Tualatin River/}).click();await p.getByRole('heading',{name:'Tualatin River',exact:true}).waitFor();
  const star=p.getByRole('button',{name:'Add Tualatin River to favorites',exact:true});if(await star.count())await star.click();
  await p.getByRole('button',{name:'Close details',exact:true}).click();await explore.getByRole('button',{name:'Favorites',exact:true}).click();
  const card=p.getByRole('article',{name:'Tualatin River',exact:true});await card.getByText('Your recent trips',{exact:true}).waitFor();
  ok(await card.getByText(/No trips logged here/).isVisible(),`${theme}/${size}: favorite shows honest personal-history empty state`);await scan(`${theme}-favorites`);
  await p.getByRole('button',{name:'Hide Explore waters',exact:true}).click();
  await p.getByRole('button',{name:'Prepare for offline',exact:true}).first().click();const dlg=p.getByRole('dialog',{name:'Prepare for offline',exact:true});
  await dlg.getByLabel('Area to save',{exact:true}).selectOption('zone');await dlg.getByLabel('Zone',{exact:true}).selectOption('central');
  await dlg.getByText(/additional storage/).waitFor();ok(/Estimate uses 20 KB/.test(await dlg.textContent()),`${theme}/${size}: selected zone has bounded count and labelled storage estimate`);await scan(`${theme}-offline-zone`);
  await dlg.getByLabel('Area to save',{exact:true}).selectOption('trip');await dlg.getByLabel('Trip waterbody',{exact:true}).selectOption({label:'Malheur River'});await dlg.getByLabel('Area around the pin',{exact:true}).selectOption('5');await dlg.getByLabel('Map detail',{exact:true}).selectOption('8');await dlg.getByText(/additional storage/).waitFor();
  ok((await dlg.getByLabel('Map detail',{exact:true}).locator('option').allTextContents()).every(t=>!t.includes('Zoom 12')),`${theme}/${size}: unsupported map detail is not offered`);await scan(`${theme}-offline-trip`);
  if(theme==='fir'&&size==='desktop'){
   await p.route('**/api/spots?**',async route=>{await new Promise(r=>setTimeout(r,700));await route.continue();});
   await dlg.getByRole('button',{name:'Save for offline',exact:true}).click();await dlg.getByRole('button',{name:'Stop',exact:true}).click();await dlg.getByRole('status').filter({hasText:/Stopped/}).waitFor({timeout:10000});ok(true,'cancelled download reports stop and keeps saved work');await p.unroute('**/api/spots?**');
   await dlg.getByRole('button',{name:'Save for offline',exact:true}).click();await dlg.getByRole('status').filter({hasText:/Saved/}).waitFor({timeout:30000});ok(!/Could not finish/.test(await dlg.textContent()),'download can resume after cancellation');
   await dlg.getByRole('button',{name:'Save for offline',exact:true}).click();await dlg.getByRole('status').filter({hasText:/Saved/}).waitFor({timeout:30000});ok(/0 new map tiles/.test(await dlg.textContent()),'repeat preparation reuses saved map tiles');
   await dlg.getByLabel('Area around the pin',{exact:true}).selectOption('15');
   await p.evaluate(()=>{window.originalTilePut=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(...args){if(this.name==='tiles')throw new DOMException('Synthetic full storage','QuotaExceededError');return window.originalTilePut.apply(this,args);};});
   await dlg.getByRole('button',{name:'Save for offline',exact:true}).click();await dlg.getByRole('status').filter({hasText:/storage full/}).waitFor({timeout:30000});ok(/saved tiles are retained/.test(await dlg.textContent()),'quota failure is reported without discarding saved tiles');await p.evaluate(()=>{IDBObjectStore.prototype.put=window.originalTilePut;delete window.originalTilePut;});

  }
  await dlg.getByRole('button',{name:'Close',exact:true}).click();
  if(theme==='fir'&&size==='desktop'){
   await p.evaluate(()=>{window.originalEstimate=navigator.storage.estimate;Object.defineProperty(navigator.storage,'estimate',{value:async()=>({usage:0,quota:1}),configurable:true});});
   await p.getByRole('button',{name:'Prepare for offline',exact:true}).first().click();await dlg.getByRole('alert').filter({hasText:/estimate exceeds available storage/}).waitFor();ok(await dlg.getByRole('button',{name:'Save for offline',exact:true}).isDisabled(),'preview blocks a download estimated larger than available storage');await dlg.getByRole('button',{name:'Close',exact:true}).click();await p.evaluate(()=>{Object.defineProperty(navigator.storage,'estimate',{value:window.originalEstimate,configurable:true});delete window.originalEstimate;});
  }
  // Day view passes its selected date into the preparation dialog.
  await p.getByRole('button',{name:'Show Explore waters',exact:true}).click();await card.getByRole('button',{name:'Tualatin River',exact:true}).click();await p.getByRole('button',{name:'Plan the day',exact:true}).click();await p.getByRole('button',{name:'Tomorrow',exact:true}).click();await p.getByRole('button',{name:'Prepare for offline',exact:true}).last().click();
  const expected=await p.evaluate(()=>{const d=new Date();d.setDate(d.getDate()+1);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10);});ok(await dlg.getByLabel('Trip date',{exact:true}).inputValue()===expected,`${theme}/${size}: trip preparation keeps selected plan date`);await dlg.getByRole('button',{name:'Close',exact:true}).click();await p.getByRole('button',{name:'Back',exact:true}).click();await p.getByRole('button',{name:'Close details',exact:true}).click();
  await nav('Gear');await p.getByRole('button',{name:'Add gear',exact:true}).click();ok(await p.getByText(/Photos are resized on this device/).isVisible(),`${theme}/${size}: photo resizing is explained before save`);await scan(`${theme}-gear-photo`);await p.getByRole('button',{name:'Close',exact:true}).click();
 }
 await p.screenshot({path:`${shots}/${size}-final.png`});
 // Map canvas and panel widths settle after the existing navigation transition.
 await p.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth,{},{timeout:2000});
 ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${size}: no page overflow`);ok(errors.length===0,`${size}: no browser errors`);await ctx.close();
}console.log(`${checks} trip preparation UI checks passed`);}finally{await b.close();}
