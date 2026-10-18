/* Explicit axis conversion: never overlay nanometres on pixel distances. */
const Comparison=(()=>{
function select(jobs,excluded,mode){
 const completed=jobs.filter(j=>j.state==='done'),curves=[],unavailable=[];
 for(const j of completed){
  if(excluded.has(j.id))continue;
  const scale=Number(j.result.settings.scale),offset=Number(j.result.settings.offset_nm||0);
  const calibrated=Number.isFinite(scale)&&scale>0;
  if(mode==='wavelength'&&!calibrated){unavailable.push(j);continue}
  const x=mode==='pixels'&&calibrated?j.chart.axis.map(v=>(v-offset)/scale):j.chart.axis.slice();
  curves.push({id:j.id,label:j.label,x,y:j.chart.full});
 }
 return {completed:completed.length,curves,unavailable};
}
return {select};
})();
if(typeof module!=='undefined')module.exports=Comparison;
