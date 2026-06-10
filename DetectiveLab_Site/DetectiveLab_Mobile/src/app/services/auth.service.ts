import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Storage } from '@ionic/storage-angular';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';

/**
 * AuthService — centro da autenticacao do app.
 *
 * Responsabilidades:
 *  - login / registro / logout chamando a API Django
 *  - guardar e recuperar o TOKEN no Ionic Storage (persiste entre sessoes)
 *  - dizer se o usuario esta logado (isAuthenticated)
 *
 * O token guardado aqui e lido pelo AuthInterceptor, que o injeta em toda
 * requisicao. Assim, as telas nao precisam mexer com token diretamente.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly USER_KEY = 'auth_user';
  private storageReady: Promise<void>;
  private _token: string | null = null;

  constructor(private http: HttpClient, private storage: Storage) {
    // Inicializa o storage e ja carrega o token salvo (se houver)
    this.storageReady = this.init();
  }

  private async init(): Promise<void> {
    await this.storage.create();
    this._token = await this.storage.get(this.TOKEN_KEY);
  }

  /** Garante que o storage terminou de carregar antes de ler o token. */
  async ready(): Promise<void> {
    await this.storageReady;
  }

  /** Login por EMAIL + senha. Salva token + user e retorna os dados. */
  async login(email: string, password: string): Promise<any> {
    const resp: any = await firstValueFrom(
      this.http.post(`${environment.apiUrl}/auth/login/`, { email, password })
    );
    await this.salvarSessao(resp.token, resp.user);
    return resp;
  }

  /** Registro. A API ja devolve token (login automatico), entao salvamos. */
  async register(dados: {
    username: string; email: string; password: string; password2: string;
  }): Promise<any> {
    const resp: any = await firstValueFrom(
      this.http.post(`${environment.apiUrl}/auth/register/`, dados)
    );
    await this.salvarSessao(resp.token, resp.user);
    return resp;
  }

  /** Logout: avisa a API (apaga o token no servidor) e limpa o storage local. */
  async logout(): Promise<void> {
    try {
      await firstValueFrom(this.http.post(`${environment.apiUrl}/auth/logout/`, {}));
    } catch (e) {
      // Mesmo se a chamada falhar (ex: offline), limpamos local de qualquer jeito
    }
    this._token = null;
    await this.storage.remove(this.TOKEN_KEY);
    await this.storage.remove(this.USER_KEY);
  }

  /** Salva token e dados do usuario no storage e em memoria. */
  private async salvarSessao(token: string, user: any): Promise<void> {
    this._token = token;
    await this.storage.set(this.TOKEN_KEY, token);
    await this.storage.set(this.USER_KEY, user);
  }

  /** Token atual (em memoria). Usado pelo interceptor. */
  getToken(): string | null {
    return this._token;
  }

  /** Dados do usuario logado. */
  async getUser(): Promise<any> {
    await this.ready();
    return this.storage.get(this.USER_KEY);
  }

  /** True se ha token salvo. */
  async isAuthenticated(): Promise<boolean> {
    await this.ready();
    return !!this._token;
  }
}