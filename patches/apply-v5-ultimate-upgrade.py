from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
html_path = root / "app/src/main/assets/index.html"
s = html_path.read_text(encoding="utf-8")
if "NUTRITRACK_5_0_ULTIMATE" in s:
    print("NutriTrack 5.0 already applied")
    raise SystemExit(0)

code = r"""
/* NUTRITRACK_5_0_ULTIMATE */
(function(){
 "use strict";
 if(window.__NUTRITRACK_5_0_ULTIMATE__)return;
 window.__NUTRITRACK_5_0_ULTIMATE__=true;
 const $=id=>document.getElementById(id);
 const safeNum=v=>{const n=Number(v);return Number.isFinite(n)&&n>=0?n:0};
 const fmt=v=>Math.round(v).toLocaleString();
 function getWeek(){
  const now=new Date(),days=[];
  for(let i=6;i>=0;i--){
   const d=new Date(now);d.setHours(12,0,0,0);d.setDate(d.getDate()-i);
   const key=dateISO(d),rows=dayEntries(key),t=totals(rows);
   days.push({key,label:d.toLocaleDateString(undefined,{weekday:"short"}),kcal:safeNum(t.kcal),protein:safeNum(t.protein),fat:safeNum(t.fat),carbs:safeNum(t.carbs),logged:rows.length>0});
  }
  return days;
 }
 function renderWeek(){
  const host=$("progress");if(!host||!Array.isArray(state.entries))return;
  let card=$("ntWeeklyInsights");
  if(!card){card=document.createElement("section");card.id="ntWeeklyInsights";card.className="card";const monthly=$("ntMonthlyInsights");if(monthly&&monthly.parentElement===host)monthly.insertAdjacentElement("afterend",card);else host.appendChild(card)}
  const days=getWeek(),logged=days.filter(x=>x.logged),sum=logged.reduce((a,x)=>a+x.kcal,0),protein=logged.reduce((a,x)=>a+x.protein,0),target=safeNum(state.targets&&state.targets.kcal),max=Math.max(target,...days.map(x=>x.kcal),1);
  const bars=days.map(x=>'<div title="'+x.key+': '+fmt(x.kcal)+' kcal" style="flex:1;min-width:0;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:118px;gap:5px"><div style="width:100%;height:'+Math.max(3,Math.round(x.kcal/max*88))+'px;background:'+(x.logged?'var(--green)':'var(--line)')+';border-radius:5px 5px 2px 2px;opacity:'+(x.logged?'1':'.35')+'"></div><small class="tiny muted">'+x.label+'</small></div>').join("");
  const adherence=target?logged.filter(x=>x.kcal>=target*.8&&x.kcal<=target*1.1).length:0;
  card.innerHTML='<h2>Weekly nutrition overview</h2><div class="statgrid"><div class="stat"><b>'+fmt(logged.length)+'/7</b><small>Days tracked</small></div><div class="stat"><b>'+fmt(logged.length?sum/logged.length:0)+'</b><small>Average kcal / tracked day</small></div><div class="stat"><b>'+fmt(logged.length?protein/logged.length:0)+' g</b><small>Average protein / tracked day</small></div></div><div style="display:flex;align-items:flex-end;gap:7px;margin:12px 0 4px">'+bars+'</div><div class="tiny muted">Daily calories · last 7 days</div>'+(target?'<p class="small muted">'+adherence+' of '+logged.length+' tracked days were within 80–110% of your calorie target.</p>':'<p class="small muted">Set a calorie target to see target adherence.</p>');
 }
 const priorProgress=window.renderProgress;
 if(typeof priorProgress==="function")window.renderProgress=function(){priorProgress.apply(this,arguments);try{renderWeek()}catch(e){console.warn("Weekly insights unavailable",e)}};
 function auditData(){
  const entries=Array.isArray(state.entries)?state.entries:[];
  const planner=Array.isArray(state.planner)?state.planner:[];
  const foods=(Array.isArray(window.referenceFoods)?window.referenceFoods.length:0)+(Array.isArray(state.customFoods)?state.customFoods.length:0)+(Array.isArray(state.products)?state.products.length:0);
  const invalid=entries.filter(x=>!x||typeof x!=="object"||!String(x.name||"").trim()||!/^\d{4}-\d{2}-\d{2}$/.test(String(x.date||""))||["kcal","protein","fat","carbs"].some(k=>!Number.isFinite(Number(x[k]))||Number(x[k])<0)).length;
  let storage={mode:"Not available",ready:false,error:null};
  try{if(window.NutriTrackStorage&&typeof window.NutriTrackStorage.status==="function")storage=window.NutriTrackStorage.status()}catch(e){storage.error=String(e.message||e)}
  return {entries:entries.length,planner:planner.length,foods,invalid,storage};
 }
 function renderDataHealth(){
  const settings=$("settings");if(!settings)return;
  let card=$("ntDataHealth");
  if(!card){card=document.createElement("section");card.id="ntDataHealth";card.className="card";const backup=$("backup");if(backup&&backup.parentElement)backup.parentElement.insertAdjacentElement("afterend",card);else settings.appendChild(card)}
  const a=auditData(),warning=a.invalid>0||!!a.storage.error;
  card.innerHTML='<h2>Data health check</h2><p class="small muted">A read-only check of your diary and saved nutrition data. Nothing is changed or deleted.</p><div class="statgrid"><div class="stat"><b>'+fmt(a.entries)+'</b><small>Diary entries</small></div><div class="stat"><b>'+fmt(a.planner)+'</b><small>Planned meals</small></div><div class="stat"><b>'+fmt(a.foods)+'</b><small>Available foods</small></div></div><p class="small" style="margin-top:10px;color:'+(warning?'var(--red)':'var(--green)')+'">'+(a.invalid?fmt(a.invalid)+' diary records need review.':'No malformed diary records detected.')+'</p><div class="tiny muted">Storage: '+String(a.storage.mode||"unknown")+(a.storage.ready?' · recovery database ready':' · recovery database not ready')+(a.storage.error?' · '+String(a.storage.error):'')+'</div><p class="tiny muted">Recommended: create a JSON backup before changing devices or clearing app data.</p>';
 }
 const prevGo=window.go;
 if(typeof prevGo==="function")window.go=function(page){const result=prevGo.apply(this,arguments);if(page==="progress")try{renderWeek()}catch(e){}if(page==="settings")try{renderDataHealth()}catch(e){}return result};
 document.addEventListener("visibilitychange",()=>{if(!document.hidden){const page=document.querySelector(".page.active");if(page&&page.id==="progress")try{renderWeek()}catch(e){}if(page&&page.id==="settings")try{renderDataHealth()}catch(e){}}});
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>{try{renderDataHealth()}catch(e){}});
 else try{renderDataHealth()}catch(e){}
 window.NutriTrackHealth={audit:auditData,refresh:()=>{renderDataHealth();renderWeek();return auditData()}};
})();
"""
idx=s.rfind("</script>")
if idx < 0:
    raise SystemExit("Inline script closing tag missing")
s=s[:idx]+code+"\n"+s[idx:]
html_path.write_text(s,encoding="utf-8")

# Keep Android package identity and signing configuration unchanged.
gradle_path=root/"app/build.gradle"
g=gradle_path.read_text(encoding="utf-8")
if "versionCode 14" not in g or "versionName '4.0.0'" not in g:
    raise SystemExit("Expected Android 4.0.0 / code 14 baseline not found")
g=g.replace("versionCode 14","versionCode 15",1).replace("versionName '4.0.0'","versionName '5.0.0'",1)
gradle_path.write_text(g,encoding="utf-8")

manifest_path=root/"app/src/main/assets/manifest.webmanifest"
m=manifest_path.read_text(encoding="utf-8")
if "NutriTrack 4.0" not in m:
    raise SystemExit("Expected PWA 4.0 marker not found")
manifest_path.write_text(m.replace("NutriTrack 4.0","NutriTrack 5.0",1),encoding="utf-8")
print("Applied NutriTrack 5.0 weekly insights, read-only data health audit and release metadata")
