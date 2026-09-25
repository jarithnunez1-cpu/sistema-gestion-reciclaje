(() => {
  const DEMO_EMAIL = 'demo@verdeciclo.com';
  const DEMO_PASSWORD = 'reciclaje2026';
  const collections = [
    ['25 sep 2026', 'María Rojas', 'EcoAndes', 'Plástico PET', '128 kg'],
    ['24 sep 2026', 'Luis Quispe', 'ReciCentro', 'Cartón', '86 kg'],
    ['23 sep 2026', 'Ana Flores', 'EcoAndes', 'Aluminio', '42 kg'],
    ['22 sep 2026', 'Carlos Mendoza', 'Circular Sur', 'Vidrio', '113 kg'],
    ['21 sep 2026', 'María Rojas', 'ReciCentro', 'Plástico PET', '74 kg'],
  ];
  const navGroups = [
    ['RESUMEN', [['dashboard', '◫', 'Dashboard'], ['indicadores', '⌁', 'Indicadores']]],
    ['GESTIÓN', [['recolectores', '♧', 'Recicladores'], ['empresas', '▤', 'Empresas afiliadas'], ['materiales', '◈', 'Tipos de material'], ['recolecciones', '↗', 'Recolecciones']]],
    ['ANÁLISIS', [['reportes', '▧', 'Informes mensuales']]],
  ];
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const rows = items => items.map(item => `<tr>${item.map((v, i) => `<td>${i === 0 ? `<strong>${esc(v)}</strong>` : esc(v)}</td>`).join('')}</tr>`).join('');
  const heading = (eyebrow, title, subtitle, suffix='') => `<div class="page-head"><div><div class="kicker">${eyebrow}</div><h1>${title}</h1><p>${subtitle}</p></div><div class="head-actions">${suffix}</div></div>`;
  const table = (headers, body) => `<div class="table-panel"><div class="table-top"><h3>${headers[0]}</h3><span>Datos de demostración · solo lectura</span></div><div class="table-wrap"><table><thead><tr>${headers.slice(1).map(x=>`<th>${x}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div></div>`;

  function dashboard() {
    return `${heading('VISTA GENERAL', 'Dashboard', 'Una vista rápida del impacto de VerdeCiclo.', '<span class="role-tag">MODO DEMO · SOLO LECTURA</span>')}
      <div class="notice demo-note"><strong>Espacio de demostración.</strong> Explora el menú y los indicadores; estos registros son ejemplos y no se guardan.</div>
      <div class="grid stats-grid">
        <article class="stat-card"><span class="stat-label">Total reciclado</span><span class="stat-icon">↗</span><div class="stat-value">1.284 <small>kg</small></div><div class="stat-note">Este mes · +12% frente al anterior</div></article>
        <article class="stat-card"><span class="stat-label">Recolecciones</span><span class="stat-icon">▤</span><div class="stat-value">34</div><div class="stat-note">Registros de este mes</div></article>
        <article class="stat-card"><span class="stat-label">Recicladores</span><span class="stat-icon">♧</span><div class="stat-value">12</div><div class="stat-note">Personas en el equipo</div></article>
        <article class="stat-card"><span class="stat-label">Empresas aliadas</span><span class="stat-icon">◉</span><div class="stat-value">6</div><div class="stat-note">Puntos de recolección</div></article>
      </div>
      <div class="grid dashboard-grid"><section class="panel"><div class="panel-head"><div><h3>Actividad mensual</h3><p>Kilogramos recuperados durante el año</p></div><span class="legend"><i></i> kg</span></div><div class="chart">${[['Ene',45],['Feb',60],['Mar',52],['Abr',72],['May',64],['Jun',83],['Jul',68],['Ago',94],['Sep',78]].map(([m,h],i)=>`<div class="bar-col"><div class="bar ${i===7?'current':''}" style="height:${h}%"></div><span class="bar-label">${m}</span></div>`).join('')}</div></section>
      <section class="panel"><div class="panel-head"><div><h3>Materiales recuperados</h3><p>Distribución del mes</p></div></div><div class="material-list">${[['Plástico PET','42%','539 kg'],['Cartón','27%','347 kg'],['Vidrio','18%','231 kg'],['Aluminio','13%','167 kg']].map(([n,p,v])=>`<div class="material-row"><span>${n}</span><strong>${p} · ${v}</strong><div class="progress"><span style="width:${p}"></span></div></div>`).join('')}</div></section></div>
      ${table(['Actividad reciente','Reciclador','Empresa','Material','Cantidad'], rows(collections.slice(0,4)) )}`;
  }

  function render(route='dashboard') {
    const titles = {dashboard:'Dashboard',indicadores:'Indicadores',recolectores:'Recicladores',empresas:'Empresas afiliadas',materiales:'Tipos de material',recolecciones:'Recolecciones',reportes:'Informes mensuales'};
    document.querySelector('#crumb').textContent = titles[route] || 'Dashboard';
    document.querySelectorAll('#nav [data-demo-route]').forEach(link=>link.classList.toggle('active',link.dataset.demoRoute===route));
    const view = document.querySelector('#view');
    if (route === 'dashboard' || route === 'indicadores') view.innerHTML = dashboard();
    else if (route === 'recolectores') view.innerHTML = `${heading('GESTIÓN','Recicladores','Personas que hacen posible la recuperación de materiales.')} ${table(['Equipo de reciclaje','Correo','Empresa','Registros','Estado'], rows([['María Rojas','maria@ejemplo.com','EcoAndes','18','Activo'],['Luis Quispe','luis@ejemplo.com','ReciCentro','14','Activo'],['Ana Flores','ana@ejemplo.com','Circular Sur','12','Activo'],['Carlos Mendoza','carlos@ejemplo.com','EcoAndes','9','Activo']]))}`;
    else if (route === 'empresas') view.innerHTML = `${heading('GESTIÓN','Empresas afiliadas','Aliados que reciben y clasifican material reciclable.')} ${table(['Red de aliados','Dirección','Contacto','Estado'], rows([['EcoAndes','La Paz · Sopocachi','+591 700 12345','Activa'],['ReciCentro','La Paz · Miraflores','+591 700 23456','Activa'],['Circular Sur','El Alto · Villa Adela','+591 700 34567','Activa'],['Verde Futuro','La Paz · Calacoto','+591 700 45678','Activa']]))}`;
    else if (route === 'materiales') view.innerHTML = `${heading('GESTIÓN','Tipos de material','Clasificación de lo recolectado y sus metas.')} ${table(['Materiales','Meta de recuperación','Cantidad del mes','Tendencia'], rows([['Plástico PET','40%','539 kg','↗ 12%'],['Cartón','30%','347 kg','↗ 8%'],['Vidrio','20%','231 kg','↗ 5%'],['Aluminio','10%','167 kg','↗ 3%']]))}`;
    else if (route === 'recolecciones') view.innerHTML = `${heading('REGISTRO','Recolecciones','Actividad reciente registrada por el equipo.')} ${table(['Últimos registros','Reciclador','Empresa','Material','Cantidad'], rows(collections))}`;
    else view.innerHTML = `${heading('ANÁLISIS','Informes mensuales','Resumen del impacto por empresa aliada.')} ${table(['Resumen de septiembre','Empresa','Recolecciones','Total recuperado'], rows([['EcoAndes','EcoAndes','12','482 kg'],['ReciCentro','ReciCentro','9','356 kg'],['Circular Sur','Circular Sur','7','271 kg'],['Verde Futuro','Verde Futuro','6','175 kg']]))}`;
    view.querySelectorAll('.table-top span').forEach(el=>{el.textContent='Datos de demostración · solo lectura'});
  }

  function enterDemo() {
    document.querySelector('#login').hidden = true;
    document.querySelector('#app').hidden = false;
    document.querySelector('#user-name').textContent = 'Usuario Demo';
    document.querySelector('#user-role').textContent = 'Demo · solo lectura';
    document.querySelector('#avatar').textContent = 'D';
    document.querySelector('#top-avatar').textContent = 'D';
    document.querySelector('#today').textContent = new Intl.DateTimeFormat('es-BO',{weekday:'short',day:'numeric',month:'short'}).format(new Date());
    document.querySelector('#nav').innerHTML = navGroups.map(([group,items])=>`<div class="nav-group">${group}</div>${items.map(([key,icon,label])=>`<a class="nav-item" href="#${key}" data-demo-route="${key}"><span class="nav-icon">${icon}</span><span>${label}</span></a>`).join('')}`).join('');
    document.querySelectorAll('#nav [data-demo-route]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();render(link.dataset.demoRoute)}));
    document.querySelector('#logout').onclick=()=>{document.querySelector('#app').hidden=true;document.querySelector('#login').hidden=false;document.querySelector('#login-form').reset()};
    render();
  }

  document.addEventListener('submit', event => {
    if (event.target?.id !== 'login-form') return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const form = new FormData(event.target);
    const email = String(form.get('correo')||'').trim().toLowerCase();
    const password = String(form.get('contrasena')||'');
    const error = document.querySelector('#login-error');
    if (email === DEMO_EMAIL && password === DEMO_PASSWORD) { error.hidden=true; enterDemo(); }
    else { error.textContent='Para entrar a la demo usa los datos que aparecen arriba.'; error.hidden=false; }
  }, true);
})();
