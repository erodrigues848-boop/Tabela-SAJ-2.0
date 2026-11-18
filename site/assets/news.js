/* Renderizador seguro: somente campos de texto e links HTTPS, sem injetar HTML remoto. */
(()=>{
  'use strict';
  const cards=document.getElementById('news-list');
  const msg=document.getElementById('live-news-status');
  const health=document.getElementById('feed-health');
  const updated=document.getElementById('news-updated');
  const kind=document.getElementById('news-kind');
  const reload=document.getElementById('news-reload');
  if(!cards)return;
  const select=document.getElementById('news-kind');
  window.SAJNewsPredicate=(el)=>!select?.value || el.dataset.status===select.value;
  const plain=(v)=>String(v??'').trim();
  const norm=(v)=>plain(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const friendlyDate=(str)=>{
    if(!str)return 'Data não informada';
    const dt=new Date(str);
    return isNaN(dt.getTime())?'Data não informada':new Intl.DateTimeFormat('pt-BR',{day:'2-digit',month:'2-digit',year:'numeric',timeZone:'America/Sao_Paulo'}).format(dt);
  };
  const linkURL=(str)=>{
    try {const u=new URL(str);return u.protocol==='https:'?u.href:null;}catch{return null;}
  };
  function add(parent,tag,klass,value){
    const el=document.createElement(tag);if(klass)el.className=klass;
    if(value!==undefined)el.textContent=plain(value);
    parent.appendChild(el);return el;
  }
  function empty(text){cards.replaceChildren();add(cards,'div','live-news-empty',text);}
  function render(data){
    const news=Array.isArray(data.noticias)?data.noticias:[];
    cards.replaceChildren();
    for(const item of news){
      const url=linkURL(item.url);if(!url||!item.titulo)continue;
      const sections=Array.isArray(item.setores)?item.setores.map(Number).filter(Number.isFinite):[];
      const card=add(cards,'article','news-card');
      // For a multi-setor article, allow it in each matching filter.
      card.dataset.setores=sections.join(',');
      card.dataset.sector=String(sections[0]||0);
      card.dataset.status=plain(item.categoria);
      card.dataset.search=norm([item.titulo,item.fonte,item.categoria,...(item.temas||[]),...sections].join(' '));
      const meta=add(card,'div','news-meta');
      add(meta,'span','news-status',item.categoria||'Notícia');
      add(meta,'time','',friendlyDate(item.publicado_em));
      add(card,'h3','',item.titulo);
      add(card,'p','news-area','Possível tema na tabela: '+(Array.isArray(item.temas)?item.temas.join(' · '):'Acompanhamento geral'));
      if(item.canal?.includes('Google')) add(card,'p','news-tipo','Fonte encontrada em agregador; confirme a publicação original.');
      add(card,'p','news-impact','Notícia para triagem jurídica; não comprova vigência.');
      const row=add(card,'div','news-source');
      add(row,'span','',item.fonte||'Fonte pública');
      const a=add(row,'a','', 'Abrir publicação ↗');
      a.href=url;a.target='_blank';a.rel='noopener noreferrer';
    }
    const dt=data.atualizado_em ? friendlyDate(data.atualizado_em) : 'Sem atualização';
    if(updated)updated.textContent=`${news.length} notícias • coleta: ${dt}`;
    if(!news.length){
      empty('Ainda não há manchetes disponíveis. Se o site acabou de ser publicado, consulte Actions → Atualizar notícias e publicar Tabela SAJ → Run workflow.');
      msg?.classList.add('warning');
      if(msg)msg.textContent='Aguardando coleta de notícias';
    } else {
      msg?.classList.remove('warning');
      if(msg)msg.textContent=`Coleta concluída em ${dt}.`;
    }
    if(health){
      const issues=(Array.isArray(data.fontes)?data.fontes:[]).filter(x=>x.situacao!=='ok');
      health.textContent = issues.length
        ? `Fontes temporariamente indisponíveis: ${issues.map(x=>x.nome).join(', ')}. O painel pode não incluir todas as novidades.`
        : 'Monitoramento por RSS e fontes públicas. As notícias são metadados; a vigência jurídica exige conferência oficial.';
    }
    if(window.SAJNewsRefresh)window.SAJNewsRefresh();
  }
  async function load(){
    if(msg)msg.textContent='Consultando últimas notícias publicadas…';
    try{
      const response=await fetch(`data/news.json?v=${Date.now()}`,{cache:'no-store'});
      if(!response.ok)throw new Error('HTTP '+response.status);
      const data=await response.json();
      if(!data || !Array.isArray(data.noticias))throw new Error('Formato JSON inesperado');
      render(data);
    }catch(err){
      empty('Não foi possível carregar o arquivo de notícias. Confira se o site foi publicado no GitHub Pages e execute novamente o workflow.');
      msg?.classList.add('warning');
      if(msg)msg.textContent='Falha na leitura do feed';
      if(health)health.textContent=`Erro de leitura: ${err.message}`;
    }
  }
  select?.addEventListener('change',()=>window.SAJNewsRefresh?.());
  reload?.addEventListener('click',load);
  load();
})();
