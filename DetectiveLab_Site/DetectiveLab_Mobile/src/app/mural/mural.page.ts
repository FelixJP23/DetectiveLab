import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { IonContent, IonSpinner, IonIcon, ViewWillEnter } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { arrowBack, bookOutline, libraryOutline } from 'ionicons/icons';
import { MuralService } from '../services/mural.service';

@Component({
  selector: 'app-mural',
  standalone: true,
  imports: [CommonModule, IonContent, IonSpinner, IonIcon],
  templateUrl: './mural.page.html',
  styleUrls: ['./mural.page.scss'],
})
export class MuralPage implements ViewWillEnter {
  americanos: any[] = [];
  japoneses: any[] = [];
  carregando = true;
  erro = '';

  tradicaoAtiva: 'americana' | 'japonesa' = 'americana';
  autorAtual: any = null;
  trocando = false;   // controla o fade

  constructor(private muralSvc: MuralService, private router: Router) {
    addIcons({ arrowBack, bookOutline, libraryOutline });
  }

  async ionViewWillEnter() {
    await this.carregar();
  }

  async carregar() {
    this.carregando = true;
    this.erro = '';
    try {
      const data = await this.muralSvc.listar();
      this.americanos = data.americanos || [];
      this.japoneses = data.japoneses || [];
      // selecao inicial: primeiro americano; se nao houver, primeiro japones
      if (this.americanos.length > 0) {
        this.tradicaoAtiva = 'americana';
        this.autorAtual = this.americanos[0];
      } else if (this.japoneses.length > 0) {
        this.tradicaoAtiva = 'japonesa';
        this.autorAtual = this.japoneses[0];
      } else {
        this.autorAtual = null;
      }
    } catch (e) {
      this.erro = 'Nao foi possivel carregar o mural.';
    } finally {
      this.carregando = false;
    }
  }

  /** Lista de autores da tradicao ativa. */
  get autoresAtivos(): any[] {
    return this.tradicaoAtiva === 'americana' ? this.americanos : this.japoneses;
  }

  get temAutores(): boolean {
    return this.americanos.length > 0 || this.japoneses.length > 0;
  }

  trocarTradicao(t: 'americana' | 'japonesa') {
    if (t === this.tradicaoAtiva) return;
    this.tradicaoAtiva = t;
    const lista = this.autoresAtivos;
    if (lista.length > 0) this.selecionarAutor(lista[0]);
  }

  /** Troca o autor com transicao suave (fade). */
  selecionarAutor(autor: any) {
    if (!autor || autor === this.autorAtual) return;
    this.trocando = true;
    setTimeout(() => {
      this.autorAtual = autor;
      this.trocando = false;
    }, 250);
  }

  tradicaoLabel(): string {
    return this.tradicaoAtiva === 'americana' ? 'TRADICAO AMERICANA' : 'TRADICAO JAPONESA';
  }

  voltar() { this.router.navigateByUrl('/home'); }
}