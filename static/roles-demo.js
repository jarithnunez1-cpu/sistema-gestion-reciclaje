(() => {
  const profiles = {
    'demo@verdeciclo.com': { password:'reciclaje2026', type:'admin' },
    'reciclador@verdeciclo.com': { password:'recolector2026', type:'recolector' },
    'empresa@verdeciclo.com': { password:'empresa2026', type:'empresa' }
  };
  const el = (selector) => document.querySelector(selector);
  const style = document.createElement('style');
  style.textContent =     'body.demo-recolector .sidebar{background:linear-gradient(180deg,#244d70,#142f49)}' +
    'body.demo-recolector .nav-item.active{box-shadow:inset 3px 0 #8dd8ff}' +
    'body.demo-recolector .nav-item.active .nav-icon{color:#8dd8ff}' +
    'body.demo-empresa .sidebar{background:linear-gradient(180deg,#654a78,#392d4d)}' +
    'body.demo-empresa .nav-item.active{box-shadow:inset 3px 0 #edc5ff}' +
    'body.demo-empresa .nav-item.active .nav-icon{color:#edc5ff}' +
    '.demo-credentials{display:grid;gap:8px;margin:18px 0;padding:13px;border:1px solid #e4ece6;border-radius:13px;background:#f7faf7;font-size:11px;color:#557067;line-height:1.6}' +
    '.demo-credentials strong{color:#234b3d}.demo-credentials span{display:block}' +
    '.demo-readonly{padding:11px 14px;margin:0 0 18px;border-radius:11px;background:#eff5eb;color:#55705a;font-size:11px}' +
    '.demo-form{max-width:680px;background:#fff;border:1px solid #e5ebe7;border-radius:16px;padding:22px;box-shadow:0 22px 65px #113b2a12}' +
    '.demo-form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:15px 0}' +
    '.demo-form label{display:grid;gap:7px;font-size:11px;color:#52655b}.demo-form input,.demo-form select{height:42px;border:1px solid #dfe8e2;border-radius:10px;padding:0 11px;background:#fff}' +
    '.demo-report{display:flex;align-items:center;justify-content:space-between;gap:14px;margin:18px 0;padding:18px;background:#fff;border:1px solid #e5ebe7;border-radius:14px}' +
    '@media(max-width:620px){.demo-form-grid{grid-template-columns:1fr}.demo-report{align-items:flex-start;flex-direction:column}}';
  document.head.append(style);

  const credentials = document.createElement('div');
  credentials.className = 'demo-credentials';
  credentials.innerHTML = '<strong>Accesos de demostración · solo lectura</strong>' +
    '<span>Administrador: <b>demo@verdeciclo.com</b> / <b>reciclaje2026</b></span>' +
    '<span>Recolector: <b>reciclador@verdeciclo.com</b> / <b>recolector2026</b></span>' +
    '<span>Empresa afiliada: <b>empresa@verdeciclo.com</b> / <b>empresa2026</b></span>';
  const form = el('#login-form');
  if (form) form.before(credentials);

  const pickups = [
    ['25 sep 2026','EcoAndes','Plástico PET','128 kg','Recibida'],
    ['23 sep 2026','EcoAndes','Cartón','74 kg','Recibida'],
    ['19 sep 2026','EcoAndes','Vidrio','52 kg','Recibida'],
    ['16 sep 2026','EcoAndes','Aluminio','31 kg','Recibida']
  ];
  const esc = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const heading = (k,title,sub,action='') => '<div class="page-head"><div><div class="kicker">'+k+'</div><h1>'+title+'</h1><p>'+sub+'</p></div><div class="head-actions">'+action+'</div></div>';
  const rows = data => data.map(row=>'<tr>'+row.map((v,i)=>'<td>'+(i===0?'<strong>'+esc(v)+'</strong>':esc(v))+'</td>').join('')+'</tr>').join('');
  const table = (title,headers,data) => '<div class="table-panel"><div class="table-top"><h3>'+title+'</h3><span>Ejemplo · no se guarda</span></div><div class="table-wrap"><table><thead><tr>'+headers.map(x=>'<th>'+x+'</th>').join('')+'</tr></thead><tbody>'+rows(data)+'</tbody></table></div></div>';
  const readOnly = '<div class="demo-readonly"><b>Modo demostración.</b> Información ficticia; las acciones no modifican registros oficiales.</div>';
  function enter(type){
    document.body.classList.remove('demo-recolector','demo-empresa');
    document.body.classList.add('demo-'+type);
    el('#login').hidden=true; el('#app').hidden=false;
    const isCompany=type==='empresa';
    const name=isCompany?'EcoAndes':'María Rojas';
    el('#user-name').textContent=isCompany?'EcoAndes · empresa':'María Rojas';
    el('#user-role').textContent=isCompany?'Empresa afiliada · demo':'Recolectora · demo';
    el('#avatar').textContent=isCompany?'E':'M'; el('#top-avatar').textContent=isCompany?'E':'M';
    el('#today').textContent=new Intl.DateTimeFormat('es-BO',{weekday:'short',day:'numeric',month:'short'}).format(new Date());
    const links=isCompany?[
      ['inicio','◫','Resumen de empresa'],['recepciones','↗','Recepciones'],['informe','▧','Informe mensual']
    ]:[['inicio','◫','Mi resumen'],['nuevo','＋','Registrar recolección'],['historial','↗','Mis recolecciones']];
    el('#nav').innerHTML='<div class="nav-group">PANEL DEMO</div>'+links.map(([r,i,n])=>'<a class="nav-item" href="#'+r+'" data-role-route="'+r+'"><span class="nav-icon">'+i+'</span><span>'+n+'</span></a>').join('');
    el('#nav').querySelectorAll('[data-role-route]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();show(type,a.dataset.roleRoute)}));
    el('#logout').onclick=()=>{document.body.classList.remove('demo-recolector','demo-empresa');el('#app').hidden=true;el('#login').hidden=false;form.reset()};
    show(type,'inicio');
  }
  function show(type,route){
    const company=type==='empresa';
    const routes=company?{inicio:'Resumen de empresa',recepciones:'Recepciones',informe:'Informe mensual'}:{inicio:'Mi resumen',nuevo:'Registrar recolección',historial:'Mis recolecciones'};
    el('#crumb').textContent=routes[route]||routes.inicio;
    el('#nav').querySelectorAll('[data-role-route]').forEach(a=>a.classList.toggle('active',a.dataset.roleRoute===route));
    const view=el('#view');
    if(company){
      if(route==='recepciones') view.innerHTML=heading('EMPRESA AFILIADA','Recepciones','Material recibido por EcoAndes.')+readOnly+table('Recepciones recientes',['Fecha','Recolector','Material','Cantidad','Estado'],[['25 sep 2026','María Rojas','Plástico PET','128 kg','Recibida'],['23 sep 2026','Luis Quispe','Cartón','86 kg','Recibida'],['20 sep 2026','Ana Flores','Vidrio','63 kg','Recibida'],['18 sep 2026','María Rojas','Aluminio','41 kg','Recibida']]);
      else if(route==='informe') view.innerHTML=heading('ANÁLISIS','Informe mensual','Resumen de septiembre de 2026 para EcoAndes.')+readOnly+'<div class="demo-report"><div><div class="kicker">TOTAL RECIBIDO</div><h2>482 kg</h2><p>12 recolecciones · 4 tipos de material</p></div><button class="button primary" id="download-report">Descargar informe CSV</button></div>'+table('Detalle mensual',['Material','Recolecciones','Cantidad'],[['Plástico PET','5','196 kg'],['Cartón','3','124 kg'],['Vidrio','2','91 kg'],['Aluminio','2','71 kg']]);
      else view.innerHTML=heading('PANEL EMPRESA AFILIADA','EcoAndes','Consulta tus recepciones y el resumen de materiales.')+readOnly+'<div class="grid stats-grid">'+[['Material recibido','482 kg','En septiembre','↗'],['Recolecciones','12','Este mes','▤'],['Materiales','4','Con actividad','◈'],['Recolectores','3','Personas asignadas','♧']].map(x=>'<article class="stat-card"><span class="stat-label">'+x[0]+'</span><span class="stat-icon">'+x[3]+'</span><div class="stat-value">'+x[1]+'</div><div class="stat-note">'+x[2]+'</div></article>').join('')+'</div>'+table('Últimas recepciones',['Fecha','Recolector','Material','Cantidad','Estado'],[['25 sep 2026','María Rojas','Plástico PET','128 kg','Recibida'],['23 sep 2026','Luis Quispe','Cartón','86 kg','Recibida'],['20 sep 2026','Ana Flores','Vidrio','63 kg','Recibida']]);
      const button=el('#download-report'); if(button) button.onclick=()=>{const csv='Material,Recolecciones,Cantidad\nPlastico PET,5,196 kg\nCarton,3,124 kg\nVidrio,2,91 kg\nAluminio,2,71 kg\nTOTAL,12,482 kg';const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));a.download='informe-demo-ecoandes-septiembre-2026.csv';a.click();URL.revokeObjectURL(a.href)};
    } else if(route==='nuevo'){
      view.innerHTML=heading('MI ACTIVIDAD','Registrar recolección','Completa los datos para simular un nuevo registro.')+readOnly+'<form class="demo-form" id="demo-pickup"><div class="demo-form-grid"><label>Fecha<input name="fecha" type="date" value="2026-09-25" required></label><label>Cantidad (kg)<input name="cantidad" type="number" min="0.1" step="0.1" placeholder="Ej. 25" required></label><label>Empresa afiliada<select name="empresa"><option>EcoAndes</option><option>ReciCentro</option><option>Circular Sur</option></select></label><label>Material<select name="material"><option>Plástico PET</option><option>Cartón</option><option>Vidrio</option><option>Aluminio</option></select></label></div><button class="button primary">Simular registro</button><p id="demo-result" class="demo-readonly" hidden></p></form>';
      el('#demo-pickup').onsubmit=e=>{e.preventDefault();const d=new FormData(e.target);const out=el('#demo-result');out.hidden=false;out.textContent='Registro de ejemplo preparado: '+d.get('cantidad')+' kg de '+d.get('material')+' para '+d.get('empresa')+'. No se guardó en el sistema.'};
    } else if(route==='historial') view.innerHTML=heading('MI ACTIVIDAD','Mis recolecciones','Registros de ejemplo asociados a María Rojas.')+readOnly+table('Historial de recolecciones',['Fecha','Empresa','Material','Cantidad','Estado'],pickups);
    else view.innerHTML=heading('PANEL RECOLECTOR','Hola, María','Tu actividad de recolección en septiembre de 2026.')+readOnly+'<div class="grid stats-grid">'+[['Recolectado','286 kg','Este mes','↗'],['Recolecciones','8','Registros de ejemplo','▤'],['Materiales','3','Tipos recolectados','◈'],['Empresas','2','Puntos atendidos','◉']].map(x=>'<article class="stat-card"><span class="stat-label">'+x[0]+'</span><span class="stat-icon">'+x[3]+'</span><div class="stat-value">'+x[1]+'</div><div class="stat-note">'+x[2]+'</div></article>').join('')+'</div>'+table('Actividad reciente',['Fecha','Empresa','Material','Cantidad','Estado'],pickups.slice(0,3));
  }
  document.addEventListener('submit',event=>{
    if(event.target?.id!=='login-form') return;
    const data=new FormData(event.target),email=String(data.get('correo')||'').trim().toLowerCase(),password=String(data.get('contrasena')||''),profile=profiles[email];
    if(!profile||profile.password!==password||profile.type==='admin') return;
    event.preventDefault(); event.stopImmediatePropagation();
    const error=el('#login-error'); error.hidden=true; enter(profile.type);
  },true);
})();
