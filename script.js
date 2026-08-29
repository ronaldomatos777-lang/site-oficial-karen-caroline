
// V5.30 — ativa os ícones sociais somente quando os perfis oficiais forem configurados.
(()=>{
  const cfg=window.KAREN_SOCIALS||{};
  document.querySelectorAll('.social-icon').forEach(icon=>{
    const name=(icon.getAttribute('aria-label')||'').toLowerCase();
    const key=name.includes('instagram')?'instagram':name.includes('tiktok')?'tiktok':name.includes('facebook')?'facebook':'';
    const url=key&&cfg[key];
    if(!url) return;
    const a=document.createElement('a');
    for(const attr of icon.attributes) a.setAttribute(attr.name,attr.value);
    a.classList.add('social-live');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.innerHTML=icon.innerHTML;
    icon.replaceWith(a);
  });
})();
function getUtm(){
  const p=new URLSearchParams(location.search);
  return {
    utm_source:p.get('utm_source')||'',
    utm_medium:p.get('utm_medium')||'',
    utm_campaign:p.get('utm_campaign')||'',
    utm_content:p.get('utm_content')||'',
    utm_term:p.get('utm_term')||''
  }
}
function pageContext(){
  const form=document.querySelector('.lead-form[data-empreendimento]');
  const rawTitle=document.title.split('|')[0].trim();
  const empreendimento=form?.dataset.empreendimento||document.body.dataset.empreendimento||((rawTitle && !/^Empreendimentos em Campinas/i.test(rawTitle))?rawTitle:'Karen Caroline Imóveis');
  const utm=getUtm();
  return {
    empreendimento,
    pagina_url:location.href,
    pagina_titulo:document.title,
    referrer:document.referrer||'',
    ...utm
  }
}
function apiEndpoint(path){
  return location.protocol==='file:' ? `http://127.0.0.1:5000${path}` : path;
}

function queuePendingLead(payload){
  try{
    const key='karen_pending_leads_v1';
    const list=JSON.parse(localStorage.getItem(key)||'[]');
    list.push({...payload,...pageContext(),queued_at:new Date().toISOString()});
    localStorage.setItem(key,JSON.stringify(list.slice(-50)));
    return true;
  }catch(_e){return false}
}
async function syncPendingLeads(){
  if(location.protocol==='file:') return;
  const key='karen_pending_leads_v1';
  let list=[];
  try{list=JSON.parse(localStorage.getItem(key)||'[]')}catch(_e){}
  if(!Array.isArray(list)||!list.length) return;
  const remaining=[];
  for(const item of list){
    try{
      const r=await fetch('/api/leads',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(item)});
      if(!r.ok) remaining.push(item);
    }catch(_e){remaining.push(item)}
  }
  try{localStorage.setItem(key,JSON.stringify(remaining))}catch(_e){}
}
window.addEventListener('load',syncPendingLeads);

async function saveLead(payload){
  let r;
  try{
    r=await fetch(apiEndpoint('/api/leads'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...payload,...pageContext()})});
  }catch(_err){
    const queued=queuePendingLead(payload);
    const err=new Error(queued?'CRM indisponível agora. O pedido foi salvo neste navegador e será sincronizado quando o site estiver conectado.':'Não foi possível conectar ao CRM.');
    err.queued=queued;
    throw err;
  }
  const data=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(data.error||'Não foi possível concluir o cadastro.');
  return data
}
async function trackEvent(tipo,extra={}){
  try{
    await fetch(apiEndpoint('/api/events'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo,...pageContext(),...extra}),keepalive:true});
  }catch(_e){}
}
function campaignLabel(){
  const u=getUtm();
  const parts=[];
  if(u.utm_source)parts.push(`origem: ${u.utm_source}`);
  if(u.utm_campaign)parts.push(`campanha: ${u.utm_campaign}`);
  if(u.utm_medium)parts.push(`mídia: ${u.utm_medium}`);
  return parts.join(' • ')||'acesso direto ao site';
}


// V5.22 — menu mobile profissional
(()=>{
  const header=document.querySelector('.site-header');
  if(!header) return;
  const nav=header.querySelector('nav');
  if(!nav) return;
  const toggle=document.createElement('button');
  toggle.type='button';toggle.className='mobile-menu-toggle';toggle.setAttribute('aria-label','Abrir menu');toggle.setAttribute('aria-expanded','false');
  toggle.innerHTML='<span></span><span></span><span></span>';
  header.appendChild(toggle);
  const overlay=document.createElement('div');overlay.className='mobile-menu-overlay';overlay.setAttribute('aria-hidden','true');
  const panel=document.createElement('div');panel.className='mobile-menu-panel';
  panel.innerHTML=`<button type="button" class="mobile-menu-close" aria-label="Fechar menu">×</button><div class="mobile-menu-brand"><img src="karen-caroline-logo-oficial.png" alt="Karen Caroline Consultora Imobiliária"></div><nav class="mobile-nav">${nav.innerHTML}<a class="mobile-contact" href="index.html#contato">Falar com Karen</a></nav>`;
  overlay.appendChild(panel);document.body.appendChild(overlay);
  const open=()=>{overlay.classList.add('open');overlay.setAttribute('aria-hidden','false');toggle.setAttribute('aria-expanded','true');document.body.classList.add('menu-open')};
  const close=()=>{overlay.classList.remove('open');overlay.setAttribute('aria-hidden','true');toggle.setAttribute('aria-expanded','false');document.body.classList.remove('menu-open')};
  toggle.addEventListener('click',open);panel.querySelector('.mobile-menu-close').addEventListener('click',close);overlay.addEventListener('click',e=>{if(e.target===overlay)close()});panel.querySelectorAll('a').forEach(a=>a.addEventListener('click',close));document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
})();

// Formulários normais
for(const form of document.querySelectorAll('.lead-form')){
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    const box=form.parentElement.querySelector('.form-ok');
    const fd=new FormData(form);const payload=Object.fromEntries(fd.entries());
    payload.empreendimento=form.dataset.empreendimento||'Site geral';payload.origem='formulario_contato';
    try{if(box)box.textContent='Enviando...';await saveLead(payload);if(box)box.textContent='✓ Cadastro realizado. Em breve entraremos em contato.';form.reset()}
    catch(err){if(box)box.textContent='⚠ '+err.message}
  })
}

// Material Casa Prado
const modal=document.getElementById('material-modal');
if(modal){
  const open=()=>{modal.classList.add('open');modal.setAttribute('aria-hidden','false');document.body.classList.add('modal-open')};
  const close=()=>{modal.classList.remove('open');modal.setAttribute('aria-hidden','true');document.body.classList.remove('modal-open')};
  document.querySelectorAll('[data-open-material]').forEach(b=>b.addEventListener('click',open));
  document.querySelectorAll('[data-close-material]').forEach(b=>b.addEventListener('click',close));
  modal.addEventListener('click',e=>{if(e.target===modal)close()});document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
  const form=modal.querySelector('.material-form');const status=modal.querySelector('.material-status');
  form.addEventListener('submit',async e=>{e.preventDefault();const fd=new FormData(form);const payload=Object.fromEntries(fd.entries());payload.empreendimento='Casa Prado Residence';payload.origem='download_material';try{status.textContent='Cadastrando e preparando o material...';const data=await saveLead(payload);status.textContent='✓ Cadastro realizado. O download será iniciado.';form.reset();if(data.download_url){setTimeout(()=>{const a=document.createElement('a');a.href=data.download_url;a.download='Casa-Prado-Material-Completo.pdf';document.body.appendChild(a);a.click();a.remove()},500)}}catch(err){status.textContent='⚠ '+err.message}})
}

// WhatsApp oficial + contexto automático
const WHATSAPP_NUMBER='5519974078273';
const WHATSAPP_SVG=`<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false"><path fill="currentColor" d="M19.11 17.24c-.3-.15-1.77-.87-2.04-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.17-.17.2-.35.22-.65.07-.3-.15-1.27-.47-2.42-1.5-.9-.8-1.5-1.78-1.68-2.08-.17-.3-.02-.46.13-.61.14-.13.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.62-.92-2.22-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.8.37-.27.3-1.04 1.02-1.04 2.49s1.07 2.89 1.22 3.09c.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.69.63.71.23 1.36.19 1.87.12.57-.08 1.77-.72 2.02-1.42.25-.7.25-1.3.17-1.42-.07-.12-.27-.2-.57-.35z"/><path fill="currentColor" d="M16.05 3.2c-7.1 0-12.87 5.74-12.87 12.82 0 2.26.59 4.47 1.72 6.41L3.07 29l6.75-1.77a12.9 12.9 0 0 0 6.22 1.58h.01c7.1 0 12.87-5.74 12.87-12.82 0-3.43-1.34-6.65-3.77-9.07A12.83 12.83 0 0 0 16.05 3.2zm0 23.45h-.01a10.72 10.72 0 0 1-5.46-1.49l-.39-.23-4 .99 1.07-3.89-.25-.4a10.62 10.62 0 0 1-1.63-5.61c0-5.88 4.79-10.66 10.68-10.66 2.85 0 5.53 1.11 7.54 3.12a10.57 10.57 0 0 1 3.13 7.52c0 5.88-4.79 10.65-10.68 10.65z"/></svg>`;
for(const icon of document.querySelectorAll('.wa-icon')) icon.innerHTML=WHATSAPP_SVG;

function whatsappMessage(prefix){
  const ctx=pageContext();
  return `${prefix}\n\nEmpreendimento: ${ctx.empreendimento}\nPágina: ${location.href}\nOrigem: ${campaignLabel()}`;
}
const waButton=document.querySelector('[data-whatsapp-float]');
if(waButton){
  waButton.addEventListener('click',e=>{
    e.preventDefault();
    const base=document.body.dataset.whatsappMessage||'Olá! Vim pelo site e gostaria de mais informações.';
    const message=whatsappMessage(base);
    trackEvent('whatsapp_click',{origem:'botao_flutuante'});
    window.open(`https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`,'_blank','noopener,noreferrer');
  })
}

// Botão Agendar visita + cadastro no CRM
function createVisitUI(){
  const ctx=pageContext();
  const btn=document.createElement('button');
  btn.type='button';btn.className='schedule-float';btn.innerHTML='<span class="schedule-dot">⌂</span><span><strong>Agendar visita</strong><small>Escolha o melhor horário</small></span>';
  btn.setAttribute('aria-label','Agendar visita');document.body.appendChild(btn);

  const wrap=document.createElement('div');wrap.className='visit-backdrop';wrap.setAttribute('aria-hidden','true');
  wrap.innerHTML=`<div class="visit-modal visit-modal-pro" role="dialog" aria-modal="true" aria-labelledby="visit-title"><button class="visit-close" type="button" aria-label="Fechar">×</button><div class="visit-grid"><div class="visit-copy"><div class="visit-form-view"><p class="eyebrow dark visit-eyebrow">AGENDAR VISITA</p><h2 id="visit-title">Conheça o ${ctx.empreendimento}.</h2><p class="visit-intro">Deixe seus dados e sua preferência de dia e período. O pedido ficará registrado no CRM e a corretora entrará em contato para confirmar os detalhes da visita.</p><div class="visit-interest-note" hidden></div><form class="visit-form"><input class="hp-field" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true"><div class="two-cols"><input required name="nome" placeholder="Nome"><input name="sobrenome" placeholder="Sobrenome"></div><input required name="whatsapp" type="tel" placeholder="WhatsApp"><input name="email" type="email" placeholder="E-mail"><div class="two-cols"><input required name="data_visita" type="date"><select required name="periodo"><option value="">Melhor período</option><option>Manhã</option><option>Tarde</option><option>Fim de tarde</option><option>Quero combinar pelo WhatsApp</option></select></div><label class="consent modal-consent"><input required name="consentimento" type="checkbox" value="1"><span>Autorizo o contato da corretora para tratar deste agendamento. Li a <a href="privacidade.html" target="_blank">Política de Privacidade</a>.</span></label><button class="btn visit-submit" type="submit">Registrar</button><div class="visit-status" aria-live="polite"></div></form></div><div class="visit-success" hidden><span class="success-check">✓</span><p class="eyebrow dark">SOLICITAÇÃO REGISTRADA</p><h2>Visita solicitada!</h2><p>Recebemos sua solicitação para conhecer o <strong>${ctx.empreendimento}</strong>. Karen Caroline entrará em contato para confirmar o melhor horário.</p><div class="success-actions"><button type="button" class="btn success-back">Voltar ao imóvel</button><button type="button" class="btn success-wa">Falar com Karen no WhatsApp</button></div></div></div><div class="visit-visual" aria-hidden="true"><img src="assets/visit-consultora-v543.png" alt=""></div></div></div>`;
  document.body.appendChild(wrap);
  let selectedInterest='';
  const formView=wrap.querySelector('.visit-form-view'),successView=wrap.querySelector('.visit-success'),interestNote=wrap.querySelector('.visit-interest-note');
  const resetViews=()=>{formView.hidden=false;successView.hidden=true;wrap.querySelector('.visit-status').textContent=''};
  const open=(interest='')=>{selectedInterest=interest||'';resetViews();if(selectedInterest){interestNote.hidden=false;interestNote.textContent=`Interesse selecionado: ${selectedInterest}`}else{interestNote.hidden=true;interestNote.textContent=''};wrap.classList.add('open');wrap.setAttribute('aria-hidden','false');document.body.classList.add('modal-open');trackEvent('agendar_visita_open',{origem:selectedInterest?'interesse_planta':'botao_agendar',interesse:selectedInterest})};
  const close=()=>{wrap.classList.remove('open');wrap.setAttribute('aria-hidden','true');document.body.classList.remove('modal-open')};
  window.openVisitModal=open;
  btn.addEventListener('click',()=>open());
  wrap.querySelector('.visit-close').addEventListener('click',close);wrap.addEventListener('click',e=>{if(e.target===wrap)close()});
  wrap.querySelector('.success-back').addEventListener('click',close);
  wrap.querySelector('.success-wa').addEventListener('click',()=>{const message=whatsappMessage(`Olá! Acabei de registrar uma solicitação de visita para ${ctx.empreendimento}${selectedInterest?` (${selectedInterest})`:''}.`);trackEvent('whatsapp_click',{origem:'confirmacao_agendamento'});window.open(`https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`,'_blank','noopener,noreferrer')});
  wrap.querySelector('.visit-form').addEventListener('submit',async e=>{
    e.preventDefault();const form=e.currentTarget;const status=wrap.querySelector('.visit-status');const payload=Object.fromEntries(new FormData(form).entries());
    payload.empreendimento=ctx.empreendimento;payload.origem=selectedInterest?'interesse_planta':'agendar_visita';payload.interesse=selectedInterest?`${selectedInterest} • Visita: ${payload.data_visita} • ${payload.periodo}`:`Visita: ${payload.data_visita} • ${payload.periodo}`;
    try{
      status.textContent='Registrando seu pedido...';
      const data=await saveLead(payload);
      trackEvent('agendar_visita_submit',{lead_id:data.lead_id,origem:payload.origem,interesse:selectedInterest});
      form.reset();formView.hidden=true;successView.hidden=false;
    }catch(err){
      if(err.queued){form.reset();formView.hidden=true;successView.hidden=false;}
      else{status.textContent='⚠ '+err.message}
    }
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&wrap.classList.contains('open'))close()});
}
createVisitUI();

// Seletor e ampliação das plantas dos empreendimentos
const floorTabs=[...document.querySelectorAll('.floorplan-tab')];
const floorPanels=[...document.querySelectorAll('.floorplan-panel')];
if(floorTabs.length){
  floorTabs.forEach(tab=>tab.addEventListener('click',()=>{
    const key=tab.dataset.floorplan;
    floorTabs.forEach(t=>{const active=t===tab;t.classList.toggle('active',active);t.setAttribute('aria-selected',active?'true':'false')});
    floorPanels.forEach(p=>p.classList.toggle('active',p.dataset.floorplanPanel===key));
  }));
}
const floorLightbox=document.getElementById('floorplan-lightbox');
if(floorLightbox){
  const img=floorLightbox.querySelector('img');const title=floorLightbox.querySelector('.floorplan-lightbox-title');
  const openFloor=(el)=>{img.src=el.dataset.floorplanImage;title.textContent=el.dataset.floorplanTitle||'Planta do empreendimento';floorLightbox.classList.add('open');floorLightbox.setAttribute('aria-hidden','false');document.body.classList.add('modal-open')};
  const closeFloor=()=>{floorLightbox.classList.remove('open');floorLightbox.setAttribute('aria-hidden','true');document.body.classList.remove('modal-open');img.src=''};
  document.querySelectorAll('[data-floorplan-image]').forEach(el=>el.addEventListener('click',()=>openFloor(el)));
  floorLightbox.querySelector('.floorplan-lightbox-close').addEventListener('click',closeFloor);
  floorLightbox.addEventListener('click',e=>{if(e.target===floorLightbox)closeFloor()});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&floorLightbox.classList.contains('open'))closeFloor()});
}


// V5.22 — interesse direto por planta integrado ao CRM
for(const info of document.querySelectorAll('.floorplan-info')){
  if(info.querySelector('.floorplan-interest')) continue;
  const label=[info.querySelector('.eyebrow')?.textContent?.trim(),info.querySelector('h3')?.textContent?.trim()].filter(Boolean).join(' • ');
  if(!label) continue;
  const b=document.createElement('button');b.type='button';b.className='floorplan-interest';b.textContent='Tenho interesse nesta planta';
  b.addEventListener('click',()=>{if(window.openVisitModal) window.openVisitModal(label)});
  info.appendChild(b);
}

// Casa Prado — galeria com setas, miniaturas, teclado e swipe
(()=>{document.querySelectorAll('[data-cp-carousel]').forEach(c=>{const main=c.querySelector('.cp-main'),thumbs=[...c.querySelectorAll('.cp-thumb')],counter=c.querySelector('.cp-counter span');if(!main||!thumbs.length)return;let index=0,startX=null;const show=i=>{index=(i+thumbs.length)%thumbs.length;const img=thumbs[index].querySelector('img');main.src=img.src;main.alt=img.alt;if(counter)counter.textContent=index+1;thumbs.forEach((t,n)=>t.classList.toggle('active',n===index));thumbs[index].scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'})};c.querySelector('.cp-prev')?.addEventListener('click',()=>show(index-1));c.querySelector('.cp-next')?.addEventListener('click',()=>show(index+1));thumbs.forEach((t,i)=>t.addEventListener('click',()=>show(i)));document.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')show(index-1);if(e.key==='ArrowRight')show(index+1)});main.addEventListener('touchstart',e=>startX=e.touches[0].clientX,{passive:true});main.addEventListener('touchend',e=>{if(startX===null)return;const dx=e.changedTouches[0].clientX-startX;if(Math.abs(dx)>45)show(index+(dx<0?1:-1));startX=null},{passive:true});show(0)})})();
