from pathlib import Path

root = Path(__file__).resolve().parents[1]
html_path = root / "app/src/main/assets/index.html"
s = html_path.read_text(encoding="utf-8")

if "NUTRITRACK_5_2_PRIVACY_CONSENT" in s:
    print("NutriTrack 5.2 privacy/consent patch already applied")
    raise SystemExit(0)

if "NUTRITRACK_5_1_INSIGHTS" not in s:
    raise SystemExit("Expected NutriTrack 5.1 baseline not found")

# The checkbox is a one-request authorization, not a persistent preference.
old_ask = 'if(!$("aiConsent").checked)return toast("Consent is required before sending");'
old_photo = 'if(!$("aiConsent").checked)return toast("Consent is required before sending the photo");'
if s.count(old_ask) != 2:
    raise SystemExit(f"Expected exactly two question/test consent guards, found {s.count(old_ask)}")
if s.count(old_photo) != 1:
    raise SystemExit(f"Expected exactly one photo consent guard, found {s.count(old_photo)}")

s = s.replace(old_ask, 'if(!consumeAiConsent("Consent is required before sending"))return;', 2)
s = s.replace(old_photo, 'if(!consumeAiConsent("Consent is required before sending the photo"))return;', 1)

anchor = ' async function callProvider(prompt,imageData){'
helper = ''' function consumeAiConsent(message){
  const checkbox=$("aiConsent");
  if(!checkbox||!checkbox.checked){toast(message);return false}
  checkbox.checked=false;
  try{checkbox.dispatchEvent(new Event("change"))}catch(e){}
  return true;
 }
'''
if s.count(anchor) != 1:
    raise SystemExit("AI provider function insertion point is missing or ambiguous")
s = s.replace(anchor, helper + anchor, 1)

old_label = '<label class="small"><input id="aiConsent" type="checkbox"> I agree to send this question or selected meal photo to the chosen provider.</label>'
new_label = '<label id="aiConsentLabel" class="small" for="aiConsent" style="display:flex;align-items:flex-start;gap:10px;line-height:1.5;cursor:pointer;padding:10px 2px"><input id="aiConsent" type="checkbox" aria-describedby="aiConsentHelp" style="flex:0 0 22px;width:22px;height:22px;margin:0;accent-color:var(--green)"><span id="aiConsentHelp">I agree to send this question or selected meal photo to the chosen provider. This approval applies to one request only.</span></label>'
if s.count(old_label) != 1:
    raise SystemExit("AI consent label not found exactly once")
s = s.replace(old_label, new_label, 1)

old_description = 'OpenAI and Google Gemini. Your API key stays in memory for this session only and is not embedded in the APK.'
new_description = 'OpenAI and Google Gemini. You can use a session-only API key or save it encrypted on this device. Keys are not embedded in the APK.'
if old_description not in s:
    raise SystemExit("AI key privacy description not found")
s = s.replace(old_description, new_description, 1)

s = s.replace('/* NUTRITRACK_5_1_INSIGHTS */', '/* NUTRITRACK_5_1_INSIGHTS */\n/* NUTRITRACK_5_2_PRIVACY_CONSENT */', 1)
html_path.write_text(s, encoding="utf-8")

gradle_path = root / "app/build.gradle"
g = gradle_path.read_text(encoding="utf-8")
if "versionCode 16" not in g or "versionName '5.1.0'" not in g:
    raise SystemExit("Expected Android 5.1.0 / code 16 baseline not found")
g = g.replace("versionCode 16", "versionCode 17", 1).replace("versionName '5.1.0'", "versionName '5.2.0'", 1)
gradle_path.write_text(g, encoding="utf-8")

manifest_path = root / "app/src/main/assets/manifest.webmanifest"
m = manifest_path.read_text(encoding="utf-8")
if "NutriTrack 5.1" not in m:
    raise SystemExit("Expected PWA 5.1 baseline not found")
manifest_path.write_text(m.replace("NutriTrack 5.1", "NutriTrack 5.2", 1), encoding="utf-8")
print("Applied NutriTrack 5.2 one-request consent, larger touch target and release metadata")
