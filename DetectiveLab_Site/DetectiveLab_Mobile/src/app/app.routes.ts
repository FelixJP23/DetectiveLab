import { Routes } from '@angular/router';
import { AuthGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },

  {
    path: 'login',
    loadComponent: () => import('./login/login.page').then(m => m.LoginPage),
  },
  {
    path: 'register',
    loadComponent: () => import('./register/register.page').then(m => m.RegisterPage),
  },

  // Exemplo de rota protegida (so abre logado). Aponte para sua home depois.
  {
    path: 'home',
    canActivate: [AuthGuard],
    loadComponent: () => import('./home/home.page').then(m => m.HomePage),
  },
  {
    path: 'biblioteca',
    canActivate: [AuthGuard],
    loadComponent: () => import('./biblioteca/biblioteca.page').then(m => m.BibliotecaPage),
  },
  {
    path: 'evidencias',
    canActivate: [AuthGuard],
    loadComponent: () => import('./evidencias/evidencias.page').then(m => m.EvidenciasPage),
  },
  {
    path: 'mural',
    canActivate: [AuthGuard],
    loadComponent: () => import('./mural/mural.page').then(m => m.MuralPage),
  },
  {
    path: 'quadro/:livroId',
    canActivate: [AuthGuard],
    loadComponent: () => import('./quadro/quadro.page').then(m => m.QuadroPage),
  },
  {
    path: 'quadro/:livroId/:numero',
    canActivate: [AuthGuard],
    loadComponent: () => import('./quadro/quadro.page').then(m => m.QuadroPage),
  },
];