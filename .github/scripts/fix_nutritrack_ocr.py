#!/usr/bin/env python3
from pathlib import Path
import sys

target = Path("app/src/main/assets/index.html")
if not target.exists():
    sys.exit("ERROR: app/src/main/assets/index.html was not found.")
src = target.read_text(encoding="utf-8")

start = src.find("function parseNutritionLabel(raw){")
end = src.find("\nif(el('readLabelBtn'))", start)
if start < 0 or end < 0:
    sys.exit("ERROR: OCR parser boundaries not found; no file changed.")

parser = r'''function parseNutritionLabel(raw){
 const lines=normalizeOcrDigits(raw).split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
 const rules={
  productK:/energy|calor(?:y|ies)|طاقة|سعرات|énergie/i,
  productP:/protein|proteins|protéine|proteines|بروتين/i,
  productF:/\bfat\b|\bfats\b|lipid|matières grasses|دهون/i,
  productC:/carbohydrate|carbohydrates|\bcarbs?\b|glucide|كربوهيدرات/i,
  productSugar:/sugar|sugars|sucres|سكر/i
 };
 const found={};
 for(const [field,re] of Object.entries(rules)){
  for(const line of lines){
   const hit=re.exec(line);if(!hit)continue;
   const tail=line.slice(hit.index+hit[0].length);
   let value=null;
   if(field==="productK"){
    const kcal=tail.match(/(\d+(?:\.\d+)?)\s*kcal\b/i);
    if(kcal)value=Number(kcal[1]);
    else {const nums=tail.match(/\d+(?:\.\d+)?/g)||[];if(nums.length===1&&!/kj/i.test(tail))value=Number(nums[0]);}
    if(value!==null&&value>1000)value=null;
   }else{
    const nums=tail.match(/\d+(?:\.\d+)?/g)||[];
    if(nums.length===1)value=Number(nums[0]);
    if(value!==null&&value>100)value=null;
   }
   if(value!==null&&Number.isFinite(value)&&value>=0){found[field]=value;break;}
  }
 }
 return found;
}'''
src = src[:start] + parser + src[end:]

photo_old = '''el("productPhoto").onchange=async e=>{const file=e.target.files&&e.target.files[0];if(!file)return;try{pendingProductPhoto=await compressPhoto(file);el("productPreview").src=pendingProductPhoto;el("productPreview").style.display="block";toast("Photo ready — review the label values") }catch(err){toast("Could not process this photo")}};'''
photo_new = '''el("productPhoto").onchange=async e=>{const file=e.target.files&&e.target.files[0];if(!file)return;
 pendingProductPhoto="";["productK","productP","productF","productC","productSugar"].forEach(id=>el(id).value="");
 el("ocrRawText").value="";el("ocrDetails").style.display="none";el("ocrStatus").textContent="New image selected. Read the label, then verify values before saving.";
 try{pendingProductPhoto=await compressPhoto(file);el("productPreview").src=pendingProductPhoto;el("productPreview").style.display="block";toast("Photo ready — previous scan values cleared")}
 catch(err){pendingProductPhoto="";el("productPreview").style.display="none";el("ocrStatus").textContent="Could not process this photo.";toast("Could not process this photo")}};'''
if photo_old not in src:
    sys.exit("ERROR: Photo-selection handler did not match; no file changed.")
src = src.replace(photo_old, photo_new, 1)

a = src.find("  const raw=AndroidBridge.recognizeNutritionLabel(pendingProductPhoto);")
b = src.find("\n }catch(e){status.textContent='OCR failed:", a)
if a < 0 or b < 0:
    sys.exit("ERROR: OCR result block boundaries not found; no file changed.")
block = '''  ["productK","productP","productF","productC","productSugar"].forEach(id=>el(id).value="");
  el("ocrRawText").value="";el("ocrDetails").style.display="none";
  const raw=AndroidBridge.recognizeNutritionLabel(pendingProductPhoto);
  if(String(raw).startsWith('ERROR:')){status.textContent=raw.slice(6);toast('Could not read this label');return}
  el('ocrRawText').value=raw;el('ocrDetails').style.display='block';
  const values=parseNutritionLabel(raw);let count=0;
  for(const [id,value] of Object.entries(values)){el(id).value=value;count++}
  status.textContent=count?('Found '+count+' possible values on matching OCR lines only. Verify each value and its serving basis before saving.'):'No safe value-to-row matches found. All nutrition fields were left blank; use the recognized text below and enter values manually.';
  toast(count?'Possible values found — verify before saving':'No safe matches; fields left blank');'''
src = src[:a] + block + src[b:]
target.write_text(src, encoding="utf-8")
print("SUCCESS: Updated OCR parser and stale-value clearing.")
