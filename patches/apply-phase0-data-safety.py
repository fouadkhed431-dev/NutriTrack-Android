from pathlib import Path
root = Path(__file__).resolve().parents[1]
hp = root / "app/src/main/assets/index.html"
s = hp.read_text(encoding="utf-8")
old = '''let state=load(),selectedFood=null,deferredInstall=null;
function load(){try{let old=JSON.parse(localStorage.getItem(DBKEY)||"{}");return {...defaults,...old,targets:{...defaults.targets,...(old.targets||{})},entries:Array.isArray(old.entries)?old.entries:[],customFoods:Array.isArray(old.customFoods)?old.customFoods:[],meals:Array.isArray(old.meals)?old.meals:[],weights:Array.isArray(old.weights)?old.weights:[],products:Array.isArray(old.products)?old.products:[],favorites:Array.isArray(old.favorites)?old.favorites:[],foodOverrides:old.foodOverrides&&typeof old.foodOverrides==="object"&&!Array.isArray(old.foodOverrides)?old.foodOverrides:{},hiddenReferenceFoods:Array.isArray(old.hiddenReferenceFoods)?old.hiddenReferenceFoods:[]}}catch(e){return JSON.parse(JSON.stringify(defaults))}}
function save(){try{localStorage.setItem(DBKEY,JSON.stringify(state));return true}catch(e){toast("Storage is full. Export a backup and remove some product photos.");return false}}'''
new = '''let state=load(),selectedFood=null,deferredInstall=null;
let lastPersistedState=JSON.stringify(state);
function load(){try{let old=JSON.parse(localStorage.getItem(DBKEY)||"{}");return {...defaults,...old,targets:{...defaults.targets,...(old.targets||{})},entries:Array.isArray(old.entries)?old.entries:[],customFoods:Array.isArray(old.customFoods)?old.customFoods:[],meals:Array.isArray(old.meals)?old.meals:[],weights:Array.isArray(old.weights)?old.weights:[],products:Array.isArray(old.products)?old.products:[],favorites:Array.isArray(old.favorites)?old.favorites:[],foodOverrides:old.foodOverrides&&typeof old.foodOverrides==="object"&&!Array.isArray(old.foodOverrides)?old.foodOverrides:{},hiddenReferenceFoods:Array.isArray(old.hiddenReferenceFoods)?old.hiddenReferenceFoods:[]}}catch(e){return JSON.parse(JSON.stringify(defaults))}}
function save(){
 try{const serialized=JSON.stringify(state);localStorage.setItem(DBKEY,serialized);if(localStorage.getItem(DBKEY)!==serialized)throw new Error("Storage verification failed");lastPersistedState=serialized;return true}
 catch(e){try{state=JSON.parse(lastPersistedState)}catch(rollbackError){}toast("لم يتم حفظ التغييرات. مساحة التخزين غير كافية أو تعذّر التحقق من الحفظ. صدّر نسخة احتياطية ثم حاول مرة أخرى.");return false}
}
function validateBackup(obj){
 const plain=v=>v!==null&&typeof v==="object"&&!Array.isArray(v),numeric=v=>typeof v==="number"&&Number.isFinite(v)&&v>=0;
 if(!plain(obj)||!Array.isArray(obj.entries)||!plain(obj.targets))throw new Error("Invalid backup structure");
 for(const k of ["kcal","protein","fat","carbs"])if(obj.targets[k]!==undefined&&!numeric(obj.targets[k]))throw new Error("Invalid target");
 for(const key of ["customFoods","meals","weights","products","favorites","hiddenReferenceFoods"])if(obj[key]!==undefined&&!Array.isArray(obj[key]))throw new Error("Invalid "+key);
 if(obj.foodOverrides!==undefined&&!plain(obj.foodOverrides))throw new Error("Invalid food overrides");
 for(const entry of obj.entries){if(!plain(entry)||typeof entry.name!=="string"||!entry.name.trim())throw new Error("Invalid diary entry");for(const k of ["grams","kcal","protein","fat","carbs","sugar"])if(entry[k]!==undefined&&entry[k]!==null&&!numeric(entry[k]))throw new Error("Invalid diary value")}
 for(const key of ["customFoods","products"])for(const food of (obj[key]||[])){if(!plain(food)||typeof food.name!=="string"||!food.name.trim())throw new Error("Invalid food record");for(const k of ["kcal","protein","fat","carbs","sugar","serving"])if(food[k]!==undefined&&food[k]!==null&&!numeric(food[k]))throw new Error("Invalid food nutrient")}
 for(const meal of (obj.meals||[]))if(!plain(meal)||typeof meal.name!=="string"||!Array.isArray(meal.items))throw new Error("Invalid saved meal");
 for(const weight of (obj.weights||[]))if(!plain(weight)||!numeric(weight.kg)||typeof weight.date!=="string")throw new Error("Invalid weight record");
 return {...defaults,...obj,targets:{...defaults.targets,...obj.targets},entries:obj.entries,customFoods:obj.customFoods||[],meals:obj.meals||[],weights:obj.weights||[],products:obj.products||[],favorites:obj.favorites||[],foodOverrides:obj.foodOverrides||{},hiddenReferenceFoods:obj.hiddenReferenceFoods||[]};
}'''
if new in s: raise SystemExit("Phase 0 patch already applied")
if old not in s: raise SystemExit("Expected 2.6.2 source block not found; refusing unsafe patch")
s = s.replace(old, new, 1)
restore_old = '''el("restoreFile").onchange=async e=>{try{let obj=JSON.parse(await e.target.files[0].text());if(!obj.entries||!obj.targets)throw Error();state={...defaults,...obj,foodOverrides:obj.foodOverrides&&typeof obj.foodOverrides==="object"&&!Array.isArray(obj.foodOverrides)?obj.foodOverrides:{},hiddenReferenceFoods:Array.isArray(obj.hiddenReferenceFoods)?obj.hiddenReferenceFoods:[]};save();toast("Backup restored");go("home")}catch(err){toast("Invalid backup file")}e.target.value=""};'''
restore_new = '''el("restoreFile").onchange=async e=>{try{const file=e.target.files&&e.target.files[0];if(!file)return;const obj=JSON.parse(await file.text());const validated=validateBackup(obj);const previous=state;state=validated;if(!save()){state=previous;return}toast("Backup restored and verified");renderHome();renderSettings();go("home")}catch(err){toast("Invalid backup file: check the file format and data")}finally{e.target.value=""}};'''
if restore_old not in s: raise SystemExit("Expected backup restore handler not found")
s = s.replace(restore_old, restore_new, 1)
count = s.count("save();")
if count != 15: raise SystemExit(f"Expected 15 remaining save calls, found {count}")
s = s.replace("save();", "if(!save())return;")
hp.write_text(s, encoding="utf-8")
mp = root / "app/src/main/assets/manifest.webmanifest"
m = mp.read_text(encoding="utf-8")
old_name = '"name": "NutriTrack 2.6 — Daily Nutrition"'
if old_name not in m: raise SystemExit("Expected PWA manifest name not found")
mp.write_text(m.replace(old_name, '"name": "NutriTrack 2.6.2 — Daily Nutrition"', 1), encoding="utf-8")
ap = root / "app/src/main/AndroidManifest.xml"
a = ap.read_text(encoding="utf-8")
if 'android:allowBackup="true"' not in a: raise SystemExit("Expected Android backup flag not found")
ap.write_text(a.replace('android:allowBackup="true"', 'android:allowBackup="false"', 1), encoding="utf-8")
print("Applied NutriTrack Phase 0 data-safety patch")
