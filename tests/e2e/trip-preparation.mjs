// Disposable fixture only. Images and tiles are explicitly synthetic; no real photo/location is uploaded.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const BASE=process.env.BASE_URL??'http://localhost:8060';
const shots=process.env.SHOTS??'/tmp/holdover-trip-feature-shots';await fs.mkdir(shots,{recursive:true});
const b=await chromium.launch({executablePath:process.env.CHROMIUM,args:['--no-sandbox','--use-gl=swiftshader','--enable-unsafe-swiftshader']});
let checks=0;const ok=(v,m)=>{assert.ok(v,m);console.log('PASS '+m);checks++;};
const nav=(p,name)=>p.getByRole('button',{name,exact:true}).first().click();
const table=async(p,name)=>p.evaluate(name=>new Promise((resolve,reject)=>{const r=indexedDB.open('holdover');r.onsuccess=()=>{const d=r.result,q=d.transaction(name).objectStore(name).getAll();q.onsuccess=()=>{resolve(q.result);d.close();};q.onerror=()=>reject(q.error);};}),name);
const inspect=async(p,name,wanted=null)=>p.evaluate(({name,wanted})=>new Promise(resolve=>{const r=indexedDB.open('holdover');r.onsuccess=()=>{const d=r.result,q=d.transaction(name).objectStore(name).getAll();q.onsuccess=async()=>{const row=q.result.find(x=>x.photo_blob&&(!wanted||x.name===wanted));d.close();if(!row)return resolve(null);const img=await createImageBitmap(row.photo_blob);const c=document.createElement('canvas');c.width=img.width;c.height=img.height;const g=c.getContext('2d');g.drawImage(img,0,0);const top=[...g.getImageData(Math.floor(img.width/2),20,1,1).data],bottom=[...g.getImageData(Math.floor(img.width/2),img.height-20,1,1).data];resolve({width:img.width,height:img.height,size:row.photo_blob.size,type:row.photo_blob.type,top,bottom});};};}),{name,wanted});
try{
 const ctx=await b.newContext({viewport:{width:1440,height:900}}),p=await ctx.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto(BASE);await p.evaluate(async()=>{await navigator.serviceWorker.ready;});await p.reload();
 const list=p.getByRole('region',{name:'Explore waters',exact:true});
 await list.getByRole('searchbox',{name:'Search all waters'}).fill('Malheur River');await list.getByRole('button',{name:/Malheur River/}).click();await p.getByRole('heading',{name:'Malheur River',exact:true}).waitFor();
 await p.getByRole('button',{name:'Add Malheur River to favorites',exact:true}).click();
 await p.getByRole('button',{name:'Prepare for offline',exact:true}).first().click();
 const dialog=p.getByRole('dialog',{name:'Prepare for offline',exact:true});
 await dialog.getByLabel('Area to save',{exact:true}).selectOption('trip');
 await dialog.getByLabel('Trip waterbody',{exact:true}).selectOption({label:'Malheur River'});
 await dialog.getByLabel('Area around the pin',{exact:true}).selectOption('5');await dialog.getByLabel('Map detail',{exact:true}).selectOption('8');
 ok(await dialog.getByText(/additional storage/).isVisible(),'trip preview shows tile/storage estimate outside Willamette');
 await dialog.getByLabel('Trip fishery',{exact:true}).selectOption('steelhead');
 await dialog.getByRole('button',{name:'Save for offline',exact:true}).click();await dialog.getByRole('status').filter({hasText:/Saved/}).waitFor({timeout:60000});
 ok(!/Could not finish|stopped/.test(await dialog.textContent()),'trip area and exact-date conditions save successfully');
 const tiles=await table(p,'tiles');ok(tiles.some(t=>t.key.startsWith('8/44/')),'actual saved eastern-Oregon tiles differ from old Willamette rectangle');
 ok(await p.evaluate(()=>new Promise(resolve=>{const r=indexedDB.open('holdover');r.onsuccess=()=>{const d=r.result,q=d.transaction('days').objectStore('days').getAll();q.onsuccess=()=>{resolve(q.result.length===3&&q.result.every(row=>row.fishery==='steelhead'));d.close();};};})),'three exact trip days and chosen fishery cached in IndexedDB');
 await dialog.getByRole('button',{name:'Close',exact:true}).click();await p.getByRole('button',{name:'Close details',exact:true}).click();
 await list.getByRole('searchbox',{name:'Search all waters'}).fill('');await list.getByRole('button',{name:'Favorites',exact:true}).click();
 await p.getByRole('article',{name:'Malheur River',exact:true}).getByText('Your recent trips',{exact:true}).waitFor();
 // JPEG pixels: left red/right blue. EXIF 6 rotates them clockwise (top red/bottom blue).
 const jpeg=Buffer.from(await p.evaluate(()=>{const c=document.createElement('canvas');c.width=3000;c.height=2000;const g=c.getContext('2d');g.fillStyle='red';g.fillRect(0,0,1500,2000);g.fillStyle='blue';g.fillRect(1500,0,1500,2000);return c.toDataURL('image/jpeg',.95).split(',')[1];}),'base64');
 const exif=Buffer.from([0xff,0xe1,0,34,69,120,105,102,0,0,73,73,42,0,8,0,0,0,1,0,18,1,3,0,1,0,0,0,6,0,0,0,0,0,0,0]);
 const file={name:'synthetic-oriented.jpg',mimeType:'image/jpeg',buffer:Buffer.concat([jpeg.subarray(0,2),exif,jpeg.subarray(2)])};
 await ctx.setOffline(true);await p.evaluate(()=>dispatchEvent(new Event('offline')));
 await nav(p,'Gear');await p.getByRole('button',{name:'Add gear',exact:true}).click();await p.getByLabel('Name',{exact:true}).fill('Orientation test lure');await p.getByLabel('Photo (optional)',{exact:true}).setInputFiles(file);await p.getByRole('button',{name:'Add to my gear',exact:true}).click();await p.getByRole('region',{name:'Add gear',exact:true}).waitFor({state:'hidden'});
 const gear=await inspect(p,'gear');ok(gear.width===1067&&gear.height===1600&&gear.top[0]>200&&gear.bottom[2]>200,'gear photo is resized with EXIF orientation baked into pixels offline');
 ok(gear.size<file.buffer.length,'prepared gear photo uses fewer bytes');
 const png=Buffer.from(await p.evaluate(()=>{const c=document.createElement('canvas');c.width=80;c.height=60;const g=c.getContext('2d');g.fillStyle='rgba(0,0,255,.5)';g.fillRect(0,0,80,60);return c.toDataURL('image/png').split(',')[1];}),'base64');
 await p.getByRole('button',{name:'Add gear',exact:true}).click();await p.getByLabel('Name',{exact:true}).fill('Transparent test lure');await p.getByLabel('Photo (optional)',{exact:true}).setInputFiles({name:'synthetic-alpha.png',mimeType:'image/png',buffer:png});await p.getByRole('button',{name:'Add to my gear',exact:true}).click();await p.getByRole('region',{name:'Add gear',exact:true}).waitFor({state:'hidden'});
 const alpha=await inspect(p,'gear','Transparent test lure');ok(alpha.width===80&&alpha.height===60&&alpha.top[3]>=125&&alpha.top[3]<=130,'small transparent photos retain alpha without enlargement');
 await p.getByRole('button',{name:'Add gear',exact:true}).click();await p.getByLabel('Name',{exact:true}).fill('Broken photo lure');await p.getByLabel('Photo (optional)',{exact:true}).setInputFiles({name:'invalid.jpg',mimeType:'image/jpeg',buffer:Buffer.from('not a JPEG')});await p.getByRole('button',{name:'Add to my gear',exact:true}).click();await p.getByRole('alert').filter({hasText:/photo could not be read/}).waitFor();ok(!(await table(p,'gear')).some(g=>g.name==='Broken photo lure'),'unreadable photo leaves the form intact and writes no partial gear row');await p.getByRole('button',{name:'Close',exact:true}).click();

 await nav(p,'Journal');await p.getByRole('button',{name:/Log (a|your first) trip/}).first().click();await p.getByLabel('Where',{exact:true}).selectOption({label:'Malheur River'});await p.getByLabel('Species 1',{exact:true}).fill('rainbow trout');await p.getByRole('button',{name:/More/}).first().click();await p.locator('input[type=file]').setInputFiles(file);await p.getByRole('button',{name:'Save trip',exact:true}).click();await p.locator('li.card').first().waitFor();
 const photo=await inspect(p,'catches');ok(photo.width===1067&&photo.height===1600&&photo.top[0]>200&&photo.bottom[2]>200,'journal photo uses the same orientation-preserving offline resize path');
 await nav(p,'Map');await list.getByRole('button',{name:'Favorites',exact:true}).click();
 const favorite=p.getByRole('article',{name:'Malheur River',exact:true});await favorite.getByText(/1 fish/).waitFor();ok(await favorite.getByText(/Waiting to sync/).isVisible(),'Favorites reflects a newly logged offline trip from this device');
 await p.reload();const explore=p.getByRole('region',{name:'Explore waters',exact:true});await p.getByRole('button',{name:'Show Explore waters',exact:true}).count().then(async n=>{if(n)await p.getByRole('button',{name:'Show Explore waters',exact:true}).click();});await explore.getByRole('button',{name:'Favorites',exact:true}).click();await p.getByRole('article',{name:'Malheur River',exact:true}).getByText(/1 fish/).waitFor();ok(true,'Favorites dashboard and personal trip history survive airplane-mode reload');await p.getByRole('button',{name:'Refresh favorites',exact:true}).click();await p.getByRole('article',{name:'Malheur River',exact:true}).getByText(/1 fish/).waitFor();ok(true,'Favorites refresh works against the offline public cache');
 const gearId=(await table(p,'gear')).find(g=>g.name==='Orientation test lure').uuid,catchId=(await table(p,'catches')).find(c=>c.photo_blob).uuid;
 await ctx.setOffline(false);await nav(p,'Settings');await p.getByLabel('Username',{exact:true}).fill('boss');await p.getByLabel('Password',{exact:true}).fill('correct-horse-battery');await p.getByRole('button',{name:'Sign in',exact:true}).click();await p.getByRole('button',{name:'Sign out',exact:true}).waitFor();
 let synced;
 for(let i=0;i<120;i++){
  synced=await p.evaluate(()=>fetch('/api/sync/pull').then(r=>r.json()));
  if(synced.gear.some(g=>g.uuid===gearId&&g.photo_path)&&synced.catches.some(c=>c.uuid===catchId&&c.photo_path))break;
  await p.waitForTimeout(250);
 }
 const paths=[synced.gear.find(g=>g.uuid===gearId)?.photo_path,synced.catches.find(c=>c.uuid===catchId)?.photo_path];ok(paths.every(Boolean),'both resized offline photos upload after sign-in/reconnect');
 const other=await b.newContext();const q=await other.newPage();await q.goto(BASE);await q.evaluate(()=>fetch('/api/auth/login',{method:'POST',headers:{'X-Holdover':'1','Content-Type':'application/json'},body:JSON.stringify({username:'sam',password:'sams-long-password'})}));for(const path of paths)ok(await (await q.request.get(new URL('/api/journal/photo/'+path,BASE).href)).status()===404,'another account cannot read resized photo');
 await q.reload();await nav(q,'Map');const otherExplore=q.getByRole('region',{name:'Explore waters',exact:true});await otherExplore.getByRole('button',{name:'Favorites',exact:true}).click();ok(await q.getByRole('article',{name:'Malheur River',exact:true}).count()===0,'other account does not inherit favorite dashboard/trips');
 await p.getByRole('button',{name:'Sign out',exact:true}).click();await p.getByLabel('Username',{exact:true}).fill('sam');await p.getByLabel('Password',{exact:true}).fill('sams-long-password');await p.getByRole('button',{name:'Sign in',exact:true}).click();await p.getByRole('button',{name:'Sign out',exact:true}).waitFor();
 ok((await table(p,'trips')).length===0,'same-device account switch clears the previous owner personal trips');
 await nav(p,'Map');await p.getByRole('region',{name:'Explore waters',exact:true}).getByRole('searchbox',{name:'Search all waters'}).fill('Malheur River');await p.getByRole('button',{name:/Malheur River river/}).click();await p.getByRole('button',{name:'Add Malheur River to favorites',exact:true}).click();await p.getByRole('button',{name:'Close details',exact:true}).click();await p.getByRole('region',{name:'Explore waters',exact:true}).getByRole('searchbox',{name:'Search all waters'}).fill('');await p.getByRole('region',{name:'Explore waters',exact:true}).getByRole('button',{name:'Favorites',exact:true}).click();await p.getByRole('article',{name:'Malheur River',exact:true}).getByText(/No trips logged here/).waitFor();ok(true,'same-device Favorites never displays the previous account history');
 await p.getByRole('article',{name:'Malheur River',exact:true}).getByRole('button',{name:'Malheur River',exact:true}).click();await p.getByRole('button',{name:'Remove Malheur River from favorites',exact:true}).click();
 ok(errors.length===0,'no browser errors in trip preparation/photo/Favorites flow');await other.close();await ctx.close();
 console.log(`${checks} trip preparation feature checks passed`);
}finally{await b.close();}
