/* Laboratory guides are hypotheses, never automatic chemical identifications. */
(function(root){
const sources={H:'https://physics.nist.gov/PhysRefData/Handbook/Tables/hydrogentable2.htm',He:'https://physics.nist.gov/PhysRefData/Handbook/Tables/heliumtable3.htm',Na:'https://physics.nist.gov/PhysRefData/Handbook/Tables/sodiumtable2_a.htm',Mg:'https://physics.nist.gov/PhysRefData/Handbook/Tables/magnesiumtable2_a.htm',Ca:'https://physics.nist.gov/PhysRefData/Handbook/Tables/calciumtable2_a.htm'};
const lines=[{name:'Hydrogen Hδ',short:'Hδ',element:'H',nm:410.174},{name:'Hydrogen Hγ',short:'Hγ',element:'H',nm:434.0462},{name:'Hydrogen Hβ',short:'Hβ',element:'H',nm:486.133},{name:'Hydrogen Hα',short:'Hα',element:'H',nm:656.28},
{name:'Helium He I',short:'He I',element:'He',nm:587.5615,note:'Near sodium D: a low-resolution feature cannot distinguish them by position alone.'},
{name:'Helium He I',short:'He I',element:'He',nm:667.8152},
{name:'Sodium D region',short:'Na D',element:'Na',nm:589.2937,range:'589.00–589.59',note:'Unresolved doublet region; overlaps the helium screening window.'},
{name:'Magnesium b region',short:'Mg b',element:'Mg',nm:517.4537,range:'516.73–518.36',note:'Three laboratory lines; this screen treats them as a blended region.'},
{name:'Calcium II K',short:'Ca K',element:'Ca',nm:393.3661,note:'Blue-end sensitivity and blending can dominate.'},
{name:'Calcium II H',short:'Ca H',element:'Ca',nm:396.8467,note:'Blends with nearby hydrogen Hε; not a unique calcium identification.'},
{name:'Calcium I',short:'Ca I',element:'Ca',nm:422.6727}];
function median(a){let z=a.slice().sort((a,b)=>a-b);return z.length%2?z[(z.length-1)/2]:(z[z.length/2-1]+z[z.length/2])/2}
function inspect(x,y,line,emission=false){
 if(!x||!y||x.length!==y.length||x.length<10)return {status:'insufficient data'};
 let left=[],right=[],search=[];for(let i=0;i<x.length;i++){let d=x[i]-line.nm;if(d>-14&&d<-8)left.push(i);if(d>8&&d<14)right.push(i);if(Math.abs(d)<=4)search.push(i)}
 if(left.length<3||right.length<3||search.length<3)return {status:'outside usable coverage'};
 // A local straight continuum is a screening approximation, not a physical stellar model.
 let lx=median(left.map(i=>x[i])),rx=median(right.map(i=>x[i])),ly=median(left.map(i=>y[i])),ry=median(right.map(i=>y[i]));
 if(ly<=0||ry<=0)return {status:'continuum too uncertain'};
 let ratios=search.map(i=>y[i]/(ly+(ry-ly)*(x[i]-lx)/(rx-lx)));let k=ratios.indexOf(emission?Math.max(...ratios):Math.min(...ratios)),i=search[k];let depth=emission?ratios[k]-1:1-ratios[k];
 let localMin=i>0&&i<y.length-1&&(emission?y[i]>y[i-1]&&y[i]>y[i+1]:y[i]<y[i-1]&&y[i]<y[i+1]);
 let integral=0;for(let q=1;q<search.length;q++){let i0=search[q-1],i1=search[q],v0=1-y[i0]/(ly+(ry-ly)*(x[i0]-lx)/(rx-lx)),v1=1-y[i1]/(ly+(ry-ly)*(x[i1]-lx)/(rx-lx));integral+=(x[i1]-x[i0])*(v0+v1)/2}
 return {window_integral_nm:integral,continuum_anchors:[[lx,ly],[rx,ry]],samples:search.length,status:localMin&&k>0&&k<search.length-1&&depth>=.03?(emission?'nearby peak':'nearby trough'):(emission?'no clear isolated peak':'no clear isolated trough'),minimum:x[i],depth,screening_threshold:.03};
}
function assess(job){
 if(!job.result.settings.scale)return {calibrated:false,lines:[]};
 let x=job.chart.axis,full=job.chart.full,odd=job.chart.odd,even=job.chart.even;
 return {calibrated:true,lines:lines.map(line=>{let m=inspect(x,full,line),a=inspect(x,odd,line),b=even?inspect(x,even,line):null;let repeats=m.status==='nearby trough'&&a.status==='nearby trough'&&b&&b.status==='nearby trough'&&Math.abs(a.minimum-b.minimum)<=3;let em=inspect(x,full,line,true),ea=inspect(x,odd,line,true),eb=even?inspect(x,even,line,true):null;let emissionRepeats=em.status==='nearby peak'&&ea.status==='nearby peak'&&eb&&eb.status==='nearby peak'&&Math.abs(ea.minimum-eb.minimum)<=3;return {...line,...m,repeats:Boolean(repeats),emission:em,emissionRepeats:Boolean(emissionRepeats),odd_measurement:a,even_measurement:b,identity:'unconfirmed'}})};
}
function color(nm,alpha=1){
 // Illustrative sRGB mapping of monochromatic visible wavelengths, not colorimetry.
 if(nm<380||nm>780)return `rgba(125,135,150,${alpha})`;
 let r=0,g=0,b=0;if(nm<440){r=(440-nm)/60;b=1}else if(nm<490){g=(nm-440)/50;b=1}else if(nm<510){g=1;b=(510-nm)/20}else if(nm<580){r=(nm-510)/70;g=1}else if(nm<645){r=1;g=(645-nm)/65}else r=1;
 let edge=nm<420?.3+.7*(nm-380)/40:nm>700?.3+.7*(780-nm)/80:1;
 return `rgba(${Math.round(255*Math.pow(r*edge,.8))},${Math.round(255*Math.pow(g*edge,.8))},${Math.round(255*Math.pow(b*edge,.8))},${alpha})`;
}
root.Chemistry={lines,sources,inspect,assess,color};if(typeof module!=='undefined')module.exports=root.Chemistry;
})(typeof window==='undefined'?globalThis:window);
