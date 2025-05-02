import {API_ENDPOINT} from './config.js';

// Simple templates
const templates = {
  discharge: `Dear GP,\n\nMr John Smith (DOB 01/01/1950, NHS 123‑456‑7890) was admitted on 14 March 2024…`,
  gp: `Re: Ms Jane Doe 08/08/1975 – referral for ophthalmology opinion.`
};

// Populate dropdown
const select = document.getElementById('template');
Object.keys(templates).forEach(k=>{
  const opt=document.createElement('option');
  opt.value=k; opt.textContent=k;
  select.appendChild(opt);
});
const textarea = document.getElementById('letter');
select.onchange = () => textarea.value = templates[select.value]||'';

const btn = document.getElementById('run');
const output = document.getElementById('output');
const timing = document.getElementById('timing');
const dlLink = document.getElementById('download');

btn.onclick = async () => {
  const text = textarea.value.trim();
  if(!text){alert('Please enter text');return;}
  timing.textContent='⏳ running…';
  const t0 = performance.now();
  const res = await fetch(API_ENDPOINT,{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text})
  });
  const data = await res.json();
  const t1 = performance.now();
  timing.textContent = `⏱ ${(t1-t0).toFixed(1)} ms (network) — API ${data.elapsed_ms} ms`;

  // Highlight PHI
  let html='',idx=0;
  data.phi_spans.sort((a,b)=>a.start-b.start).forEach(s=>{
    html+=escapeHTML(data.clean_text.slice(idx,s.start));
    html+=`<mark title="${s.type}">${escapeHTML(data.clean_text.slice(s.start,s.end))}</mark>`;
    idx=s.end;
  });
  html+=escapeHTML(data.clean_text.slice(idx));
  output.innerHTML = html;

  // download link
  const blob=new Blob([data.clean_text],{type:'text/plain'});
  dlLink.href=URL.createObjectURL(blob);
  dlLink.style.display='inline';
};

function escapeHTML(str){
  return str.replace(/[&<>"]/g,c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}
