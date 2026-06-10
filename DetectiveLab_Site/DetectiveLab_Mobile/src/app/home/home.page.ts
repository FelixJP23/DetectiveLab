import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import {
  IonContent, IonSpinner, IonIcon,
  ViewWillEnter
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import {
  searchCircleOutline, gitNetworkOutline, arrowForward, bookOutline,
  notificationsOutline, personOutline, logOutOutline
} from 'ionicons/icons';
import { AuthService } from '../services/auth.service';
import { LivrosService } from '../services/livros.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, IonContent, IonSpinner, IonIcon],
  templateUrl: './home.page.html',
  styleUrls: ['./home.page.scss'],
})
export class HomePage implements ViewWillEnter {
  username = '';
  fotoUrl = '';
  dossies: any[] = [];
  carregando = true;
  erro = '';

  constructor(
    private auth: AuthService,
    private livros: LivrosService,
    private router: Router
  ) {
    addIcons({
      searchCircleOutline, gitNetworkOutline, arrowForward, bookOutline,
      notificationsOutline, personOutline, logOutOutline
    });
  }

  /**
   * usuario criar/editar um livro e voltar, a lista se atualiza.
   */
  async ionViewWillEnter() {
    const user = await this.auth.getUser();
    this.username = user?.username || 'Detetive';
    this.fotoUrl = user?.foto_url || '';
    await this.carregarDossies();
  }

  async carregarDossies() {
    this.carregando = true;
    this.erro = '';
    try {
      this.dossies = await this.livros.ativos();
    } catch (e) {
      this.erro = 'Nao foi possivel carregar os dossies.';
      this.dossies = [];
    } finally {
      this.carregando = false;
    }
  }

  
  irBiblioteca()  { this.router.navigateByUrl('/biblioteca'); }
  irEvidencias()  { /* TODO: rota do arquivo de evidencias */ }
  irMural()       { /* TODO: rota do mural de casos */ }

  async sair() {
    await this.auth.logout();
    this.router.navigateByUrl('/login', { replaceUrl: true });
  }
}