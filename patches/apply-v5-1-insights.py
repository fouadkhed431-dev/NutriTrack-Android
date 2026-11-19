from pathlib import Path
root=Path(__file__).resolve().parents[1]
html=root/"app/src/main/assets/index.html"
s=html.read_text(encoding="utf-8")
if "NUTRITRACK_5_1_INSIGHTS" in s:
    print("NutriTrack 5.1 insights already applied")
    raise SystemExit(0)
code=r"""
/* NUTRITRACK_5_1_INSIGHTS */
(function(){
 "use strict";
 if(window.__NT_51_INSIGHTS__)return;
 window.__NT_51_INSIGHTS__=true;
 const $=id=>document.getElementById(id);
 const n=v=>{const x=Number(v);return Number.isFinite(x)&&x>=0?x:0};
 const fmt=v=>Math.round(v).toLocaleString();
 function renderAdvancedInsights(){
  const host=$("progress");if(!host||!Array.isArray(state.entries))return;
  let card=$("ntMacroWeightInsights");
  if(!card){card=document.createElement("section");card.id="ntMacroWeightInsights";card.className="card";const weekly=$("ntWeeklyInsights");if(weekly&&weekly.parentElement===host)weekly.insertAdjacentElement("afterend",card);else host.appendChild(card)}
  const keys=[];for(let i=6;i>=0;i--){const d=new Date();d.setHours(12,0,0,0);d.setDate(d.getDate()-i);keys.push(dateISO(d))}
  const logged=keys.map(key=>({key,rows:dayEntries(key)})).filter(x=>x.rows.length);
  const sums={protein:0,carbs:0,fat:0,kcal:0};
  logged.forEach(day=>{const t=totals(day.rows);Object.keys(sums).forEach(k=>sums[k]+=n(t[k]))});
  const avg=k=>logged.length?sums[k]/logged.length:0;
  const weights=(Array.isArray(state.weights)?state.weights:[]).filter(x=>x&&Number.isFinite(Number(x.kg))&&Number(x.kg)>0&&/^\d{4}-\d{2}-\d{2}$/.test(String(x.date||""))).slice().sort((a,b)=>a.date.localeCompare(b.date));
  const latest=weights.length?weights[weights.length-1]:null,first=weights.length?weights[0]:null;
  const change=latest&&first?Number(latest.kg)-Number(first.kg):0;
  const macroRows=[["Protein",avg("protein"),"g"],["Carbohydrates",avg("carbs"),"g"],["Fat",avg("fat"),"g"]];
  const macroHtml=macroRows.map(x=>'<div class="plan-row"><span>'+x[0]+'</span><b>'+fmt(x[1])+' '+x[2]+'</b></div>').join("");
  const weightHtml=latest?'<div class="statgrid"><div class="stat"><b>'+Number(latest.kg).toFixed(1)+' kg</b><small>Latest recorded weight</small></div><div class="stat"><b>'+(change>0?'+':'')+change.toFixed(1)+' kg</b><small>Change across '+weights.length+' records</small></div></div><p class="tiny muted">Latest entry: '+latest.date+'. Weight change is based on your first and latest saved measurements.</p>':'<p class="small muted">No weight records yet. Add measurements in Weight Tracker to see your trend here.</p>';
  card.innerHTML='<h2>Macros & weight trend</h2><p class="small muted">Daily macro averages use logged days from the last 7 days; unlogged days are excluded.</p><div class="stat"><b>'+fmt(avg("kcal"))+' kcal</b><small>Average calories per logged day</small></div>'+macroHtml+'<div class="divider"></div><h3>Weight progress</h3>'+weightHtml;
 }
 const original=window.renderProgress;
 if(typeof original==="function")window.renderProgress=function(){const result=original.apply(this,arguments);try{renderAdvancedInsights()}catch(e){console.warn("Macro and weight insights unavailable",e)}return result};
 const priorGo=window.go;
 if(typeof priorGo==="function")window.go=function(page){const result=priorGo.apply(this,arguments);if(page==="progress")try{renderAdvancedInsights()}catch(e){}return result};
 document.addEventListener("visibilitychange",()=>{if(!document.hidden){const p=document.querySelector(".page.active");if(p&&p.id==="progress")try{renderAdvancedInsights()}catch(e){}}});
 window.NutriTrackInsights={refresh:renderAdvancedInsights};
})();
"""
idx=s.rfind("</script>")
if idx<0: raise SystemExit("Inline script closing tag missing")
s=s[:idx]+code+"\n"+s[idx:]
html.write_text(s,encoding="utf-8")
gradle=root/"app/build.gradle"
g=gradle.read_text(encoding="utf-8")
if "versionCode 15" not in g or "versionName '5.0.0'" not in g: raise SystemExit("Expected 5.0.0 / code 15 baseline not found")
g=g.replace("versionCode 15","versionCode 16",1).replace("versionName '5.0.0'","versionName '5.1.0'",1)
gradle.write_text(g,encoding="utf-8")
manifest=root/"app/src/main/assets/manifest.webmanifest"
m=manifest.read_text(encoding="utf-8")
if "NutriTrack 5.0" not in m: raise SystemExit("Expected PWA 5.0 marker not found")
manifest.write_text(m.replace("NutriTrack 5.0","NutriTrack 5.1",1),encoding="utf-8")
print("Applied NutriTrack 5.1 macro averages, weight trend and release metadata")
