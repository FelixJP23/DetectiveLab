/* ===========================================================
   DetectiveLab - Arquivo de Evidencias (logica)
   Arquivo: main_Page_funcionalidades/static/Css/arquivo_evidencias.js
   =========================================================== */

document.addEventListener('DOMContentLoaded', () => {

  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  let meusTitulos = [];
  try { meusTitulos = JSON.parse(document.body.dataset.meusTitulos || '[]'); } catch (e) {}

  // ---------- TOAST ----------
  const toastEl = document.getElementById('toast');
  let toastTimer;
  function toast(msg, erro) {
    toastEl.textContent = msg;
    toastEl.classList.toggle('erro', !!erro);
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('show'), 3500);
  }

  // ---------- BUSCA (titulo do livro OU nome do autor) ----------
  const busca = document.getElementById('busca');
  const cards = document.querySelectorAll('.evidencia-card');
  const grid  = document.getElementById('grid');
  const vazia = document.getElementById('busca-vazia');

  busca.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    let visiveis = 0;
    cards.forEach(card => {
      const titulo = (card.dataset.titulo || '').toLowerCase();
      const autor  = (card.dataset.autor  || '').toLowerCase();
      const bate = titulo.includes(q) || autor.includes(q);
      card.style.display = bate ? '' : 'none';
      if (bate) visiveis++;
    });
    if (cards.length > 0 && visiveis === 0 && q.length > 0) {
      grid.classList.add('hidden'); vazia.classList.remove('hidden'); vazia.classList.add('flex');
    } else {
      grid.classList.remove('hidden'); vazia.classList.add('hidden'); vazia.classList.remove('flex');
    }
  });

  // ---------- MODAL EXPORTAR ----------
  const exportModal = document.getElementById('export-modal');
  document.getElementById('btn-exportar').addEventListener('click', () => exportModal.classList.add('open'));
  document.getElementById('export-close').addEventListener('click', () => exportModal.classList.remove('open'));
  document.getElementById('export-cancel').addEventListener('click', () => exportModal.classList.remove('open'));
  exportModal.addEventListener('click', (e) => { if (e.target === exportModal) exportModal.classList.remove('open'); });

  // ---------- OVERLAY DETALHES ----------
  const detailModal = document.getElementById('detail-modal');
  const dCapa   = document.getElementById('detail-capa');
  const dTitulo = document.getElementById('detail-titulo');
  const dAutor  = document.getElementById('detail-autor');
  const dCaps   = document.getElementById('detail-capitulos');
  const dDet    = document.getElementById('detail-detalhes');
  const dAviso  = document.getElementById('detail-aviso');
  const dImport = document.getElementById('detail-importar');

  function temOLivro(titulo) {
    return meusTitulos.some(t => t.toLowerCase() === (titulo || '').toLowerCase());
  }

  function abrirDetalhes(card) {
    const titulo = card.dataset.titulo || '';
    dTitulo.textContent = titulo;
    dAutor.textContent  = card.dataset.autor || '';
    dCaps.textContent   = card.dataset.capitulos || '0';
    dDet.textContent    = card.dataset.detalhes || 'Sem detalhes.';

    if (card.dataset.capa) {
      dCapa.style.backgroundImage = `url('${card.dataset.capa}')`;
      dCapa.innerHTML = '';
    } else {
      dCapa.style.backgroundImage = '';
      dCapa.innerHTML = '<span class="material-symbols-outlined text-4xl text-surface-container-highest">book</span>';
    }

    // Regra: so importa se tem o livro (mesmo titulo)
    const possui = temOLivro(titulo);
    dImport.dataset.exportId = card.dataset.exportId;
    dImport.dataset.titulo = titulo;
    if (possui) {
      dImport.disabled = false;
      dImport.classList.remove('opacity-40', 'cursor-not-allowed');
      dAviso.classList.add('hidden');
    } else {
      dImport.disabled = true;
      dImport.classList.add('opacity-40', 'cursor-not-allowed');
      dAviso.textContent = 'Voce precisa ter "' + titulo + '" na sua biblioteca para importar.';
      dAviso.classList.remove('hidden');
    }

    detailModal.classList.add('open');
  }

  // Clique no card abre detalhes (menos se clicou no botao importar do proprio card)
  cards.forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('.btn-importar')) return;
      abrirDetalhes(card);
    });
  });

  document.getElementById('detail-close').addEventListener('click', () => detailModal.classList.remove('open'));
  detailModal.addEventListener('click', (e) => { if (e.target === detailModal) detailModal.classList.remove('open'); });

  // ---------- IMPORTAR ----------
  function importar(exportId, titulo, btn) {
    if (!temOLivro(titulo)) {
      toast('Voce precisa ter "' + titulo + '" na sua biblioteca para importar.', true);
      return;
    }
    const txtOriginal = btn ? btn.innerHTML : null;
    if (btn) { btn.disabled = true; btn.textContent = 'Importando...'; }

    fetch('/inicio/evidencias/' + exportId + '/importar/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken }
    })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        toast('Anotacoes importadas! Confira na sua biblioteca.');
        detailModal.classList.remove('open');
      } else {
        toast(data.erro || 'Erro ao importar.', true);
      }
    })
    .catch(() => toast('Erro de conexao.', true))
    .finally(() => { if (btn) { btn.disabled = false; btn.innerHTML = txtOriginal; } });
  }

  // Botao importar dentro de cada card
  document.querySelectorAll('.btn-importar').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      importar(btn.dataset.exportId, btn.dataset.titulo, btn);
    });
  });

  // Botao importar dentro do overlay de detalhes
  dImport.addEventListener('click', () => {
    if (dImport.disabled) return;
    importar(dImport.dataset.exportId, dImport.dataset.titulo, dImport);
  });

  // ESC fecha qualquer modal
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    exportModal.classList.remove('open');
    detailModal.classList.remove('open');
  });

});
