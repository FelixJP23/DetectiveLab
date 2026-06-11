import { Injectable } from '@angular/core';
import {
  HttpInterceptor, HttpRequest, HttpHandler, HttpEvent
} from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from '../services/auth.service';

/*
 * AuthInterceptor — injeta o header de autenticacao em TODA requisicao.
 */
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private auth: AuthService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = this.auth.getToken();

    // Nao injeta token em login/registro
    const isAuthRoute = req.url.includes('/auth/login') || req.url.includes('/auth/register');

    if (token && !isAuthRoute) {
      const cloned = req.clone({
        setHeaders: { Authorization: `Token ${token}` },
      });
      return next.handle(cloned);
    }
    return next.handle(req);
  }
}