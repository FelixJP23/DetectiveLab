import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';

/**
 * LivrosService — consome os endpoints de livros da API.
 */
@Injectable({ providedIn: 'root' })
export class LivrosService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /** Dossies ativos (aberto/frio) com numeracao estavel — para a home. */
  async ativos(): Promise<any[]> {
    return await firstValueFrom(this.http.get<any[]>(`${this.base}/livros/ativos/`));
  }

  /** Todos os livros do usuario — para a biblioteca. */
  async listar(): Promise<any[]> {
    return await firstValueFrom(this.http.get<any[]>(`${this.base}/livros/`));
  }

 
  async criar(dados: { titulo: string; descricao: string; status: string; capa?: File | null }): Promise<any> {
    if (dados.capa) {
      const fd = new FormData();
      fd.append('titulo', dados.titulo);
      fd.append('descricao', dados.descricao);
      fd.append('status', dados.status);
      fd.append('capa', dados.capa);
      return await firstValueFrom(this.http.post(`${this.base}/livros/`, fd));
    }
    return await firstValueFrom(this.http.post(`${this.base}/livros/`, {
      titulo: dados.titulo, descricao: dados.descricao, status: dados.status,
    }));
  }

 
  async editar(livroId: number, dados: { status?: string; descricao?: string }): Promise<any> {
    return await firstValueFrom(this.http.put(`${this.base}/livros/${livroId}/`, dados));
  }


  async excluir(livroId: number): Promise<any> {
    return await firstValueFrom(this.http.delete(`${this.base}/livros/${livroId}/`));
  }
}