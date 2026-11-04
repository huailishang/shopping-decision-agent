'use strict';
const $=id=>document.getElementById(id);
const numeric=['monthly_pages','budget_max_cny','idle_weeks'];
const booleans=['needs_color','accepts_outsourced_color','requires_wireless','requires_scan'];
let payload=null, outcome=null;
function stage(n){for(let i=1;i<=4;i++)$('step'+i).hidden=i!==n;$('error').hidden=true;}
function fail(message){$('error').textContent=message;$('error').hidden=false;}
function gather(){const d={description:$('description').value.trim(),category:'printer',confirmed:true};if(!d.description)throw Error('请先输入需求');for(const k of numeric){const raw=$(k).value.trim();if(raw===''){d[k]=null;continue;}if(!/^\d+$/.test(raw)||!Number.isSafeInteger(Number(raw))||Number(raw)>1000000)throw Error(k+' 请输入合理的非负整数');d[k]=Number(raw);}for(const k of booleans)d[k]=$(k).value===''?null:$(k).value==='true';d.requirements=$('requirements').value.split('\n').map(s=>s.trim()).filter(Boolean);return d;}
function clearResult(){outcome=null;$('output').textContent='';$('record').hidden=true;$('record').textContent='';}
$('next').onclick=()=>{if(!$('description').value.trim())return fail('请填写一句话需求');clearResult();stage(2);};
$('back1').onclick=()=>{clearResult();stage(1)};
$('review').onclick=()=>{try{payload=gather();clearResult();const names={monthly_pages:'每月张数',budget_max_cny:'预算（元）',idle_weeks:'闲置周数',needs_color:'彩色需求',accepts_outsourced_color:'接受外包彩印',requires_wireless:'无线/手机打印',requires_scan:'扫描'};const lines=['原始需求：'+payload.description,...Object.entries(names).map(([k,v])=>v+'：'+(payload[k]===null?'未知':typeof payload[k]==='boolean'?(payload[k]?'是':'否'):payload[k])), '待核对原话与其他硬要求：\n'+[payload.description,...payload.requirements].join('\n')];$('summary').textContent=lines.join('\n');stage(3);}catch(e){fail(e.message)}};
$('back2').onclick=()=>{clearResult();stage(2)};
$('back3').onclick=()=>{clearResult();stage(2)};
for(const id of ['description','requirements',...numeric,...booleans])$(id).addEventListener('input',clearResult);
$('submit').onclick=async()=>{clearResult();$('submit').disabled=true;$('summary').textContent+='\n\n正在调用本地决策服务…';try{const response=await fetch('/api/decide',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),cache:'no-store'});const data=await response.json();if(!response.ok)throw Error(data.error||'服务失败');outcome=data;const r=data.recommendation;const label={clarify:'还需澄清',defer:'暂缓唯一推荐',compare_routes:'比较路线',route_recommended:'路线建议',invalid:'条件无效',unsupported:'暂不支持'};const lines=['结果：'+(label[r.status]||r.status),'','依据：',...r.reasons.map(s=>'• '+s),...(r.questions.length?['','需确认：',...r.questions.map(s=>'• '+s)]:[]),...(r.unknowns.length?['','尚未核实：',...r.unknowns.map(s=>'• '+s)]:[]),'','当前可用于决策的证据：'+(data.evidence.length?data.evidence.map(e=>e.id+' '+e.source+' '+e.published_on).join('；'):'无'),'13张历史卡仅作研究索引，不能冒充独立批准的当前购买证据。','不提供机型、现价或交易。'];$('output').textContent=lines.join('\n');stage(4);}catch(e){$('summary').textContent=$('summary').textContent.replace(/\n\n正在调用本地决策服务…$/,'');fail('本机服务异常：'+e.message+'。请再次点击“确认并判断”重试。');}finally{$('submit').disabled=false;}};
$('export').onclick=()=>{if(!outcome)return fail('尚无可预览记录');$('record').textContent=JSON.stringify({type:'H08_review_preview_not_auto_saved',original_description:payload.description,confirmed_fields:payload,decision:outcome,manual_feedback:'待独立评估者填写'},null,2);$('record').hidden=false;};
stage(1);
