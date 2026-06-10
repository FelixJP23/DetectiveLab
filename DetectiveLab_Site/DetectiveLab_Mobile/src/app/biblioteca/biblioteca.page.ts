import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonContent, IonSpinner, IonIcon, IonModal, IonInput, IonTextarea,
  ViewWillEnter
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import {
  arrowBack, add, search, close, cameraOutline, bookOutline,
  createOutline, trashOutline, arrowForward, checkmarkCircle, documentTextOutline
} from 'ionicons/icons';
import { LivrosService } from '../services/livros.service';

@Component({
  selector: 'app-biblioteca',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    IonContent, IonSpinner, IonIcon, IonModal, IonInput, IonTextarea,
  ],
  templateUrl: './biblioteca.page.html',
  styleUrls: ['./biblioteca.page.scss'],
})
export class BibliotecaPage implements ViewWillEnter {
  livros: any[] = [];
  carregando = true;
  erro = '';


  filtro = '';

 
  addAberto = false;
  novoTitulo = '';
  novaDescricao = '';
  novoStatus = 'aberto';
  novaCapaFile: File | null = null;
  novaCapaPreview = '';
  salvandoCriar = false;

 
  detalheAberto = false;
  sel: any = null;         
  selStatus = 'aberto';
  selDescricao = '';
  editandoDescricao = false;
  salvandoEditar = false;

  
  deleteAberto = false;
  livroParaExcluir: any = null;
  excluindo = false;

  constructor(private livrosSvc: LivrosService, private router: Router) {
    addIcons({
      arrowBack, add, search, close, cameraOutline, bookOutline,
      createOutline, trashOutline, arrowForward, checkmarkCircle, documentTextOutline
    });
  }

  async ionViewWillEnter() {
    await this.carregar();
  }

  async carregar() {
    this.carregando = true;
    this.erro = '';
    try {
      this.livros = await this.livrosSvc.listar();
    } catch (e) {
      this.erro = 'Nao foi possivel carregar a biblioteca.';
      this.livros = [];
    } finally {
      this.carregando = false;
    }
  }


  get livrosFiltrados(): any[] {
    const q = this.filtro.toLowerCase().trim();
    if (!q) return this.livros;
    return this.livros.filter(l => (l.titulo || '').toLowerCase().includes(q));
  }

  voltar() {
    this.router.navigateByUrl('/home');
  }


  abrirCriar() {
    this.novoTitulo = '';
    this.novaDescricao = '';
    this.novoStatus = 'aberto';
    this.novaCapaFile = null;
    this.novaCapaPreview = '';
    this.addAberto = true;
  }
  fecharCriar() { this.addAberto = false; }

  onCapaSelecionada(event: any) {
    const file = event?.target?.files?.[0];
    if (!file) return;
    this.novaCapaFile = file;
    this.novaCapaPreview = URL.createObjectURL(file);
  }

  async criar() {
    if (!this.novoTitulo.trim()) { return; }
    this.salvandoCriar = true;
    try {
      await this.livrosSvc.criar({
        titulo: this.novoTitulo.trim(),
        descricao: this.novaDescricao.trim(),
        status: this.novoStatus,
        capa: this.novaCapaFile,
      });
      this.addAberto = false;
      await this.carregar();
    } catch (e) {
      this.erro = 'Nao foi possivel criar o caso.';
    } finally {
      this.salvandoCriar = false;
    }
  }


  abrirDetalhe(livro: any) {
    this.sel = livro;
    this.selStatus = livro.status;
    this.selDescricao = livro.descricao || '';
    this.editandoDescricao = false;
    this.detalheAberto = true;
  }
  fecharDetalhe() { this.detalheAberto = false; this.sel = null; }

  selecionarStatus(s: string) { this.selStatus = s; }
  alternarEdicaoDescricao() { this.editandoDescricao = !this.editandoDescricao; }

  async salvarDetalhe() {
    if (!this.sel) return;
    this.salvandoEditar = true;
    try {
      await this.livrosSvc.editar(this.sel.id, {
        status: this.selStatus,
        descricao: this.selDescricao,
      });
      this.detalheAberto = false;
      await this.carregar();
    } catch (e) {
      this.erro = 'Nao foi possivel salvar.';
    } finally {
      this.salvandoEditar = false;
    }
  }

  irParaQuadro(numero?: number) {
    
  }


  abrirExcluir(livro: any, event: Event) {
    event.stopPropagation();   
    this.livroParaExcluir = livro;
    this.deleteAberto = true;
  }
  fecharExcluir() { this.deleteAberto = false; this.livroParaExcluir = null; }

  async confirmarExcluir() {
    if (!this.livroParaExcluir) return;
    this.excluindo = true;
    try {
      await this.livrosSvc.excluir(this.livroParaExcluir.id);
      this.deleteAberto = false;
      this.livroParaExcluir = null;
      await this.carregar();
    } catch (e) {
      this.erro = 'Nao foi possivel excluir.';
    } finally {
      this.excluindo = false;
    }
  }
}