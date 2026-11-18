from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
html_path = root / "app/src/main/assets/index.html"
s = html_path.read_text(encoding="utf-8")
if "NUTRITRACK_QUALITY_31" in s:
    print("Quality upgrade already applied")
    raise SystemExit(0)

# Remove the superseded legacy AI click handler. The integrated handler below
# supports saved Keystore keys and must be the only handler for aiAsk.
start = ' $("aiAsk").onclick=async function(){var provider=$("aiProvider").value'
end = ' var prev=window.renderProgress;'
a = s.find(start)
b = s.find(end, a)
if a < 0 or b < 0:
    raise SystemExit("Legacy AI handler boundary not found; refusing to patch")
s = s[:a] + " // Legacy duplicate AI handler removed by Quality 3.1.\n" + s[b:]

old_parser = ' function parseMealItems(raw){let text=String(raw||"").trim().replace(/^\x60\x60\x60(?:json)?\\s*/i,"").replace(/\x60\x60\x60$/i,"").trim();let data;try{data=JSON.parse(text)}catch(e){const a=text.indexOf("[");const b=text.lastIndexOf("]");if(a<0||b<=a)throw Error("AI response did not contain a readable food list");data=JSON.parse(text.slice(a,b+1))}if(data&&Array.isArray(data.items))data=data.items;if(!Array.isArray(data))throw Error("Expected a JSON array of food estimates");return data.map(x=>({name:String(x.name||"Food estimate"),grams:Math.max(1,num(x.grams)||100),kcal:Math.max(0,num(x.kcal)),protein:Math.max(0,num(x.protein)),fat:Math.max(0,num(x.fat)),carbs:Math.max(0,num(x.carbs))})).filter(x=>x.name)}'
# Match the actual one-line function independent of minor quote style.
m = re.search(r' function parseMealItems\(raw\)\{[^\n]*\}', s)
if not m:
    raise SystemExit("AI meal parser not found")
new_parser = """ function parseMealItems(raw){
  let text=String(raw||"").trim().replace(/^\x60\x60\x60(?:json)?\\s*/i,"").replace(/\x60\x60\x60$/i,"").trim(),data;
  try{data=JSON.parse(text)}catch(e){const a=text.indexOf("["),b=text.lastIndexOf("]");if(a<0||b<=a)throw Error("AI response did not contain a readable food list");data=JSON.parse(text.slice(a,b+1))}
  if(data&&Array.isArray(data.items))data=data.items;
  if(!Array.isArray(data)||data.length===0||data.length>30)throw Error("Expected between 1 and 30 food estimates");
  return data.map((x,i)=>{
   if(!x||typeof x!=="object"||Array.isArray(x))throw Error("Invalid food estimate at item "+(i+1));
   const name=String(x.name||"").trim(),grams=Number(x.grams),kcal=Number(x.kcal),protein=Number(x.protein),fat=Number(x.fat),carbs=Number(x.carbs);
   if(!name||name.length>100)throw Error("Invalid food name at item "+(i+1));
   if(!Number.isFinite(grams)||grams<1||grams>5000)throw Error("Invalid portion size for "+name);
   for(const [label,value] of [["calories",kcal],["protein",protein],["fat",fat],["carbs",carbs]])if(!Number.isFinite(value)||value<0||value>10000)throw Error("Invalid "+label+" estimate for "+name);
   return {name,grams,kcal,protein,fat,carbs};
  });
 }"""
s = s[:m.start()] + new_parser + s[m.end():]

# Validate planned items when restoring a backup; a malformed plan must not
# enter the live state even if the diary itself is valid.
needle = ' if(obj.planner!==undefined&&!Array.isArray(obj.planner))throw new Error("Invalid planner");'
if needle not in s:
    raise SystemExit("Planner backup validation marker not found")
s = s.replace(needle, needle + '''
 for(const item of (obj.planner||[])){if(!plain(item)||typeof item.name!=="string"||!item.name.trim()||typeof item.date!=="string")throw new Error("Invalid planner item");for(const k of ["grams","kcal","protein","fat","carbs"])if(!numeric(item[k]))throw new Error("Invalid planner value")}
''', 1)
# Preserve planner during backup normalization for older backups too.
needle2 = 'favorites:obj.favorites||[],foodOverrides:obj.foodOverrides||{},hiddenReferenceFoods:obj.hiddenReferenceFoods||[]};'
if needle2 not in s:
    raise SystemExit("Backup normalization marker not found")
s = s.replace(needle2, 'favorites:obj.favorites||[],planner:obj.planner||[],foodOverrides:obj.foodOverrides||{},hiddenReferenceFoods:obj.hiddenReferenceFoods||[]};', 1)

# Guard native key-status reads: a bridge exception must never stop app startup.
old_key = ' function keyStatus(){const ok=!!(window.AndroidBridge&&AndroidBridge.readAiKey&&AndroidBridge.readAiKey(selectedProvider()));$("aiKeyStatus").textContent=ok?"A key for this provider is saved encrypted on this device.":"No saved key for this provider. You can use a session-only key in the field above."}'
new_key = ' function keyStatus(){let ok=false;try{ok=!!(window.AndroidBridge&&AndroidBridge.readAiKey&&AndroidBridge.readAiKey(selectedProvider()))}catch(e){ok=false}if($("aiKeyStatus"))$("aiKeyStatus").textContent=ok?"A key for this provider is saved encrypted on this device.":"No saved key for this provider. You can use a session-only key in the field above."}'
if old_key not in s:
    raise SystemExit("AI key status function not found")
s = s.replace(old_key, new_key, 1)

# Keep consent state explicit in the UI; this does not grant consent automatically.
needle3 = ' keyStatus();\n // Meal photo estimates are editable'
if needle3 not in s:
    raise SystemExit("AI initialization marker not found")
s = s.replace(needle3, ''' if($("aiConsent"))$("aiConsent").addEventListener("change",()=>{if(!$("aiConsent").checked)$("aiStatus").textContent="Consent is off. No question or photo will be sent.";else $("aiStatus").textContent="Consent enabled for the next AI request only."});
 keyStatus();
 // Meal photo estimates are editable''', 1)

# Mark the release and increment the Android version without touching the
# package identity or signing configuration.
s = s.replace("/* NUTRITRACK_COMPLETION_3 */", "/* NUTRITRACK_COMPLETION_3 */\n/* NUTRITRACK_QUALITY_31 */", 1)
html_path.write_text(s, encoding="utf-8")

manifest_path = root / "app/src/main/assets/manifest.webmanifest"
manifest = manifest_path.read_text(encoding="utf-8")
if "NutriTrack 3.0" not in manifest:
    raise SystemExit("PWA manifest 3.0 marker not found")
manifest_path.write_text(manifest.replace("NutriTrack 3.0", "NutriTrack 3.1", 1), encoding="utf-8")

gradle_path = root / "app/build.gradle"
gradle = gradle_path.read_text(encoding="utf-8")
if "versionCode 12" not in gradle or "versionName '3.0.0'" not in gradle:
    raise SystemExit("Expected Android version 3.0.0 / code 12 not found")
gradle = gradle.replace("versionCode 12", "versionCode 13", 1).replace("versionName '3.0.0'", "versionName '3.1.0'", 1)
gradle_path.write_text(gradle, encoding="utf-8")
print("Applied NutriTrack 3.1 quality, AI validation, backup validation and version upgrade")
