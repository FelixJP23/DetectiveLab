

document.addEventListener('DOMContentLoaded', () => {

  const body      = document.body;
  const board     = document.getElementById('board');
  const svg        = document.getElementById('threads');
  const saveUrl   = body.dataset.saveUrl;
  const ocrUrl    = body.dataset.ocrUrl;
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;


  let conexoes = [];
  let tempId = -1;   

 
  function cardId(cardEl) { return cardEl.dataset.cardId; }


  function criarCardEl(id, titulo, descricao, x, y) {
    const el = document.createElement('div');
    el.className = 'note-card';
    el.dataset.cardId = id;
    el.style.left = x + 'px';
    el.style.top  = y + 'px';
    el.innerHTML = `
      <div class="pin" data-card-id="${id}"></div>
      <div class="note-head">
        <input class="note-title" value="" placeholder="TITULO">
      </div>
      <textarea class="note-body" placeholder="Escreva sua anotacao..."></textarea>
      <button class="note-delete" type="button" title="Remover card">
        <span class="material-symbols-outlined" style="font-size:16px;">close</span>
      </button>`;
    el.querySelector('.note-title').value = titulo || '';
    el.querySelector('.note-body').value  = descricao || '';
    board.appendChild(el);
    wireCard(el);
    return el;
  }

 
  function wireCard(el) {
    const pin = el.querySelector('.pin');
    const del = el.querySelector('.note-delete');

    let drag = false, offX = 0, offY = 0;

    el.addEventListener('mousedown', (e) => {
    
      if (e.target.closest('.note-title, .note-body, .note-subtitle-edit, .pin, .note-delete')) return;
      drag = true;
      el.classList.add('dragging');
      offX = e.clientX - el.offsetLeft;
      offY = e.clientY - el.offsetTop;
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!drag) return;
      let nx = e.clientX - offX;
      let ny = e.clientY - offY;
      nx = Math.max(0, nx);
      ny = Math.max(0, ny);
      el.style.left = nx + 'px';
      el.style.top  = ny + 'px';

   
      expandBoardIfNeeded(nx + el.offsetWidth, ny + el.offsetHeight);
      drawThreads();
    });

    document.addEventListener('mouseup', () => {
      if (drag) { drag = false; el.classList.remove('dragging'); }
    });

  
    pin.addEventListener('click', (e) => {
      e.stopPropagation();
      onPinClick(el);
    });

  
    del.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = cardId(el);
      conexoes = conexoes.filter(c => String(c.origem) !== id && String(c.destino) !== id);
      el.remove();
      drawThreads();
    });

   
    el.querySelector('.note-body').addEventListener('input', drawThreads);
  }

  
  function expandBoardIfNeeded(right, bottom) {
    const curW = board.offsetWidth;
    const curH = board.offsetHeight;
    if (right + 400 > curW)  board.style.width  = (right + 400) + 'px';
    if (bottom + 400 > curH) board.style.height = (bottom + 400) + 'px';
  }


  let armedPin = null;   // primeiro card selecionado

  const hint = document.createElement('div');
  hint.id = 'connect-hint';
  hint.textContent = 'Clique no pino de outro card para conectar (ESC cancela)';
  document.body.appendChild(hint);

  function onPinClick(cardEl) {
    if (!armedPin) {
      armedPin = cardEl;
      cardEl.querySelector('.pin').classList.add('armed');
      hint.classList.add('show');
      return;
    }
    if (armedPin === cardEl) {
    
      desarmar();
      return;
    }
    const a = cardId(armedPin);
    const b = cardId(cardEl);
    
    const existe = conexoes.some(c =>
      (String(c.origem) === a && String(c.destino) === b) ||
      (String(c.origem) === b && String(c.destino) === a));
    if (!existe) conexoes.push({ origem: a, destino: b });
    desarmar();
    drawThreads();
  }

  function desarmar() {
    if (armedPin) armedPin.querySelector('.pin').classList.remove('armed');
    armedPin = null;
    hint.classList.remove('show');
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') desarmar();
  });

 
  function drawThreads() {
    svg.innerHTML = '';
    conexoes.forEach(con => {
      const o = board.querySelector(`.note-card[data-card-id="${con.origem}"]`);
      const d = board.querySelector(`.note-card[data-card-id="${con.destino}"]`);
      if (!o || !d) return;

      const ox = o.offsetLeft + o.offsetWidth / 2;
      const oy = o.offsetTop;            // topo (onde fica o pino)
      const dx = d.offsetLeft + d.offsetWidth / 2;
      const dy = d.offsetTop;

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', ox); line.setAttribute('y1', oy);
      line.setAttribute('x2', dx); line.setAttribute('y2', dy);
      line.setAttribute('class', 'thread-line');
      svg.appendChild(line);
    });
  }


  try {
    const raw = document.getElementById('conexoes-data').textContent.trim();
    if (raw) conexoes = JSON.parse(raw).map(c => ({ origem: String(c.origem), destino: String(c.destino) }));
  } catch (e) { conexoes = []; }


  document.querySelectorAll('.note-card').forEach(el => {
   
    el.style.left = (el.dataset.x || 100) + 'px';
    el.style.top  = (el.dataset.y || 100) + 'px';
    wireCard(el);
  });
  drawThreads();


  document.getElementById('btn-novo-card').addEventListener('click', () => {
    const scrollLeft = document.getElementById('board-container').scrollLeft;
    const scrollTop  = document.getElementById('board-container').scrollTop;
    criarCardEl(tempId--, '', '', scrollLeft + 80, scrollTop + 80);
  });


  document.getElementById('btn-salvar').addEventListener('click', () => {
    const cards = [];
    board.querySelectorAll('.note-card').forEach(el => {
      let descricao = '';
      let subtitulos = [];

      if (el.classList.contains('note-card-img')) {
      
        el.querySelectorAll('.sub-block').forEach(b => {
          subtitulos.push({
            titulo:   b.querySelector('.note-subtitle-edit').value,
            conteudo: b.querySelector('.note-body').value
          });
        });
      } else {
      
        const ta = el.querySelector('.note-body');
        descricao = ta ? ta.value : '';
      }

      cards.push({
        id: cardId(el),
        titulo: el.querySelector('.note-title').value,
        descricao: descricao,
        subtitulos: subtitulos,
        x: el.offsetLeft,
        y: el.offsetTop
      });
    });

    fetch(saveUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ cards: cards, conexoes: conexoes })
    })
    .then(r => r.json())
    .then(data => { if (data.ok) toast('Anotações salvas.'); else toast('Erro ao salvar.'); })
    .catch(() => toast('Erro de conexao.'));
  });


  document.getElementById('btn-ocr').addEventListener('click', () => {
    document.getElementById('ocr-input').click();
  });

  document.getElementById('ocr-input').addEventListener('change', (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    toast('Analisando Evidência...');

    const fd = new FormData();
    fd.append('imagem', file);

    fetch(ocrUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      body: fd
    })
    .then(r => r.json())
    .then(data => {
      if (!data.ok) { toast(data.erro || 'Erro no OCR.'); return; }

      criarCardFromOCR(data.linhas || [], data.imagem_url || null, data.card_id || null);
      toast('Texto reconhecido!');
    })
    .catch(() => toast('Erro ao processar imagem.'));

    e.target.value = ''; 
  });

  
  function criarCardFromOCR(linhas, imagemUrl, cardIdReal) {
    const sl = document.getElementById('board-container').scrollLeft;
    const st = document.getElementById('board-container').scrollTop;

    const id = (cardIdReal != null) ? cardIdReal : (tempId--);

    const el = document.createElement('div');
    el.className = 'note-card note-card-img';
    el.dataset.cardId = id;
    el.style.left = (sl + 120) + 'px';
    el.style.top  = (st + 120) + 'px';

    el.innerHTML = `
      <div class="pin" data-card-id="${id}"></div>
      ${imagemUrl ? `<img class="note-img" src="${imagemUrl}" alt="Diagrama importado">` : ''}
      <div class="note-head">
        <input class="note-title" value="Diagrama Importado" placeholder="TITULO">
      </div>
      <div class="note-subtitles"></div>
      <button class="note-delete" type="button" title="Remover card">
        <span class="material-symbols-outlined" style="font-size:16px;">close</span>
      </button>`;

    board.appendChild(el);

    const subWrap = el.querySelector('.note-subtitles');
    linhas.forEach(linha => {
      const bloco = document.createElement('div');
      bloco.className = 'sub-block';
      bloco.innerHTML = `
        <input class="note-subtitle-edit" value="">
        <textarea class="note-body" placeholder="Escreva sobre este item..."></textarea>`;
      bloco.querySelector('.note-subtitle-edit').value = linha;
      bloco.querySelector('.note-body').addEventListener('input', drawThreads);
      subWrap.appendChild(bloco);
    });

    wireCard(el);
    drawThreads();
  }


  let toastEl = document.getElementById('toast');
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.id = 'toast';
    document.body.appendChild(toastEl);
  }
  let toastTimer;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('show'), 2500);
  }

});
