from pathlib import Path

root = Path(__file__).resolve().parent.parent
html = root / "app/src/main/assets/index.html"
java = root / "app/src/main/java/com/nutritrack/app/MainActivity.java"
s = html.read_text(encoding="utf-8")
if "nutritrack-ai-v1" not in s:
    marker = "</section>"
    pos = s.find(marker, s.find('<section id="settings"'))
    if pos < 0:
        raise SystemExit("Settings section closing marker not found")
    card = """
<div class="card" id="nutritrack-ai-v1"><h2>AI nutrition assistant</h2>
<p class="small muted">OpenAI and Google Gemini. API keys are encrypted with Android Keystore on this device.</p>
<div class="field"><label>Provider</label><select id="aiProvider"><option value="openai">OpenAI</option><option value="gemini">Google Gemini</option></select></div>
<div class="field"><label>API key</label><input id="aiKey" type="password" autocomplete="off" placeholder="Paste your provider API key"></div>
<div class="actions"><button class="soft" id="aiSaveKey">Save key securely</button><button class="ghost" id="aiDeleteKey">Delete saved key</button></div>
<div class="small muted" id="aiKeyStatus">No saved key for this provider.</div>
<div class="field"><label>Ask a question</label><textarea id="aiQuestion" rows="3" placeholder="Ask a nutrition question"></textarea></div>
<label class="small"><input id="aiConsent" type="checkbox"> I agree to send this question or selected meal photo to the chosen provider.</label>
<div class="actions"><button class="primary" id="aiAsk">Ask assistant</button><button class="soft" id="aiTest">Test connection</button></div>
<div class="field"><label>Meal photo analysis</label><input id="aiPhoto" type="file" accept="image/*" capture="environment"></div>
<div class="field"><label>Meal</label><select id="aiMeal"><option>Breakfast</option><option>Lunch</option><option>Dinner</option><option>Snack</option></select></div>
<button class="soft" id="aiAnalyze" style="width:100%">Analyze meal photo</button>
<div class="small muted" id="aiStatus" aria-live="polite"></div><div id="aiAnswer" class="card" hidden></div>
</div>
"""
    s = s[:pos] + card + s[pos:]
    js = r"""
// NutriTrack AI assistant v1: consent is read synchronously at each send action.
(function(){
 const $=id=>document.getElementById(id);
 const status=t=>{if($("aiStatus"))$("aiStatus").textContent=t};
 const provider=()=> $("aiProvider").value;
 const key=()=> $("aiKey").value.trim() || (window.AndroidBridge&&AndroidBridge.getAiKey?AndroidBridge.getAiKey(provider()):"");
 const allowed=()=>!!$("aiConsent").checked;
 const requireConsent=()=>{if(!allowed()){status("Consent is required before sending data.");return false}return true};
 const b64=blob=>new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result).split(",")[1]);r.onerror=reject;r.readAsDataURL(blob)});
 async function request(prompt,imageFile){
  const k=key();if(!k)throw Error("Enter or save an API key first.");
  if(provider()==="openai"){
   const userContent=[{type:"text",text:prompt}];
   if(imageFile)userContent.push({type:"image_url",image_url:{url:"data:"+imageFile.type+";base64,"+await b64(imageFile)}});
   const r=await fetch("https://api.openai.com/v1/chat/completions",{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+k},body:JSON.stringify({model:"gpt-4o-mini",messages:[{role:"system",content:"You are a cautious nutrition assistant. Estimate nutrition, state uncertainty, and never claim exact values from a photo."},{role:"user",content:userContent}],temperature:.2})});
   const j=await r.json();if(!r.ok)throw Error(j.error?.message||"OpenAI request failed");return j.choices?.[0]?.message?.content||"No response";
  }
  const parts=[{text:"You are a cautious nutrition assistant. Estimate nutrition, state uncertainty, and never claim exact values from a photo. "+prompt}];
  if(imageFile)parts.push({inline_data:{mime_type:imageFile.type,data:await b64(imageFile)}});
  const r=await fetch("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key="+encodeURIComponent(k),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({contents:[{parts}]})});
  const j=await r.json();if(!r.ok)throw Error(j.error?.message||"Gemini request failed");return j.candidates?.[0]?.content?.parts?.map(x=>x.text||"").join("\n")||"No response";
 }
 async function run(kind){
  if(!requireConsent())return;
  const photo=kind==="photo"?$("aiPhoto").files[0]:null;
  if(kind==="photo"&&!photo){status("Choose a meal photo first.");return}
  const q=kind==="test"?"Reply with exactly: connection successful.":kind==="photo"?"Analyze this "+$("aiMeal").value+" photo. Estimate foods, portion sizes, calories, protein, carbohydrates and fat. Clearly label uncertainty. Do not log the meal.":"Nutrition question: "+$("aiQuestion").value.trim();
  if(kind==="ask"&&!$("aiQuestion").value.trim()){status("Enter a question first.");return}
  status(kind==="test"?"Testing provider connection…":kind==="photo"?"Analyzing photo…":"Sending question…");
  ["aiAsk","aiTest","aiAnalyze"].forEach(id=>$(id).disabled=true);
  try{const answer=await request(q,photo);$("aiAnswer").hidden=false;$("aiAnswer").textContent=answer;status(kind==="test"?"Connection successful.": "Done. Review estimates before adding anything to your diary.");}
  catch(e){status("Request failed: "+e.message)}
  finally{["aiAsk","aiTest","aiAnalyze"].forEach(id=>$(id).disabled=false)}
 }
 $("aiSaveKey").onclick=()=>{const k=$("aiKey").value.trim();if(!k){status("Enter an API key first.");return}if(!window.AndroidBridge?.saveAiKey){status("Secure native storage is unavailable in this build.");return}const ok=AndroidBridge.saveAiKey(provider(),k);$("aiKeyStatus").textContent=ok?"Saved securely on this device.":"Could not save key securely.";status(ok?"API key saved.":"Secure save failed.")};
 $("aiDeleteKey").onclick=()=>{if(window.AndroidBridge?.deleteAiKey){AndroidBridge.deleteAiKey(provider());$("aiKey").value="";$("aiKeyStatus").textContent="No saved key for this provider.";status("Saved key deleted.")}};
 $("aiProvider").onchange=()=>{$("aiKey").value="";const v=window.AndroidBridge?.getAiKey?AndroidBridge.getAiKey(provider()):"";$("aiKeyStatus").textContent=v?"A saved key is available for this provider.":"No saved key for this provider.";};
 $("aiAsk").onclick=()=>run("ask");$("aiTest").onclick=()=>run("test");$("aiAnalyze").onclick=()=>run("photo");
})();
"""
    s = s.replace("</script>", js + "\n</script>", 1)
    html.write_text(s, encoding="utf-8")

j = java.read_text(encoding="utf-8")
if "saveAiKey(String provider" not in j:
    imports = """
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import java.security.KeyStore;
"""
    j = j.replace("import android.widget.Toast;", "import android.widget.Toast;\n" + imports, 1)
    methods = r'''
        private SecretKey aiSecretKey() throws Exception {
            KeyStore ks = KeyStore.getInstance("AndroidKeyStore"); ks.load(null);
            String alias = "NutriTrack.AI.API.KEY";
            if (ks.containsAlias(alias)) return (SecretKey) ks.getKey(alias, null);
            KeyGenerator kg = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            kg.init(new KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setRandomizedEncryptionRequired(true).build());
            return kg.generateKey();
        }
        @JavascriptInterface public boolean saveAiKey(String provider, String value) {
            try {
                Cipher c = Cipher.getInstance("AES/GCM/NoPadding"); c.init(Cipher.ENCRYPT_MODE, aiSecretKey());
                byte[] encrypted = c.doFinal(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                String stored = Base64.encodeToString(c.getIV(), Base64.NO_WRAP) + ":" + Base64.encodeToString(encrypted, Base64.NO_WRAP);
                getSharedPreferences("nutritrack_ai", MODE_PRIVATE).edit().putString(provider, stored).apply();
                return true;
            } catch (Exception e) { return false; }
        }
        @JavascriptInterface public String getAiKey(String provider) {
            try {
                String stored = getSharedPreferences("nutritrack_ai", MODE_PRIVATE).getString(provider, null);
                if (stored == null) return "";
                String[] parts = stored.split(":", 2);
                Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
                c.init(Cipher.DECRYPT_MODE, aiSecretKey(), new GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)));
                return new String(c.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), java.nio.charset.StandardCharsets.UTF_8);
            } catch (Exception e) { return ""; }
        }
        @JavascriptInterface public void deleteAiKey(String provider) {
            getSharedPreferences("nutritrack_ai", MODE_PRIVATE).edit().remove(provider).apply();
        }
'''
    marker = "    public class AndroidBridge {"
    if marker not in j: raise SystemExit("AndroidBridge marker missing")
    j = j.replace(marker, marker + "\n" + methods, 1)
    java.write_text(j, encoding="utf-8")
print("NutriTrack AI assistant patch applied")
