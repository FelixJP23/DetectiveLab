import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';


@Injectable({ providedIn: 'root' })
export class MuralService {
  private base = environment.apiUrl;
  constructor(private http: HttpClient) {}

  async listar(): Promise<{ americanos: any[]; japoneses: any[] }> {
    return await firstValueFrom(
      this.http.get<{ americanos: any[]; japoneses: any[] }>(`${this.base}/mural/`)
    );
  }
}