import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonContent, IonInput, IonButton, IonItem, IonLabel, IonText,
  IonSpinner, IonIcon
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { searchOutline } from 'ionicons/icons';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    IonContent, IonInput, IonButton, IonItem, IonLabel, IonText,
    IonSpinner, IonIcon,
  ],
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
})
export class LoginPage {
  email = '';
  password = '';
  erro = '';
  carregando = false;

  constructor(private auth: AuthService, private router: Router) {
    addIcons({ searchOutline });   // registra o icone usado no template
  }

  async entrar() {
    this.erro = '';
    if (!this.email || !this.password) {
      this.erro = 'Informe email e senha.';
      return;
    }
    this.carregando = true;
    try {
      await this.auth.login(this.email, this.password);
      this.router.navigateByUrl('/home', { replaceUrl: true });
    } catch (e: any) {
      this.erro = e?.error?.erro || 'Nao foi possivel entrar. Verifique os dados.';
    } finally {
      this.carregando = false;
    }
  }

  irParaRegistro() {
    this.router.navigateByUrl('/register');
  }
}