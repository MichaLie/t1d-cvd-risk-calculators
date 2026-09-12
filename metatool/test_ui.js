/* Execute the real page event handlers in a minimal DOM, no browser dependency.
 * Layout and native browser behavior are reviewed separately. */
const fs=require('fs'), vm=require('vm'), assert=require('node:assert/strict');
const M=require('./models.js');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const el={};
for(const match of html.matchAll(/<(input|select|div|table)\b([^>]*\bid="([^"]+)"[^>]*)>/g)){
  const attrs=match[2],id=match[3];
  el[id]={value:attrs.match(/\bvalue="([^"]*)"/)?.[1]??'',checked:/\bchecked\b/.test(attrs),innerHTML:'',className:'',listeners:{},addEventListener(e,f){(this.listeners[e]??=[]).push(f);}};
}
Object.assign(el.sex,{value:'male'});el.ethnicity.value='white';el.alb.value='normal';el.region.value='high';
const context=vm.createContext({document:{getElementById:id=>{assert.ok(el[id],id);return el[id];}},window:{T1DCVD:M},console});
vm.runInContext([...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1],context);
function input(id,value){el[id].value=String(value);for(const f of el[id].listeners.input??[])f();}
function valid(){assert.notEqual(el.results.innerHTML,'');assert.ok(!/NaN|Infinity/.test(el.results.innerHTML));}
function invalid(pattern){assert.equal(el.results.innerHTML,'');assert.match(el.flag.innerHTML,pattern);}
function patient(){return vm.runInContext('patient()',context);}
valid();
input('age',69.5);assert.equal(patient().onset_age,49.5);valid();assert.ok(Number.isFinite(M.score2(patient())));
input('duration',70);invalid(/duration cannot exceed age/);input('duration',20);valid();
input('hba1cmmol',70);assert.equal(patient().hba1c_pct,M.hba1cMmolToPct(70));valid();
input('hba1cmmol','');invalid(/HbA1c/);input('hba1c',8);valid();
for(const id of ['age','duration','sbp','dbp','tc','hdl','tg','egfr','bmi','oe']){
 const old=el[id].value;input(id,'');invalid(/./);input(id,old);valid();
}
input('hdl',0);invalid(/HDL/);input('hdl',1.4);valid();
input('tg',5);invalid(/measured LDL/);input('ldl',2);valid();input('ldl',7);invalid(/LDL/);input('ldl','');input('tg',1.2);valid();
input('tc',1.5);invalid(/LDL/);input('tc',4.8);valid();
input('ethnicity','other');assert.equal(patient().ethrisk,9);
console.log('UI REGRESSIONS OK: timeline, fractional age, HbA1c precision, missing/invalid fields, LDL, ethnicity');
