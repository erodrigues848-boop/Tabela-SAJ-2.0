/* Painel SAJ: manchetes com imagens públicas de RSS/OG e filtros independentes. */
(()=>{
  'use strict';
  const cards=document.getElementById('news-list');
  if(!cards)return;
  const msg=document.getElementById('live-news-status');
  const health=document.getElementById('feed-health');
  const updated=document.getElementById('news-updated');
  const typeSelect=document.getElementById('news-kind');
  const reload=document.getElementById('news-reload');
  const sectorButtons=[...document.querySelectorAll('.news-filter[data-sector]')];
  const globalSearch=document.getElementById('q');
  const sectorNames={1:'Telecom',2:'Ferrovias',3:'Rodovias',4:'Aeroportos',5:'Serviços aéreos',6:'Energia',7:'Petróleo',8:'Gás · transporte',9:'Gás · outras atividades'};
  let stories=[];
  let allLoaded=false;

  const str=v=>String(v??'').trim();
  const normal=v=>str(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const https=u=>{try{const v=new URL(u);return v.protocol==='https:'?v.href:null;}catch{return null;}};
  const dmy=d=>{
    if(!d)return 'Sem data';const date=new Date(d);
    return Number.isNaN(date.getTime())?'Sem data':new Intl.DateTimeFormat('pt-BR',{day:'2-digit',month:'short',year:'numeric',timeZone:'America/Sao_Paulo'}).format(date);
  };
  function make(parent,tag,cls,txt){
    const n=document.createElement(tag);if(cls)n.className=cls;
    if(txt!==undefined)n.textContent=str(txt);
    parent.appendChild(n);return n;
  }
  function anchor(parent,cls,title,url){
    const a=make(parent,'a',cls,title);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;
  }
  function brandName(fonte){
    return str(fonte).replace(/^Diário Oficial da União.*$/,'DOU').replace(/^Agência iNFRA$/,'iNFRA').slice(0,24)||'NOTÍCIA';
  }
  function searchLabel(story){
    return normal([story.titulo,story.fonte,story.categoria,story.descricao, ...(story.temas||[]),...(story.setores||[]).map(i=>sectorNames[i]||'')].join(' '));
  }
  function createStory(story){
    const url=https(story.url);if(!url||!story.titulo)return null;
    const sectors=(Array.isArray(story.setores)?story.setores:[]).map(Number).filter(i=>i>=1&&i<=9);
    if(!sectors.length)return null;
    const card=make(cards,'article','news-card news-card-rich');
    card.dataset.setores=sectors.join(',');card.dataset.sector=String(sectors[0]||0);
    card.dataset.status=str(story.categoria||'Notícia setorial');
    card.dataset.search=searchLabel(story);
    const media=anchor(card,'news-media','',url);
    media.setAttribute('aria-label',`Abrir matéria: ${story.titulo}`);
    const image=https(story.imagem);
    if(image){
      const img=make(media,'img','news-image');
      img.src=image;img.alt='';img.loading='lazy';img.decoding='async';img.referrerPolicy='no-referrer';
      img.onerror=()=>{img.remove();media.classList.add('news-media-fallback');make(media,'span','news-media-source',brandName(story.fonte));};
    }else{
      media.classList.add('news-media-fallback');
      make(media,'span','news-media-source',brandName(story.fonte));
    }
    make(media,'span','news-media-corner','VER MATÉRIA ↗');
    const body=make(card,'div','news-body');
    const meta=make(body,'div','news-meta');
    make(meta,'span','news-status',story.categoria||'Notícia setorial');
    const date=make(meta,'time','',dmy(story.publicado_em));
    if(story.publicado_em)date.dateTime=story.publicado_em;
    const heading=make(body,'h3','news-headline');
    anchor(heading,'news-title-link',story.titulo,url);
    if(story.descricao){make(body,'p','news-preview',str(story.descricao).slice(0,140));}
    const badges=make(body,'div','news-sector-tags');
    if(sectors.length){for(const i of sectors.slice(0,3)) make(badges,'span','news-sector-tag',sectorNames[i]);}
    else make(badges,'span','news-sector-tag news-sector-general','Geral · sem setor identificado');
    const bottom=make(body,'div','news-source');
    make(bottom,'span','news-publisher',story.fonte||'Fonte pública');
    anchor(bottom,'news-open','Ler notícia ↗',url);
    return card;
  }
  function activeSector(){
    return Number(sectorButtons.find(b=>b.classList.contains('active'))?.dataset.sector||0);
  }
  // Busca dedicada às notícias, independente da pesquisa na tabela jurídica.
  const tools=document.querySelector('.live-news-tools');
  let dedicated=document.getElementById('news-query');
  if(tools && !dedicated){
    const searchBox=make(tools,'label','news-search-wrap');
    make(searchBox,'span','sr-only','Pesquisar somente nas notícias');
    dedicated=make(searchBox,'input','news-search');
    dedicated.type='search';dedicated.id='news-query';dedicated.placeholder='Pesquisar notícias…';
    dedicated.autocomplete='off';
    tools.insertBefore(searchBox,tools.querySelector('.news-tool-right'));
  }
  const emptyNotice=make(cards,'div','live-news-empty news-filter-empty');
  emptyNotice.hidden=true;
  const filterCounter=document.createElement('p');filterCounter.id='news-visible-count';
  filterCounter.className='news-visible-count';cards.after(filterCounter);
  function filterCards(){
    if(!allLoaded)return 0;
    const sector=activeSector();
    const term=normal(dedicated?.value);
    const global=normal(globalSearch?.value);
    const kind=str(typeSelect?.value);
    let shown=0;
    cards.querySelectorAll('article.news-card').forEach(card=>{
      const sectors=(card.dataset.setores||'').split(',').filter(Boolean);
      const okay=(!sector||sectors.includes(String(sector))) &&
        (!kind||card.dataset.status===kind) &&
        (!term||card.dataset.search.includes(term)) &&
        (!global||card.dataset.search.includes(global));
      card.classList.toggle('hidden',!okay);
      if(okay)shown++;
    });
    const total=cards.querySelectorAll('article.news-card').length;
    filterCounter.textContent=`${shown} notícia${shown===1?'':'s'} exibida${shown===1?'':'s'} de ${total}`;
    const topCount=document.getElementById('search-count');
    if(topCount)topCount.textContent=topCount.textContent.replace(/\d+\s+(?:atualizações|notícias)/i,`${shown} notícias`);
    if(total && !shown){
      emptyNotice.textContent='Nenhuma notícia corresponde aos filtros selecionados. Experimente “Todos” ou limpe a pesquisa.';
      emptyNotice.hidden=false;
    }else{emptyNotice.hidden=true;}
    return shown;
  }
  function render(data){
    stories=(Array.isArray(data.noticias)?data.noticias:[]).filter(x=>x.escopo==='normativo' && Array.isArray(x.setores) && x.setores.length>0);
    cards.replaceChildren();
    cards.appendChild(emptyNotice);emptyNotice.hidden=true;
    const valid=stories.map(createStory).filter(Boolean);
    const collected=dmy(data.atualizado_em);
    if(updated)updated.textContent=`${valid.length} notícias · ${collected}`;
    if(msg){
      msg.classList.toggle('warning',valid.length===0);
      msg.textContent=valid.length?`Notícias coletadas em ${collected}`:'Nenhuma atualização normativa aderente aos temas da tabela nesta coleta';
    }
    if(health){
      const bad=(Array.isArray(data.fontes)?data.fontes:[]).filter(f=>f.situacao!=='ok');
      health.textContent=bad.length
        ? `Algumas fontes não responderam: ${bad.map(f=>f.nome).join(', ')}. A cobertura pode estar incompleta.`
        : 'Prévia por imagem fornecida na fonte pública (RSS ou metadados); ausência de imagem não significa falha. Verifique o ato oficial antes de atualizar a tabela.';
    }
    allLoaded=true;
    // Mantém também o contador de pesquisa jurídica original atualizado.
    window.SAJNewsRefresh?.();
    filterCards();
    if(!valid.length){
      emptyNotice.textContent='Nenhuma publicação normativa diretamente relacionada à tabela foi identificada nesta coleta. Isso não significa ausência de mudanças; consulte também as fontes oficiais.';
      emptyNotice.hidden=false;
    }
  }
  async function reloadNews(){
    if(msg)msg.textContent='Lendo notícias publicadas…';
    try{
      const r=await fetch(`data/news.json?t=${Date.now()}`,{cache:'no-store'});
      if(!r.ok)throw new Error(`HTTP ${r.status}`);
      const json=await r.json();
      if(!json || !Array.isArray(json.noticias))throw new Error('Formato inesperado de notícias');
      render(json);
    }catch(e){
      cards.replaceChildren(emptyNotice);
      emptyNotice.hidden=false;
      emptyNotice.textContent='Não foi possível ler data/news.json. Confirme a publicação do site e o arquivo no repositório.';
      filterCounter.textContent='';
      if(msg){msg.textContent='Erro ao carregar manchetes';msg.classList.add('warning');}
      if(health)health.textContent=`Falha de leitura: ${e.message}`;
    }
  }
  // Os botões já alteram a classe "active" no HTML original; aqui atualizamos os cartões.
  sectorButtons.forEach(b=>b.addEventListener('click',filterCards));
  typeSelect?.addEventListener('change',filterCards);
  dedicated?.addEventListener('input',filterCards);
  globalSearch?.addEventListener('input',filterCards);
  globalSearch?.addEventListener('search',filterCards);
  document.getElementById('reset')?.addEventListener('click',()=>{if(dedicated)dedicated.value='';filterCards();});
  reload?.addEventListener('click',reloadNews);
  reloadNews();
})();

// Evita marcas desenhadas/falsificadas quando imagens externas não carregam.
document.querySelectorAll('.agency-logo img').forEach(img=>{img.addEventListener('error',()=>{if(img.dataset.backup&&!img.dataset.backupTried){img.dataset.backupTried='1';img.src=img.dataset.backup;return;}img.classList.add('failed');});});
