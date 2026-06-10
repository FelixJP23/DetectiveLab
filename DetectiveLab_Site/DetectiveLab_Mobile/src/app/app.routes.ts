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
];