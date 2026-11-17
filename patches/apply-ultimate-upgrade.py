from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/"app/src/main/assets/index.html"
s=p.read_text(encoding="utf-8")
if "NUTRITRACK_ULTIMATE_3" in s:
 print("Already applied"); raise SystemExit(0)
css="""
/* NUTRITRACK_ULTIMATE_3 */
:root[data-theme="dark"]{color-scheme:dark;--green:#8bd3b2;--green2:#183b30;--ink:#edf5f0;--muted:#a5b6ac;--bg:#101a16;--card:#1a2922;--field-bg:#14221b;--nav-bg:#17251fee;--soft-surface:#22352b;--track-bg:#34483d;--line:#34483d;--red:#ff9991;--amber:#e8bb70;--shadow:0 8px 25px #0005}
:root[data-theme="dark"] body{background:var(--bg);color:var(--ink)}
:root[data-theme="dark"] .macro,:root[data-theme="dark"] .stat{background:#24372d}
:root[data-theme="dark"] .ring:before{background:var(--card)}
:root[data-theme="dark"] .tabs button,:root[data-theme="dark"] .suggest button{background:var(--card);color:var(--ink);border-color:var(--line)}
:root[data-theme="dark"] .notice{background:#3b3020;color:#f2d49b}
:root[data-theme="dark"] .remove,:root[data-theme="dark"] .danger{background:#482927;color:#ffaaa3}
:root[data-theme="dark"] .favorite{background:#40351f;color:#f0c77a}
:root[data-theme="dark"] .primary{background:#277c5c;color:white}
:root[data-theme="dark"] .soft{background:#234b3a;color:#b9f0d2}
:root[data-theme="dark"] .ghost{background:#293a31;color:var(--ink)}
:root[data-theme="dark"] input,:root[data-theme="dark"] select,:root[data-theme="dark"] textarea{color:var(--ink)!important;background:var(--field-bg)!important;border-color:var(--line)!important}
:root[data-theme="dark"] header{background:#183f31}
.plan-row{padding:10px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:8px;align-items:center}
.ai-answer{white-space:pre-wrap;line-height:1.6;background:var(--soft-surface);border-radius:12px;padding:12px;margin-top:10px}
"""
if "</style>" not in s: raise SystemExit("style marker missing")
s=s.replace("</style>",css+"</style>",1)
planner="""<section id="planner" class="page"><div class="card"><h2>Weekly meal planner</h2><div class="formgrid"><div class="field"><label>Day</label><select id="planDay"></select></div><div class="field"><label>Meal</label><select id="planMeal"><option>Breakfast</option><option>Lunch</option><option>Dinner</option><option>Snack</option></select></div><div class="field wide"><label>Food</label><input id="planFood" list="planFoodList" placeholder="Search food"><datalist id="planFoodList"></datalist></div><div class="field"><label>Quantity (g)</label><input id="planGrams" type="number" value="100" min="1"></div><button class="primary" id="planAdd">Add to plan</button></div><div id="weeklyPlan"></div></div><div class="card"><h2>Shopping list</h2><button class="soft" id="copyShopping">Copy list</button><div id="shoppingList"></div></div></section>"""
s=s.replace('<section id="settings"',planner+'<section id="settings"',1)
provider="""<div class="card"><h2>AI nutrition assistant</h2><p class="small muted">OpenAI and Google Gemini. Your API key stays in memory for this session only and is not embedded in the APK.</p><div class="field"><label>Provider</label><select id="aiProvider"><option value="openai">OpenAI</option><option value="gemini">Google Gemini</option></select></div><div class="field"><label>API key (session only)</label><input id="aiKey" type="password" autocomplete="off"></div><div class="field"><label>Question</label><textarea id="aiQuestion" rows="3" placeholder="Ask a nutrition question"></textarea></div><label class="small"><input id="aiConsent" type="checkbox"> I agree to send this question to the selected provider.</label><button class="primary" id="aiAsk" style="width:100%;margin-top:8px">Ask assistant</button><div id="aiStatus" class="tiny"></div><div id="aiAnswer" class="ai-answer" hidden></div></div>"""
mark='<div class="card"><h2>Data & backup</h2>'
if mark not in s: raise SystemExit("settings marker missing")
s=s.replace(mark,provider+mark,1)
s=s.replace('<button data-page="settings">','<button data-page="planner"><span class="ico">▦</span>Plan</button><button data-page="settings">',1)
s=s.replace('grid-template-columns:repeat(5,1fr)','grid-template-columns:repeat(6,1fr)',1)
s=s.replace('favorites:[]};','favorites:[],planner:[]};',1)
js=r"""
/* NUTRITRACK_ULTIMATE_3 */
(function(){
 var $=function(id){return document.getElementById(id)};
 var esc=function(v){return String(v==null?"":v).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};
 if(!Array.isArray(state.planner))state.planner=[];
 var days=Array.from({length:7},function(_,i){var d=new Date();d.setDate(d.getDate()+i);return {key:dateISO(d),label:d.toLocaleDateString(undefined,{weekday:"short",day:"numeric"})}});
 function applyTheme(){var t=localStorage.getItem("nutritrack_theme")==="dark"?"dark":"light";document.documentElement.dataset.theme=t;if($("themeToggle"))$("themeToggle").textContent=t==="dark"?"Switch to light mode":"Switch to dark mode"}
 applyTheme();
 if($("themeToggle"))$("themeToggle").onclick=function(){localStorage.setItem("nutritrack_theme",document.documentElement.dataset.theme==="dark"?"light":"dark");applyTheme()};
 var oldGo=window.go;window.go=function(page){oldGo(page);if(page==="planner")render()};
 function allFoods(){return [].concat(referenceFoods||[],state.customFoods||[],state.products||[])}
 function render(){
  if(!$("planDay"))return;
  if(!$("planDay").options.length)$("planDay").innerHTML=days.map(function(d){return '<option value="'+d.key+'">'+d.label+'</option>'}).join("");
  $("planFoodList").innerHTML=allFoods().map(function(f){return '<option value="'+esc(f.name)+'"></option>'}).join("");
  $("weeklyPlan").innerHTML=days.map(function(d){var rows=state.planner.filter(function(x){return x.date===d.key});return '<div class="meal"><div class="mealtitle"><span>'+d.label+'</span><span>'+Math.round(rows.reduce(function(a,x){return a+x.kcal},0))+' kcal</span></div>'+rows.map(function(x){return '<div class="plan-row"><span>'+esc(x.meal)+' · '+esc(x.name)+' ('+x.grams+' g)</span><span><button class="soft small" data-log="'+x.id+'">Log</button> <button class="danger small" data-del="'+x.id+'">×</button></span></div>'}).join("")+'</div>'}).join("");
  var list={};state.planner.forEach(function(x){list[x.name]=(list[x.name]||0)+x.grams});
  $("shoppingList").innerHTML=Object.keys(list).map(function(n){return '<div class="plan-row"><span>'+esc(n)+'</span><b>'+list[n]+' g</b></div>'}).join("")||"No planned foods yet.";
  $("weeklyPlan").querySelectorAll("[data-log]").forEach(function(b){b.onclick=function(){var x=state.planner.find(function(y){return y.id===b.dataset.log});if(!x)return;state.entries.push(Object.assign({},x,{id:Date.now().toString()+Math.random(),date:dateISO()}));save();toast("Added to diary") }});
  $("weeklyPlan").querySelectorAll("[data-del]").forEach(function(b){b.onclick=function(){state.planner=state.planner.filter(function(x){return x.id!==b.dataset.del});save();render()}});
 }
 $("planAdd").onclick=function(){var name=$("planFood").value,f=allFoods().find(function(x){return (x.name||"").toLowerCase()===name.toLowerCase()}),g=Math.max(1,num($("planGrams").value));if(!f){toast("Choose a food from suggestions");return}var z=g/100;state.planner.push({id:Date.now().toString()+Math.random(),date:$("planDay").value,meal:$("planMeal").value,name:f.name,grams:g,kcal:rnd(num(f.kcal)*z),protein:rnd(num(f.protein)*z),fat:rnd(num(f.fat)*z),carbs:rnd(num(f.carbs)*z)});if(!save())return;$("planFood").value="";render();toast("Added to weekly plan")};
 $("copyShopping").onclick=function(){var a={};state.planner.forEach(function(x){a[x.name]=(a[x.name]||0)+x.grams});var t=Object.keys(a).map(function(n){return n+": "+a[n]+" g"}).join("\n");if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(function(){toast("Shopping list copied")}).catch(function(){toast("Copy unavailable")});else toast("Copy unavailable")};
 $("aiAsk").onclick=async function(){var provider=$("aiProvider").value,key=$("aiKey").value.trim(),q=$("aiQuestion").value.trim();if(!key||!q){$("aiStatus").textContent="Enter API key and question.";return}if(!$("aiConsent").checked){$("aiStatus").textContent="Consent required.";return}var b=$("aiAsk");b.disabled=true;$("aiStatus").textContent="Connecting…";try{var answer="";
 if(provider==="openai"){var r=await fetch("https://api.openai.com/v1/chat/completions",{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+key},body:JSON.stringify({model:"gpt-4o-mini",messages:[{role:"system",content:"You are a cautious nutrition assistant. Give estimates and state assumptions."},{role:"user",content:q}],temperature:.2})});var j=await r.json();if(!r.ok)throw Error(j.error&&j.error.message||"OpenAI request failed");answer=j.choices&&j.choices[0].message.content||"No answer"}
 else{var r=await fetch("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key="+encodeURIComponent(key),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({contents:[{parts:[{text:"You are a cautious nutrition assistant. Give estimates and state assumptions.\n"+q}]}]})});var j=await r.json();if(!r.ok)throw Error(j.error&&j.error.message||"Gemini request failed");answer=j.candidates&&j.candidates[0].content.parts.map(function(x){return x.text||""}).join("\n")||"No answer"}
 $("aiAnswer").textContent=answer;$("aiAnswer").hidden=false;$("aiStatus").textContent="Review estimates before logging."; }catch(e){$("aiStatus").textContent="Request failed: "+e.message}finally{b.disabled=false}};
 var prev=window.renderProgress;if(typeof prev==="function")window.renderProgress=function(){prev();var c=$("monthSummary");if(!c){c=document.createElement("div");c.id="monthSummary";c.className="card";$("progress").appendChild(c)}var n=new Date(),from=dateISO(new Date(n.getFullYear(),n.getMonth(),1)),a=state.entries.filter(function(x){return x.date>=from&&x.date<=dateISO()}),sum=a.reduce(function(t,x){return t+num(x.kcal)},0),daysCount=new Set(a.map(function(x){return x.date})).size;c.innerHTML='<h2>This month</h2><div class="statgrid"><div class="stat"><b>'+Math.round(sum)+'</b><small>Total kcal</small></div><div class="stat"><b>'+daysCount+'</b><small>Days logged</small></div><div class="stat"><b>'+Math.round(daysCount?sum/daysCount:0)+'</b><small>Average kcal/day</small></div></div>'};
 render();
})();
"""
i=s.rfind("</script>")
if i<0: raise SystemExit("script end missing")
s=s[:i]+js+"\n"+s[i:]
p.write_text(s,encoding="utf-8")
print("NutriTrack 3.0 patch applied")
