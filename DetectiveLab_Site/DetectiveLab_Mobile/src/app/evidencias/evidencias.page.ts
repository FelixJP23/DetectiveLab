import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonContent, IonSpinner, IonIcon, IonModal, IonTextarea, IonSelect, IonSelectOption,
  ViewWillEnter
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import {
  arrowBack, search, close, cloudUploadOutline, downloadOutline, bookOutline,
  personCircleOutline, documentLockOutline
} from 'ionicons/icons';
import { EvidenciasService } from '../services/evidencias.service';
import { LivrosService } from '../services/livros.service';

@Component({
  selector: 'app-evidencias',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    IonContent, IonSpinner, IonIcon, IonModal, IonTextarea, IonSelect, IonSelectOption,
  ],
  templateUrl: './evidencias.page.html',
  styleUrls: ['./evidencias.page.scss'],
})
export class EvidenciasPage implements ViewWillEnter {
  compartilhadas: any[] = [];
  meusTitulos: string[] = [];
  carregando = true;
  erro = '';
  filtro = '';
  toastMsg = '';

  // modal exportar
  exportAberto = false;
  meusLivros: any[] = [];
  livroSelecionado: number | null = null;
  detalhesExport = '';
  exportando = false;

  // overlay detalhe
  detalheAberto = false;
  sel: any = null;
  importando = false;

  constructor(
    private evSvc: EvidenciasService,
    private livrosSvc: LivrosService,
    private router: Router
  ) {
    addIcons({
      arrowBack, search, close, cloudUploadOutline, downloadOutline, bookOutline,
      personCircleOutline, documentLockOutline
    });
  }

  async ionViewWillEnter() {
    await this.carregar();
  }

  async carregar() {
    this.carregando = true;
    this.erro = '';
    try {
      const data = await this.evSvc.listar();
      this.compartilhadas = data.compartilhadas || [];
      this.meusTitulos = data.meus_titulos || [];
    } catch (e) {
      this.erro = 'Nao foi possivel carregar as evidencias.';
    } finally {
      this.carregando = false;
    }
  }

  /** Filtra por titulo do livro OU nome do autor. */
  get filtradas(): any[] {
    const q = this.filtro.toLowerCase().trim();
    if (!q) return this.compartilhadas;
    return this.compartilhadas.filter(e =>
      (e.titulo_livro || '').toLowerCase().includes(q) ||
      (e.autor_nome || '').toLowerCase().includes(q)
    );
  }

  /** Regra de import: so pode quem tem um livro de titulo igual. */
  temOLivro(titulo: string): boolean {
    return this.meusTitulos.some(t => t.toLowerCase() === (titulo || '').toLowerCase());
  }

  voltar() { this.router.navigateByUrl('/home'); }

  // ---------- EXPORTAR ----------
  async abrirExport() {
    this.livroSelecionado = null;
    this.detalhesExport = '';
    try {
      this.meusLivros = await this.livrosSvc.listar();
    } catch (e) {
      this.meusLivros = [];
    }
    this.exportAberto = true;
  }
  fecharExport() { this.exportAberto = false; }

  async exportar() {
    if (!this.livroSelecionado) return;
    this.exportando = true;
    try {
      await this.evSvc.exportar(this.livroSelecionado, this.detalhesExport.trim());
      this.exportAberto = false;
      await this.carregar();
      this.toast('Anotacoes exportadas.');
    } catch (e) {
      this.toast('Erro ao exportar.');
    } finally {
      this.exportando = false;
    }
  }

  // ---------- DETALHE / IMPORTAR ----------
  abrirDetalhe(ev: any) {
    this.sel = ev;
    this.detalheAberto = true;
  }
  fecharDetalhe() { this.detalheAberto = false; this.sel = null; }

  async importar(ev: any, e?: Event) {
    if (e) e.stopPropagation();
    if (!this.temOLivro(ev.titulo_livro)) {
      this.toast('Voce precisa ter "' + ev.titulo_livro + '" na sua biblioteca para importar.');
      return;
    }
    this.importando = true;
    try {
      await this.evSvc.importar(ev.id);
      this.toast('Anotacoes importadas! Confira na biblioteca.');
      this.detalheAberto = false;
    } catch (err: any) {
      this.toast(err?.error?.erro || 'Erro ao importar.');
    } finally {
      this.importando = false;
    }
  }

  // ---------- TOAST ----------
  private toastTimer: any;
  toast(msg: string) {
    this.toastMsg = msg;
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => (this.toastMsg = ''), 3000);
  }
}