import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';


@Injectable({ providedIn: 'root' })
export class QuadroService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /** Abre um capitulo do quadro. Se numero for omitido, abre o capitulo 1. */
  async abrir(livroId: number, numero?: number): Promise<any> {
    const url = numero != null
      ? `${this.base}/livros/${livroId}/quadro/${numero}/`
      : `${this.base}/livros/${livroId}/quadro/`;
    return await firstValueFrom(this.http.get(url));
  }

  /** Salva o estado do quadro (cards + conexoes) via JSON. */
  async salvar(capituloId: number, payload: { cards: any[]; conexoes: any[] }): Promise<any> {
    return await firstValueFrom(
      this.http.post(`${this.base}/capitulos/${capituloId}/salvar/`, payload)
    );
  }

  /** Cria o proximo capitulo do livro. */
  async novoCapitulo(livroId: number): Promise<any> {
    return await firstValueFrom(
      this.http.post(`${this.base}/livros/${livroId}/novo-capitulo/`, {})
    );
  }

  /** Envia uma imagem para OCR (multipart). Retorna {linhas, card_id, imagem_url}. */
  async ocr(capituloId: number, imagem: File): Promise<any> {
    const fd = new FormData();
    fd.append('imagem', imagem);
    return await firstValueFrom(
      this.http.post(`${this.base}/capitulos/${capituloId}/ocr/`, fd)
    );
  }
}