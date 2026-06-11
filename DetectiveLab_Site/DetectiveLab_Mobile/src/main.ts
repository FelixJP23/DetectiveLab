import { bootstrapApplication } from '@angular/platform-browser';
import { RouteReuseStrategy, provideRouter } from '@angular/router';
import { IonicRouteStrategy, provideIonicAngular } from '@ionic/angular/standalone';
import { provideHttpClient, withInterceptorsFromDi, HTTP_INTERCEPTORS } from '@angular/common/http';
import { IonicStorageModule } from '@ionic/storage-angular';
import { importProvidersFrom } from '@angular/core';

import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';
import { AuthInterceptor } from './app/interceptors/auth.interceptor';

bootstrapApplication(AppComponent, {
  providers: [
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    provideIonicAngular(),
    provideRouter(routes),

    // HttpClient com suporte a interceptors registrados via DI
    provideHttpClient(withInterceptorsFromDi()),

    // Registra o interceptor de autenticacao (injeta o token em toda requisicao)
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },

    // Ionic Storage (guarda o token)
    importProvidersFrom(IonicStorageModule.forRoot()),
  ],
});