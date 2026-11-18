from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
html_path = root / "app/src/main/assets/index.html"
s = html_path.read_text(encoding="utf-8")
if "NUTRITRACK_4_0_COMPLETE" in s:
    print("NutriTrack 4.0 already applied")
    raise SystemExit(0)

# A safe, versioned IndexedDB mirror. Existing localStorage remains the immediate
# compatibility layer; IndexedDB is seeded from it and can recover it if it is absent.
code = r"""
/* NUTRITRACK_4_0_COMPLETE */
(function(){
 "use strict";
 const DB_NAME="nutritrack_v4", DB_VERSION=1, STORE="snapshots", SNAP="primary";
 let db=null, writeQueue=Promise.resolve(), restoredFromIndexedDB=false, localStorageWriteFailed=false;
 const storageStatus={mode:"localStorage+IndexedDB",ready:false,lastSaved:null,error:null};
 function openStore(){
  return new Promise((resolve,reject)=>{
   if(!("indexedDB" in window)){reject(new Error("IndexedDB unavailable"));return}
   const req=indexedDB.open(DB_NAME,DB_VERSION);
   req.onupgradeneeded=()=>{const d=req.result;if(!d.objectStoreNames.contains(STORE))d.createObjectStore(STORE,{keyPath:"id"})};
   req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error||new Error("IndexedDB open failed"));
  });
 }
 function readSnapshot(){
  return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,"readonly"),req=tx.objectStore(STORE).get(SNAP);req.onsuccess=()=>resolve(req.result||null);req.onerror=()=>reject(req.error||new Error("IndexedDB read failed"))});
 }
 function writeSnapshot(snapshot){
  return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,"readwrite");tx.objectStore(STORE).put(snapshot);tx.oncomplete=()=>resolve(true);tx.onerror=()=>reject(tx.error||new Error("IndexedDB write failed"));tx.onabort=()=>reject(tx.error||new Error("IndexedDB write aborted"))});
 }
 function cloneState(){return JSON.parse(JSON.stringify(state))}
 function mirrorState(){
  if(!db)return;
  const snapshot={id:SNAP,schemaVersion:4,updatedAt:Date.now(),data:cloneState()};
  writeQueue=writeQueue.then(()=>writeSnapshot(snapshot)).then(()=>{
   storageStatus.lastSaved=snapshot.updatedAt;storageStatus.error=null;
   if(localStorageWriteFailed){try{localStorage.removeItem(DBKEY);localStorageWriteFailed=false}catch(e){storageStatus.error="IndexedDB saved, but the old local copy could not be cleared"}}
  }).catch(e=>{storageStatus.error=String(e&&e.message||e)});
 }
 const originalSave=save;
 save=function(){
  if(db&&storageStatus.ready){
   try{localStorage.setItem(DBKEY,JSON.stringify(state));localStorageWriteFailed=false}catch(e){localStorageWriteFailed=true}
   mirrorState();
   return true;
  }
  const ok=originalSave();
  if(ok)mirrorState();
  return ok;
 };
 async function initialize(){
  try{
   db=await openStore();
   const localRaw=localStorage.getItem(DBKEY);
   const stored=await readSnapshot();
   if(localRaw===null && stored && stored.schemaVersion===4 && stored.data && Array.isArray(stored.data.entries)){
    state={...defaults,...stored.data,targets:{...defaults.targets,...(stored.data.targets||{})}};
    originalSave();
    restoredFromIndexedDB=true;
    if(typeof renderHome==="function")renderHome();
    if(typeof renderProgress==="function")renderProgress();
    if(typeof renderSettings==="function")renderSettings();
    toast("Recovered your latest local data from the on-device recovery database.");
   }else{
    // The installed 3.1 local database wins during first migration. Never overwrite
    // existing diary data with a possibly stale IndexedDB snapshot.
    await writeSnapshot({id:SNAP,schemaVersion:4,updatedAt:Date.now(),data:cloneState()});
   }
   storageStatus.mode="IndexedDB primary + local fallback";
   storageStatus.ready=true;
  }catch(e){storageStatus.error=String(e&&e.message||e);storageStatus.mode="localStorage fallback"}
 }
 initialize();
 window.NutriTrackStorage={status:()=>({...storageStatus}),flush:()=>writeQueue,restoreFromIndexedDB:async function(){if(!db)throw new Error("IndexedDB is not ready");const x=await readSnapshot();if(!x||!x.data)throw new Error("No recovery snapshot found");state={...defaults,...x.data,targets:{...defaults.targets,...(x.data.targets||{})}};if(!originalSave())throw new Error("Could not restore recovered data to local storage");if(typeof renderHome==="function")renderHome();if(typeof renderProgress==="function")renderProgress();return true}};
 // Versioned backup envelope; import still accepts legacy 3.1 plain-state backups.
 const backupButton=el("backup");
 if(backupButton)backupButton.onclick=()=>download("nutritrack-backup-v4-"+dateISO()+".json",JSON.stringify({app:"NutriTrack",schemaVersion:4,exportedAt:new Date().toISOString(),data:state},null,2),"application/json");
 const restoreInput=el("restoreFile");
 if(restoreInput)restoreInput.onchange=async e=>{
  try{
   const file=e.target.files&&e.target.files[0];if(!file)return;
   const parsed=JSON.parse(await file.text());
   const payload=parsed&&parsed.app==="NutriTrack"&&parsed.data?parsed.data:parsed;
   if(typeof validateBackup!=="function")throw new Error("Backup validator unavailable");
   const validated=validateBackup(payload),previous=state;
   state=validated;
   if(!save()){state=previous;throw new Error("Could not persist restored data")}
   if(typeof renderHome==="function")renderHome();
   if(typeof renderSettings==="function")renderSettings();
   if(typeof renderProgress==="function")renderProgress();
   toast("Backup validated and restored.");
   go("home");
  }catch(err){toast("Backup restore failed: "+String(err&&err.message||"invalid file"))}
  finally{e.target.value=""}
 };
 // Search index: normalize Arabic marks/tatweel and rank exact/prefix matches first.
 const normalizeFoodText=v=>String(v||"").toLocaleLowerCase().normalize("NFD").replace(/[\u064B-\u065F\u0670\u0640]/g,"").replace(/[\u0300-\u036f]/g,"").trim();
 searchFoods=function(q){
  const query=normalizeFoodText(q);if(!query)return [];
  const terms=query.split(/\s+/).filter(Boolean);
  return allFoods().map((f,i)=>{
   const name=normalizeFoodText(f.name),ar=normalizeFoodText(f.ar),barcode=normalizeFoodText(f.barcode);
   const hay=name+" "+ar+" "+barcode;
   const matches=terms.every(t=>hay.includes(t));if(!matches)return null;
   const rank=(name===query?0:name.startsWith(query)?1:ar.startsWith(query)?2:barcode===query?0:3);
   return {f,i,rank};
  }).filter(Boolean).sort((a,b)=>a.rank-b.rank||a.f.name.localeCompare(b.f.name)).slice(0,12).map(x=>x.f);
 };
 // Add a useful 30-day nutrition trend and adherence summary without replacing
 // the existing weekly and weight views.
 const priorRenderProgress=renderProgress;
 renderProgress=function(){
  priorRenderProgress();
  let card=el("ntMonthlyInsights");
  if(!card){card=document.createElement("div");card.id="ntMonthlyInsights";card.className="card";el("progress").appendChild(card)}
  const today=new Date(),days=[];
  for(let i=29;i>=0;i--){const d=new Date(today);d.setDate(d.getDate()-i);const key=dateISO(d),rows=dayEntries(key),t=totals(rows);days.push({key,kcal:t.kcal,protein:t.protein,fat:t.fat,carbs:t.carbs,logged:rows.length>0})}
  const logged=days.filter(x=>x.logged),sum=logged.reduce((a,x)=>a+x.kcal,0),avg=logged.length?sum/logged.length:0;
  const target=num(state.targets.kcal),onTarget=logged.filter(x=>x.kcal<=target*1.1&&x.kcal>=target*.8).length;
  const max=Math.max(target,...days.map(x=>x.kcal),1);
  const bars=days.map((x,i)=>'<div title="'+x.key+': '+Math.round(x.kcal)+' kcal" style="flex:1;min-width:3px;height:'+Math.max(3,Math.round(x.kcal/max*92))+'px;background:'+(x.logged?"var(--green)":"var(--line)")+';border-radius:3px 3px 0 0;opacity:'+(x.logged?1:.45)+'"></div>').join("");
  card.innerHTML='<h2>Last 30 days</h2><div class="statgrid"><div class="stat"><b>'+Math.round(avg)+'</b><small>Average kcal / logged day</small></div><div class="stat"><b>'+logged.length+'/30</b><small>Days tracked</small></div><div class="stat"><b>'+ (logged.length?Math.round(onTarget/logged.length*100):0)+'%</b><small>Days near calorie target</small></div></div><div style="height:104px;display:flex;align-items:flex-end;gap:3px;margin:14px 0 6px">'+bars+'</div><div class="tiny muted">Daily calories · last 30 days</div><div class="meal" style="margin-top:12px"><b>Macro totals · logged days</b><div class="plan-row"><span>Protein</span><b>'+Math.round(logged.reduce((a,x)=>a+x.protein,0))+' g</b></div><div class="plan-row"><span>Carbohydrates</span><b>'+Math.round(logged.reduce((a,x)=>a+x.carbs,0))+' g</b></div><div class="plan-row"><span>Fat</span><b>'+Math.round(logged.reduce((a,x)=>a+x.fat,0))+' g</b></div></div>';
 };
 // Show storage/migration status in settings without exposing internal data.
 const settings=document.getElementById("settings");
 if(settings){
  const box=document.createElement("div");box.className="card";box.id="ntStorageStatus";
  box.innerHTML='<h2>Data protection</h2><p class="small muted">Your existing diary is preserved. NutriTrack now uses a versioned IndexedDB store with a compatible local fallback.</p><div class="tiny" id="ntStorageState">Checking local database…</div>';
  const backup=el("backup");if(backup&&backup.parentElement&&backup.parentElement.parentElement)backup.parentElement.parentElement.insertAdjacentElement("afterend",box);else settings.appendChild(box);
  const updateStatus=()=>{const st=storageStatus;const node=el("ntStorageState");if(node)node.textContent=st.ready?"IndexedDB ready · local fallback available"+(st.lastSaved?" · last mirrored "+new Date(st.lastSaved).toLocaleString():""):(st.error?"Using compatible local storage · "+st.error:"Preparing recovery database…")};
  setTimeout(updateStatus,1000);setTimeout(updateStatus,4000);
 }
})();
"""
if "</script>" not in s:
    raise SystemExit("Inline script closing tag missing")
idx=s.rfind("</script>")
s=s[:idx]+code+"\n"+s[idx:]
html_path.write_text(s,encoding="utf-8")

# Update native and PWA version metadata.
gradle=root/"app/build.gradle"
g=gradle.read_text(encoding="utf-8")
if "versionCode 13" not in g or "versionName '3.1.0'" not in g:
    raise SystemExit("Expected 3.1.0 / code 13 baseline not found")
g=g.replace("versionCode 13","versionCode 14",1).replace("versionName '3.1.0'","versionName '4.0.0'",1)
gradle.write_text(g,encoding="utf-8")
manifest=root/"app/src/main/assets/manifest.webmanifest"
m=manifest.read_text(encoding="utf-8")
if "NutriTrack 3.1" not in m:
    raise SystemExit("Expected PWA 3.1 manifest marker not found")
manifest.write_text(m.replace("NutriTrack 3.1","NutriTrack 4.0",1),encoding="utf-8")
print("Applied NutriTrack 4.0 storage migration, versioned backups, search and monthly insights")
