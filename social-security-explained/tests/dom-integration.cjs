/* Minimal fake DOM: exercises application initialization and event-driven logic without a browser. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
class ClassList{constructor(){this.values=new Set()}toggle(name,on){if(on===undefined? !this.values.has(name):on)this.values.add(name);else this.values.delete(name)}contains(name){return this.values.has(name)}}
class Element{
  constructor(tag='div',id=''){this.tag=tag;this.id=id;this.children=[];this.style={};this.dataset={};this.attrs={};this.listeners={};this.classList=new ClassList();this.value='';this.checked=false;this.hidden=false;this._text='';this.firstChild={textContent:''}}
  set textContent(v){this._text=String(v);this.children=[]}
  get textContent(){return this._text+this.children.map(c=>c.textContent||'').join('')}
  set innerHTML(v){this._text=String(v);this.children=[]}
  append(...children){this.children.push(...children)}
  addEventListener(event,handler){(this.listeners[event]??=[]).push(handler)}
  setAttribute(name,value){this.attrs[name]=String(value)}
  dispatch(event){(this.listeners[event]||[]).forEach(fn=>fn({target:this}))}
  click(){this.dispatch('click')}
  select(){/* clipboard fallback not exercised */}
  remove(){/* fake */}
  showModal(){this.open=true}
  close(){this.open=false}
}
const source=fs.readFileSync(path.join(__dirname,'..','index.source.html'),'utf8');
const ids=Array.from(source.matchAll(/\sid="([a-zA-Z0-9_-]+)"/g),m=>m[1]);
const dom=Object.fromEntries(ids.map(id=>[id,new Element('div',id)]));
Object.assign(dom.monthlyBenefit,{value:'3000'});Object.assign(dom.benefitRange,{value:'3000'});
Object.assign(dom.annualEarnings,{value:'100000'});Object.assign(dom.letterApproach,{value:'balanced'});
const views=['oasi','combined'].map(v=>{const el=new Element('button');el.dataset.view=v;return el});
const benefitPresets=['2071','3208'].map(v=>{const el=new Element('button');el.dataset.benefit=v;return el});
const scenarios=['22','17','0'].map((v,i)=>{const el=new Element('input');el.value=v;el.checked=i===0;return el});
const doc={
  readyState:'complete', body:new Element('body'),
  getElementById:id=>dom[id]||null,
  createElement:tag=>new Element(tag),
  createTextNode:text=>({textContent:String(text)}),
  querySelector:sel=>sel==='input[name="benefitScenario"]:checked'?scenarios.find(r=>r.checked):null,
  querySelectorAll:sel=>{
    if(sel==='[data-view]')return views;
    if(sel==='[data-benefit]')return benefitPresets;
    if(sel==='[data-policy]')return dom.policyList.children;
    if(sel==='input[name="benefitScenario"]')return scenarios;
    return [];
  }
};
const context={document:doc,window:{},Intl,Math,Number,String,Array,Set,Map,RegExp,console};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'..','app.js'),'utf8'),context);
assert.equal(dom.fundGrid.children.length,100,'100 grid units');
assert.equal(dom.fundGrid.children.filter(x=>x.classList.contains('unfunded')).length,22,'22 unfunded tiles');
views[1].click();
assert.equal(dom.payableAmount.textContent,'$83','2034 view');
assert.equal(dom.fundGrid.children.filter(x=>x.classList.contains('unfunded')).length,17,'17 unfunded tiles');
assert.equal(dom.policyList.children.length,6,'6 SSA options');
assert.equal(dom.monthlyBefore.textContent,'$3,000');
assert.equal(dom.annualLoss.textContent,'−$7,920');
scenarios.forEach(r=>r.checked=r.value==='17');scenarios[1].dispatch('change');
assert.equal(dom.annualLoss.textContent,'−$6,120');
dom.policyList.children.find(x=>x.dataset.policy==='E1.1').click();
assert.equal(dom.extraTax.textContent,'$2,300');
assert.equal(dom.stateSelect.children.length,56,'50 states, DC, and five territories');
dom.stateSelect.value='DC';dom.stateSelect.dispatch('change');
assert.equal(dom.senateHeading.textContent,'No U.S. Senators');
assert.equal(dom.senateLink.hidden,true);
assert.equal(dom.houseLink.href,'https://www.house.gov/representatives');
dom.stateSelect.value='CA';dom.stateSelect.dispatch('change');
assert.equal(dom.senateLink.hidden,false);
assert.ok(dom.senateLink.href.includes('/CA/intro.htm'));
dom.zipInput.value='94510';dom.zipInput.dispatch('input');
assert.equal(dom.copyZip.hidden,false);
dom.senderName.value='Alex Example';dom.cityInput.value='Benicia';dom.personalStory.value='This matters to my family.';
dom.draftLetter.click();
assert.ok(dom.letterBody.value.includes('Benicia, California 94510'));
assert.ok(dom.letterBody.value.includes('Dear Member of Congress'));
assert.ok(dom.letterBody.value.includes('Alex Example'));
assert.ok(dom.letterBody.value.includes('This matters to my family.'));
console.log('DOM integration simulation PASS: initialization, grid, toggles, policy impact, all regions, contact links, editable letter draft.');