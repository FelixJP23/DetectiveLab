

document.addEventListener('DOMContentLoaded', () => {

 
  let autores = [];
  try { autores = JSON.parse(document.body.dataset.autores || '[]'); } catch (e) { autores = []; }

  const porId = {};
  autores.forEach(a => { porId[a.id] = a; });

  const conteudo   = document.getElementById('conteudo-autor');
  const vazio      = document.getElementById('mural-vazio');
  const fotoEl     = document.getElementById('autor-foto');
  const nomeEl     = document.getElementById('autor-nome');
  const bioEl      = document.getElementById('autor-bio');
  const tradLabel  = document.getElementById('autor-tradicao-label');
  const obrasWrap  = document.getElementById('autor-obras');

  const TRAD_LABEL = { 'americana': 'TRADIÇÃO AMERICANA', 'japonesa': 'TRADIÇÃO JAPONESA' };

  // Se nao ha autores, mostra estado vazio
  if (autores.length === 0) {
    conteudo.classList.add('hidden');
    vazio.classList.remove('hidden');
    vazio.classList.add('flex');
    return;
  }


  function renderAutor(autor) {
    if (!autor) return;

    nomeEl.textContent = autor.nome;
    bioEl.textContent  = autor.biografia;
    tradLabel.textContent = TRAD_LABEL[autor.tradicao] || 'DOSSIE';

  
    if (autor.foto) {
      fotoEl.src = autor.foto;
      fotoEl.style.display = '';
    } else {
      fotoEl.removeAttribute('src');
      fotoEl.style.display = 'none';
    }

    // Obras
    obrasWrap.innerHTML = '';
    if (autor.obras && autor.obras.length > 0) {
      autor.obras.forEach(o => {
        const card = document.createElement('div');
        card.className = 'obra-card group';
        let thumbInner;
        if (o.capa) {
         
          thumbInner = `<img class="obra-capa-img" src="${o.capa}" alt="${o.titulo}">`;
        } else {
        
          thumbInner = `<span class="material-symbols-outlined">auto_stories</span>`;
        }
        card.innerHTML = `
          <div class="obra-thumb">
            ${thumbInner}
            <div class="obra-underline"></div>
          </div>
          <h4 class="obra-titulo">${o.titulo}</h4>
          <p class="obra-ano">${o.ano || ''}</p>`;
        obrasWrap.appendChild(card);
      });
    } else {
      obrasWrap.innerHTML = '<p class="text-on-surface-variant/50 italic font-body-md text-sm">Nenhuma obra cadastrada.</p>';
    }
  }


  let autorAtual = null;
  function selecionarAutor(id) {
    const autor = porId[id];
    if (!autor || autor === autorAtual) return;
    autorAtual = autor;

   
    document.querySelectorAll('.autor-li').forEach(li => {
      li.classList.toggle('ativo', String(li.dataset.autorId) === String(id));
    });

    
    conteudo.classList.add('trocando');
    fotoEl.classList.add('trocando');
    setTimeout(() => {
      renderAutor(autor);
      conteudo.classList.remove('trocando');
      fotoEl.classList.remove('trocando');
    }, 300);
  }


  document.querySelectorAll('.autor-li').forEach(li => {
    li.querySelector('.autor-btn').addEventListener('click', () => {
      selecionarAutor(li.dataset.autorId);
    });
  });

 
  const listaAmericana = document.getElementById('lista-americana');
  const listaJaponesa  = document.getElementById('lista-japonesa');

  document.querySelectorAll('.trad-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const trad = btn.dataset.tradicao;

     
      document.querySelectorAll('.trad-btn').forEach(b => {
        const ativo = b === btn;
        b.classList.toggle('text-primary', ativo);
        b.classList.toggle('border-primary', ativo);
        b.classList.toggle('text-on-surface-variant', !ativo);
        b.classList.toggle('border-transparent', !ativo);
      });

    
      if (trad === 'americana') {
        listaAmericana.classList.remove('hidden');
        listaJaponesa.classList.add('hidden');
      } else {
        listaJaponesa.classList.remove('hidden');
        listaAmericana.classList.add('hidden');
      }

     
      const primeiro = (trad === 'americana' ? listaAmericana : listaJaponesa).querySelector('.autor-li');
      if (primeiro) selecionarAutor(primeiro.dataset.autorId);
    });
  });


  const primeiroLi = document.querySelector('#lista-americana .autor-li') ||
                     document.querySelector('#lista-japonesa .autor-li');
  if (primeiroLi) {

    if (!document.querySelector('#lista-americana .autor-li')) {
      listaAmericana.classList.add('hidden');
      listaJaponesa.classList.remove('hidden');
    }
    renderAutor(porId[primeiroLi.dataset.autorId]);
    autorAtual = porId[primeiroLi.dataset.autorId];
    primeiroLi.classList.add('ativo');
  }

});