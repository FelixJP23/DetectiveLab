import { Component, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import {
  IonContent, IonSpinner, IonIcon, IonModal, ViewWillEnter
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import {
  arrowBack, add, save, mapOutline, addCircleOutline, close, trashOutline,
  cameraOutline, imageOutline, layersOutline
} from 'ionicons/icons';
import { QuadroService } from '../services/quadro.service';

/** Estrutura de um card no estado local do quadro. */
interface CardLocal {
  id: string;            // id real (positivo) ou temporario (negativo) como string
  titulo: string;
  descricao: string;
  x: number;
  y: number;
  imagem_url?: string | null;
  subtitulos: { titulo: string; conteudo: string }[];
  isImagem: boolean;
}

@Component({
  selector: 'app-quadro',
  standalone: true,
  imports: [CommonModule, FormsModule, IonContent, IonSpinner, IonIcon, IonModal],
  templateUrl: './quadro.page.html',
  styleUrls: ['./quadro.page.scss'],
})
export class QuadroPage implements ViewWillEnter {
  @ViewChild('boardContainer') boardContainer!: ElementRef<HTMLElement>;

  livroId!: number;
  numeroAtual = 1;
  livroTitulo = '';
  capituloId!: number;
  capitulos: { id: number; numero: number }[] = [];

  cards: CardLocal[] = [];
  conexoes: { origem: string; destino: string }[] = [];

  carregando = true;
  salvando = false;
  erro = '';
  toastMsg = '';

  // dimensoes do board (cresce conforme os cards)
  boardW = 1400;
  boardH = 1600;

  // estado de arrastar
  private dragId: string | null = null;
  private offX = 0;
  private offY = 0;

  // estado de conectar fios
  pinoArmado: string | null = null;

  // id temporario decrescente para cards novos
  private tempId = -1;

  // seletor de capitulos (modal)
  capModalAberto = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private quadroSvc: QuadroService
  ) {
    addIcons({
      arrowBack, add, save, mapOutline, addCircleOutline, close, trashOutline,
      cameraOutline, imageOutline, layersOutline
    });
  }

  async ionViewWillEnter() {
    this.livroId = Number(this.route.snapshot.paramMap.get('livroId'));
    const num = this.route.snapshot.paramMap.get('numero');
    this.numeroAtual = num ? Number(num) : 1;
    await this.carregar();
  }

  async carregar() {
    this.carregando = true;
    this.erro = '';
    try {
      const data = await this.quadroSvc.abrir(this.livroId, this.numeroAtual);
      this.livroTitulo = data.livro_titulo;
      this.capitulos = data.capitulos || [];
      const cap = data.capitulo_atual;
      this.capituloId = cap.id;
      this.numeroAtual = cap.numero;

      // monta os cards locais a partir do retorno da API
      this.cards = (cap.cards || []).map((c: any) => ({
        id: String(c.id),
        titulo: c.titulo,
        descricao: c.descricao,
        x: c.pos_x,
        y: c.pos_y,
        imagem_url: c.imagem_url,
        subtitulos: (c.subtitulos || []).map((s: any) => ({ titulo: s.titulo, conteudo: s.conteudo })),
        isImagem: !!c.imagem_url,
      }));

      // conexoes vem com ids de Card reais
      this.conexoes = (cap.conexoes || []).map((x: any) => ({
        origem: String(x.origem), destino: String(x.destino),
      }));

      this.ajustarBoard();
    } catch (e) {
      this.erro = 'Nao foi possivel carregar o quadro.';
    } finally {
      this.carregando = false;
    }
  }

  // ---------- BOARD: expande conforme os cards ----------
  private ajustarBoard() {
    let maxX = 1000, maxY = 1200;
    this.cards.forEach(c => {
      maxX = Math.max(maxX, c.x + 400);
      maxY = Math.max(maxY, c.y + 400);
    });
    this.boardW = maxX;
    this.boardH = maxY;
  }

  // ---------- ARRASTAR (Pointer Events: mouse + toque) ----------
  onPointerDown(ev: PointerEvent, card: CardLocal) {
    // nao arrasta se tocar em campos de texto ou botoes
    const alvo = ev.target as HTMLElement;
    if (alvo.closest('.note-input, .note-textarea, .pino, .btn-remover')) return;
    this.dragId = card.id;
    const el = (ev.currentTarget as HTMLElement);
    const rect = el.getBoundingClientRect();
    this.offX = ev.clientX - rect.left;
    this.offY = ev.clientY - rect.top;
    el.setPointerCapture(ev.pointerId);
  }

  onPointerMove(ev: PointerEvent, card: CardLocal) {
    if (this.dragId !== card.id) return;
    const cont = this.boardContainer.nativeElement;
    const contRect = cont.getBoundingClientRect();
    // posicao relativa ao board, considerando o scroll
    let nx = ev.clientX - contRect.left + cont.scrollLeft - this.offX;
    let ny = ev.clientY - contRect.top + cont.scrollTop - this.offY;
    card.x = Math.max(0, nx);
    card.y = Math.max(0, ny);
    this.ajustarBoard();
  }

  onPointerUp(ev: PointerEvent, card: CardLocal) {
    if (this.dragId === card.id) this.dragId = null;
  }

  // ---------- CONECTAR FIOS ----------
  togglePino(card: CardLocal, ev: Event) {
    ev.stopPropagation();
    if (!this.pinoArmado) {
      this.pinoArmado = card.id;
      return;
    }
    if (this.pinoArmado === card.id) {
      this.pinoArmado = null;   // clicou no mesmo: cancela
      return;
    }
    const a = this.pinoArmado, b = card.id;
    const existe = this.conexoes.some(c =>
      (c.origem === a && c.destino === b) || (c.origem === b && c.destino === a));
    if (!existe) this.conexoes.push({ origem: a, destino: b });
    this.pinoArmado = null;
  }

  /** Coordenadas (centro do topo) de um card, para desenhar o fio. */
  pontoCard(id: string): { x: number; y: number } | null {
    const c = this.cards.find(x => x.id === id);
    if (!c) return null;
    // largura aproximada do card (260) -> centro = x + 130; topo = y
    return { x: c.x + 130, y: c.y };
  }

  /** Lista de linhas (x1,y1,x2,y2) para o SVG. */
  get linhas(): { x1: number; y1: number; x2: number; y2: number }[] {
    const out: any[] = [];
    this.conexoes.forEach(con => {
      const o = this.pontoCard(con.origem);
      const d = this.pontoCard(con.destino);
      if (o && d) out.push({ x1: o.x, y1: o.y, x2: d.x, y2: d.y });
    });
    return out;
  }

  // ---------- CRIAR / REMOVER CARD ----------
  criarCard() {
    const cont = this.boardContainer?.nativeElement;
    const sl = cont ? cont.scrollLeft : 0;
    const st = cont ? cont.scrollTop : 0;
    this.cards.push({
      id: String(this.tempId--),
      titulo: '', descricao: '',
      x: sl + 40, y: st + 40,
      imagem_url: null, subtitulos: [], isImagem: false,
    });
  }

  removerCard(card: CardLocal, ev: Event) {
    ev.stopPropagation();
    this.conexoes = this.conexoes.filter(c => c.origem !== card.id && c.destino !== card.id);
    this.cards = this.cards.filter(c => c.id !== card.id);
    if (this.pinoArmado === card.id) this.pinoArmado = null;
  }

  // ---------- SALVAR ----------
  async salvar() {
    this.salvando = true;
    try {
      const payload = {
        cards: this.cards.map(c => ({
          id: c.id,
          titulo: c.titulo,
          descricao: c.isImagem ? '' : c.descricao,
          x: Math.round(c.x),
          y: Math.round(c.y),
          subtitulos: c.isImagem ? c.subtitulos : [],
        })),
        conexoes: this.conexoes,
      };
      await this.quadroSvc.salvar(this.capituloId, payload);
      this.toast('Anotacoes salvas.');
      // recarrega para sincronizar ids temporarios -> reais
      await this.carregar();
    } catch (e) {
      this.toast('Erro ao salvar.');
    } finally {
      this.salvando = false;
    }
  }

  // ---------- CAPITULOS ----------
  abrirSeletorCap() { this.capModalAberto = true; }
  fecharSeletorCap() { this.capModalAberto = false; }

  async trocarCapitulo(numero: number) {
    this.capModalAberto = false;
    if (numero === this.numeroAtual) return;
    this.numeroAtual = numero;
    await this.carregar();
  }

  async criarCapitulo() {
    try {
      const cap = await this.quadroSvc.novoCapitulo(this.livroId);
      this.capModalAberto = false;
      this.numeroAtual = cap.numero;
      await this.carregar();
    } catch (e) {
      this.toast('Erro ao criar capitulo.');
    }
  }

  // ---------- OCR ----------
  acionarOcr(input: HTMLInputElement) { input.click(); }

  async onImagemOcr(ev: any) {
    const file = ev?.target?.files?.[0];
    if (!file) return;
    this.toast('Processando imagem...');
    try {
      const r = await this.quadroSvc.ocr(this.capituloId, file);
      if (!r.ok) { this.toast(r.erro || 'Erro no OCR.'); return; }
      // a API ja criou o card no banco; adicionamos ao estado local com o id real
      const cont = this.boardContainer?.nativeElement;
      this.cards.push({
        id: String(r.card_id),
        titulo: 'Diagrama Importado',
        descricao: '',
        x: (cont ? cont.scrollLeft : 0) + 60,
        y: (cont ? cont.scrollTop : 0) + 60,
        imagem_url: r.imagem_url,
        subtitulos: (r.linhas || []).map((l: string) => ({ titulo: l, conteudo: '' })),
        isImagem: true,
      });
      this.ajustarBoard();
      this.toast('Texto reconhecido!');
    } catch (e) {
      this.toast('Erro ao processar imagem.');
    } finally {
      ev.target.value = '';
    }
  }

  voltar() { this.router.navigateByUrl('/biblioteca'); }

  // ---------- TOAST ----------
  private toastTimer: any;
  toast(msg: string) {
    this.toastMsg = msg;
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => (this.toastMsg = ''), 2500);
  }

  trackById(_i: number, c: CardLocal) { return c.id; }
}