import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonContent, IonInput, IonButton, IonItem, IonLabel, IonText,
  IonHeader, IonToolbar, IonTitle, IonSpinner, IonButtons, IonBackButton
} from '@ionic/angular/standalone';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    IonContent, IonInput, IonButton, IonItem, IonLabel, IonText,
    IonHeader, IonToolbar, IonTitle, IonSpinner, IonButtons, IonBackButton,
  ],
  templateUrl: './register.page.html',
  styleUrls: ['./register.page.scss'],
})
export class RegisterPage {
  username = '';
  email = '';
  password = '';
  password2 = '';
  erro = '';
  carregando = false;

  constructor(private auth: AuthService, private router: Router) {}

  async registrar() {
    this.erro = '';
    if (!this.username || !this.email || !this.password) {
      this.erro = 'Preencha todos os campos.';
      return;
    }
    if (this.password !== this.password2) {
      this.erro = 'As senhas nao conferem.';
      return;
    }
    this.carregando = true;
    try {
      await this.auth.register({
        username: this.username,
        email: this.email,
        password: this.password,
        password2: this.password2,
      });
      this.router.navigateByUrl('/home', { replaceUrl: true });
    } catch (e: any) {
      this.erro = this.extrairErro(e) || 'Nao foi possivel registrar.';
    } finally {
      this.carregando = false;
    }
  }

  private extrairErro(e: any): string {
    const err = e?.error;
    if (!err) return '';
    if (typeof err === 'string') return err;
    const primeiraChave = Object.keys(err)[0];
    if (primeiraChave) {
      const v = err[primeiraChave];
      return Array.isArray(v) ? v[0] : String(v);
    }
    return '';
  }
}