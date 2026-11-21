from pathlib import Path

root = Path(__file__).resolve().parents[1]
html_path = root / "app/src/main/assets/index.html"
html = html_path.read_text(encoding="utf-8")
marker = "/* NUTRITRACK_6_0_BARCODE_SCANNER */"
if marker not in html:
    code = r"""
/* NUTRITRACK_6_0_BARCODE_SCANNER */
(function(){
 "use strict";
 if(window.__NT_60_BARCODE_SCANNER__)return;
 window.__NT_60_BARCODE_SCANNER__=true;
 const $=id=>document.getElementById(id);
 const home=$("home");
 if(!home)throw new Error("NutriTrack home page container not found");
 const card=document.createElement("section");
 card.id="ntBarcodeScanner";card.className="card";
 card.innerHTML='<h2>Barcode food scanner</h2><p class="small muted">Scan a packaged food barcode from a camera photo, or enter the barcode manually. The scanner searches your saved food database.</p><div class="field"><label>Scan barcode with camera</label><input id="ntBarcodeImage" type="file" accept="image/*" capture="environment"></div><div class="formgrid"><div class="field wide"><label>Barcode number</label><input id="ntBarcodeValue" inputmode="numeric" autocomplete="off" placeholder="Enter barcode"></div><button id="ntBarcodeSearch" class="soft" type="button">Find food</button></div><div id="ntBarcodeStatus" class="tiny muted" role="status" aria-live="polite"></div><div id="ntBarcodeMatch" hidden></div><div id="ntBarcodeNew" hidden><h3>Food not found — add its nutrition values</h3><div class="field"><label>Food name</label><input id="ntBarcodeName" maxlength="100"></div><div class="formgrid"><div class="field"><label>Calories / 100 g</label><input id="ntBarcodeKcal" type="number" min="0" step="0.1"></div><div class="field"><label>Protein / 100 g</label><input id="ntBarcodeProtein" type="number" min="0" step="0.1"></div><div class="field"><label>Carbs / 100 g</label><input id="ntBarcodeCarbs" type="number" min="0" step="0.1"></div><div class="field"><label>Fat / 100 g</label><input id="ntBarcodeFat" type="number" min="0" step="0.1"></div><div class="field"><label>Sugar / 100 g</label><input id="ntBarcodeSugar" type="number" min="0" step="0.1" value="0"></div></div></div><div id="ntBarcodeLog" hidden><div class="formgrid"><div class="field"><label>Quantity (g)</label><input id="ntBarcodeGrams" type="number" min="1" value="100"></div><div class="field"><label>Meal</label><select id="ntBarcodeMeal"><option>Breakfast</option><option>Lunch</option><option>Dinner</option><option>Snack</option></select></div></div><button id="ntBarcodeAdd" class="primary" type="button">Add to food diary</button><button id="ntBarcodeSaveNew" class="soft" type="button" hidden>Save food and add to diary</button></div>';
 home.appendChild(card);
 let selected=null,barcode="";
 const status=message=>{$("ntBarcodeStatus").textContent=message};
 const allFoods=()=>[].concat(Array.isArray(window.referenceFoods)?window.referenceFoods:[],state.customFoods||[],state.products||[]);
 function findFood(value){
  const q=String(value||"").trim();if(!q)return null;
  if(typeof window.searchFoods==="function"){const found=window.searchFoods(q);if(found&&found.length)return found[0]}
  return allFoods().find(f=>String(f.barcode||"").trim()===q)||null;
 }
 function showFood(food){
  selected=food;$("ntBarcodeNew").hidden=!!food;$("ntBarcodeMatch").hidden=!food;$("ntBarcodeLog").hidden=false;$("ntBarcodeSaveNew").hidden=!!food;$("ntBarcodeAdd").hidden=!food;
  if(food){const box=$("ntBarcodeMatch");box.textContent=food.name+" · "+Number(food.kcal||0)+" kcal · Protein "+Number(food.protein||0)+" g per 100 g";status("Food found. Confirm quantity and meal, then add it to your diary.")}
  else{$("ntBarcodeName").value="";status("No matching food was found. Enter the nutrition values shown on the package.");}
 }
 function search(value){
  barcode=String(value||"").trim();$("ntBarcodeValue").value=barcode;
  if(!barcode){status("Enter or scan a barcode first.");return}
  const food=findFood(barcode);showFood(food);
 }
 $("ntBarcodeSearch").addEventListener("click",()=>search($("ntBarcodeValue").value));
 $("ntBarcodeValue").addEventListener("keydown",e=>{if(e.key==="Enter")search($("ntBarcodeValue").value)});
 $("ntBarcodeImage").addEventListener("change",()=>{
  const file=$("ntBarcodeImage").files&&$("ntBarcodeImage").files[0];if(!file)return;
  if(!window.AndroidBridge||typeof AndroidBridge.scanBarcode!=="function"){status("Barcode camera scanning requires the updated Android app. You can still enter the barcode manually.");return}
  status("Reading barcode from image…");
  const reader=new FileReader();
  reader.onerror=()=>status("Could not read the selected image.");
  reader.onload=()=>{
   try{const value=AndroidBridge.scanBarcode(String(reader.result||""));if(!value)status("No barcode detected. Try a clearer, well-lit photo or enter the number manually.");else if(value.indexOf("ERROR:")===0)status(value.slice(6));else search(value)}
   catch(e){status("Barcode scan failed: "+String(e.message||e))}
  };
  reader.readAsDataURL(file);
 });
 function nutrient(id){const value=Number($(id).value);return Number.isFinite(value)&&value>=0?value:null}
 function addEntry(food,saveFood){
  const grams=Number($("ntBarcodeGrams").value),factor=grams/100;
  if(!Number.isFinite(grams)||grams<=0||grams>5000){status("Enter a valid quantity between 1 and 5000 g.");return}
  const nutrients={kcal:Number(food.kcal),protein:Number(food.protein),carbs:Number(food.carbs),fat:Number(food.fat),sugar:Number(food.sugar||0)};
  if(Object.keys(nutrients).some(k=>!Number.isFinite(nutrients[k])||nutrients[k]<0)){status("Food nutrition values are invalid.");return}
  if(saveFood){if(!String(food.name||"").trim()){status("Enter a food name.");return}state.customFoods.push(food)}
  const entry={id:"barcode-"+Date.now()+"-"+Math.random().toString(36).slice(2),date:dateISO(),meal:$("ntBarcodeMeal").value,name:food.name,ar:food.ar||"",grams:grams,kcal:nutrients.kcal*factor,protein:nutrients.protein*factor,fat:nutrients.fat*factor,carbs:nutrients.carbs*factor,sugar:nutrients.sugar*factor};
  state.entries.push(entry);
  if(!save()){state.entries.pop();if(saveFood)state.customFoods.pop();status("Could not save the food. Export a backup and check device storage.");return}
  status("Added "+food.name+" to your diary.");
  $("ntBarcodeLog").hidden=true;$("ntBarcodeMatch").hidden=true;$("ntBarcodeNew").hidden=true;$("ntBarcodeValue").value="";$("ntBarcodeImage").value="";selected=null;
  if(typeof renderHome==="function")renderHome();
 }
 $("ntBarcodeAdd").addEventListener("click",()=>{if(selected)addEntry(selected,false)});
 $("ntBarcodeSaveNew").addEventListener("click",()=>{
  const food={name:$("ntBarcodeName").value.trim(),barcode:barcode,kcal:nutrient("ntBarcodeKcal"),protein:nutrient("ntBarcodeProtein"),carbs:nutrient("ntBarcodeCarbs"),fat:nutrient("ntBarcodeFat"),sugar:nutrient("ntBarcodeSugar")};
  if(!food.name||Object.keys(food).some(k=>k!=="name"&&k!=="barcode"&&food[k]===null)){status("Complete the name and all nutrition values with non-negative numbers.");return}
  addEntry(food,true);
 });
})();
"""
    idx = html.rfind("</script>")
    if idx < 0: raise SystemExit("Could not locate application script closing tag")
    html = html[:idx] + code + "\n" + html[idx:]
    html_path.write_text(html, encoding="utf-8")

java_path = root / "app/src/main/java/com/nutritrack/app/MainActivity.java"
java = java_path.read_text(encoding="utf-8")
if "scanBarcode(String imageDataUrl)" not in java:
    import_anchor = "import com.googlecode.tesseract.android.TessBaseAPI;"
    if import_anchor not in java: raise SystemExit("Tesseract import anchor missing")
    java = java.replace(import_anchor, import_anchor + """
import com.google.mlkit.vision.barcode.common.Barcode;
import com.google.mlkit.vision.barcode.BarcodeScanner;
import com.google.mlkit.vision.barcode.BarcodeScannerOptions;
import com.google.mlkit.vision.barcode.BarcodeScanning;
import com.google.mlkit.vision.common.InputImage;
import com.google.android.gms.tasks.Tasks;""", 1)
    method_anchor = "    // Offline OCR after the Arabic and English language packs have been downloaded once."
    method = """    // Offline on-device barcode recognition using Google ML Kit.
    @JavascriptInterface
    public String scanBarcode(String imageDataUrl) {
        Bitmap bitmap = null;
        BarcodeScanner scanner = null;
        try {
            if (imageDataUrl == null) return "ERROR:No image was supplied";
            int comma = imageDataUrl.indexOf(',');
            String encoded = comma >= 0 ? imageDataUrl.substring(comma + 1) : imageDataUrl;
            byte[] imageBytes = Base64.decode(encoded, Base64.DEFAULT);
            bitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.length);
            if (bitmap == null) return "ERROR:Could not decode image";
            BarcodeScannerOptions options = new BarcodeScannerOptions.Builder()
                .setBarcodeFormats(Barcode.FORMAT_ALL_FORMATS).build();
            scanner = BarcodeScanning.getClient(options);
            java.util.List<Barcode> results = Tasks.await(scanner.process(InputImage.fromBitmap(bitmap, 0)));
            for (Barcode result : results) {
                String raw = result.getRawValue();
                if (raw != null && !raw.trim().isEmpty()) return raw.trim();
            }
            return "";
        } catch (Exception e) {
            return "ERROR:" + (e.getMessage() == null ? "Barcode scan failed" : e.getMessage());
        } finally {
            if (scanner != null) try { scanner.close(); } catch (Exception ignored) { }
            if (bitmap != null && !bitmap.isRecycled()) bitmap.recycle();
        }
    }

"""
    class_anchor = "public class AndroidBridge {"
    class_start = java.find(class_anchor)
    method_index = java.find("@JavascriptInterface", class_start)
    if class_start < 0 or method_index < 0:
        raise SystemExit("AndroidBridge insertion point missing")
    java = java[:method_index] + method + java[method_index:]
    java_path.write_text(java, encoding="utf-8")

gradle_path = root / "app/build.gradle"
gradle = gradle_path.read_text(encoding="utf-8")
dependency = "implementation 'com.google.mlkit:barcode-scanning:17.3.0'"
if dependency not in gradle:
    anchor = "dependencies {"
    if anchor not in gradle: raise SystemExit("Gradle dependencies block missing")
    gradle = gradle.replace(anchor, anchor + "\n    " + dependency, 1)
if "versionCode 17" not in gradle or "versionName '5.2.0'" not in gradle:
    raise SystemExit("Expected NutriTrack 5.2.0 release baseline not found")
gradle = gradle.replace("versionCode 17", "versionCode 18", 1).replace("versionName '5.2.0'", "versionName '6.0.0'", 1)
gradle_path.write_text(gradle, encoding="utf-8")

settings_path = root / "settings.gradle"
settings = settings_path.read_text(encoding="utf-8")
mirror = 'maven { url = uri("https://maven-central.storage-download.googleapis.com/maven2/") }'
if mirror not in settings:
    central = "        mavenCentral()"
    if central not in settings: raise SystemExit("Maven Central repository anchor missing")
    settings = settings.replace(central, "        " + mirror + "\\n" + central, 1)
    settings_path.write_text(settings, encoding="utf-8")

manifest_path = root / "app/src/main/assets/manifest.webmanifest"
manifest = manifest_path.read_text(encoding="utf-8")
if "NutriTrack 5.2" not in manifest: raise SystemExit("Expected PWA 5.2 baseline not found")
manifest_path.write_text(manifest.replace("NutriTrack 5.2", "NutriTrack 6.0", 1), encoding="utf-8")
print("Applied NutriTrack 6.0 barcode scanner and release metadata")
