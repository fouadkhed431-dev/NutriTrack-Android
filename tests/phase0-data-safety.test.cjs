const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'app/src/main/assets/index.html'),'utf8');
const openTag='<script>',closeTag='</script>';
let cursor=0,scripts=[];
while(true){
 const a=html.indexOf(openTag,cursor);if(a<0)break;
 const b=html.indexOf(closeTag,a+openTag.length);if(b<0)throw Error('Unclosed inline script tag');
 scripts.push(html.slice(a+openTag.length,b));cursor=b+closeTag.length;
}
const script=scripts.join('\n');
assert(script.length>0,'No inline JavaScript found');
new vm.Script(script,{filename:'index.html.inline.js'});
assert(!script.includes('save();'),'Every save call must check persistence result');
const start=script.indexOf('const DBKEY='),end=script.indexOf('function el(id)',start);
assert(start>=0&&end>start,'Persistence module missing');
const core=script.slice(start,end);
function context(initial=null,fail=false){
 const store=new Map();if(initial!==null)store.set('nutritrack_v2_data',JSON.stringify(initial));
 const localStorage={getItem:k=>store.has(k)?store.get(k):null,setItem:(k,v)=>{if(fail)throw Error('quota');store.set(k,String(v))}};
 const c={localStorage,toast:()=>{},JSON,Number,Array,Object,Error};vm.createContext(c);
 vm.runInContext(core+'\nglobalThis.api={getState:()=>state,setState:v=>state=v,save,validateBackup,getStored:()=>localStorage.getItem(DBKEY)}',c);return c.api;
}
{
 const a=context();a.setState({targets:{kcal:2100,protein:140,fat:60,carbs:230},entries:[{name:'Test',grams:100,kcal:10,protein:1,fat:1,carbs:1}],customFoods:[],meals:[],weights:[],products:[],favorites:[],foodOverrides:{},hiddenReferenceFoods:[]});
 assert.strictEqual(a.save(),true);assert.strictEqual(a.getStored(),JSON.stringify(a.getState()));
}
{
 const a=context({targets:{kcal:2000},entries:[{name:'Persisted',grams:100,kcal:100,protein:5,fat:2,carbs:10}]},true);
 const before=JSON.stringify(a.getState());a.getState().entries.push({name:'Unsaved',grams:50,kcal:20,protein:1,fat:1,carbs:2});
 assert.strictEqual(a.save(),false);assert.strictEqual(JSON.stringify(a.getState()),before);
}
{
 const a=context(),b=a.validateBackup({targets:{kcal:2000},entries:[{name:'Rice',grams:100,kcal:130,protein:2,fat:1,carbs:28}]});
 assert.strictEqual(b.entries.length,1);assert.ok(Array.isArray(b.products)&&Array.isArray(b.customFoods));
}
{
 const a=context();assert.throws(()=>a.validateBackup({entries:{},targets:{}}));
 assert.throws(()=>a.validateBackup({entries:[{name:'Bad',kcal:-1}],targets:{}}));
 assert.throws(()=>a.validateBackup({entries:[],targets:[],products:[]}));
}
console.log('PASS: inline JavaScript syntax');
console.log('PASS: every save call checks persistence');
console.log('PASS: verified successful save');
console.log('PASS: failed save rollback');
console.log('PASS: backup validation and normalization');
