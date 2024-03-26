import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class DmxService {
  private baseUrl: string = 'http://127.0.0.1:5000';

  constructor(private http: HttpClient) {}

  setOladIp(ip: string) {
    return this.http.post(`${this.baseUrl}/set_olad_ip`, { ip });
  }

  setMode(mode: string) {
    return this.http.post(`${this.baseUrl}/set_mode`, { mode });
  }

  setSyncMode(sync_modes: string) {
    return this.http.post(`${this.baseUrl}/set_sync_mode`, { sync_modes });
  }

  setPattern(pattern: string) {
    return this.http.post(`${this.baseUrl}/set_pattern`, { pattern });
  }

  setColor(color: string) {
    return this.http.post(`${this.baseUrl}/set_color`, { color });
  }

  setDmx(data: any) {
    return this.http.post(`${this.baseUrl}/set_dmx`, data);
  }

  getBpm() {
    return this.http.get(`${this.baseUrl}/get_bpm`);
  }
}
