import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';


@Injectable({ providedIn: 'root' })
export class EvidenciasService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /** Lista as anotacoes compartilhadas + os titulos dos livros do usuario. */
  async listar(): Promise<{ compartilhadas: any[]; meus_titulos: string[] }> {
    return await firstValueFrom(
      this.http.get<{ compartilhadas: any[]; meus_titulos: string[] }>(`${this.base}/evidencias/`)
    );
  }

  /** Exporta um livro do usuario como anotacao compartilhada. */
  async exportar(livroId: number, detalhes: string): Promise<any> {
    return await firstValueFrom(
      this.http.post(`${this.base}/evidencias/exportar/`, { livro_id: livroId, detalhes })
    );
  }

  /** Importa uma anotacao compartilhada para o livro de mesmo titulo do usuario. */
  async importar(exportId: number): Promise<any> {
    return await firstValueFrom(
      this.http.post(`${this.base}/evidencias/${exportId}/importar/`, {})
    );
  }
}