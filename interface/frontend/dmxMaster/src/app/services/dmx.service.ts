import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class DmxService {
  private baseUrl: string = 'http://127.0.0.1:5000';

  constructor(private http: HttpClient) { }

  setOladIp(ip: string) {
    return this.http.post(`${this.baseUrl}/set_olad_ip`, { ip });
  }

  setMode(mode: string) {
    return this.http.post(`${this.baseUrl}/set_mode`, { mode });
  }

  setSyncMode(sync_modes: string) {
    return this.http.post(`${this.baseUrl}/set_sync_mode`, { sync_modes });
  }

  setBpmMultiplier(multiplier: number) {
    return this.http.post(`${this.baseUrl}/set_bpm_multiplier`, { multiplier });
  }

  setPattern(pattern: string) {
    return this.http.post(`${this.baseUrl}/set_pattern`, { pattern });
  }

  setColor(color: string) {
    return this.http.post(`${this.baseUrl}/set_color`, { color });
  }

  setHorizontalAdjust(adjust: number) {
    return this.http.post(`${this.baseUrl}/set_horizontal_adjust`, { adjust });
  }

  setHorizontalAnimation(enabled: boolean, speed: number) {
    return this.http.post(`${this.baseUrl}/set_horizontal_animation`, {
      enabled,
      speed
    });
  }

  setVerticalAnimation(enabled: boolean, speed: number) {
    return this.http.post(`${this.baseUrl}/set_vertical_animation`, {
      enabled,
      speed
    });
  }

  setStrobeMode(enabled: boolean) {
    return this.http.post(`${this.baseUrl}/set_strobe_mode`, { enabled });
  }

  setDmx(data: any) {
    return this.http.post(`${this.baseUrl}/set_dmx`, data);
  }

  getBpm() {
    return this.http.get(`${this.baseUrl}/get_bpm`);
  }

  setOlaIp(ip: string) {
    return this.http.post(`${this.baseUrl}/set_ola_ip`, { ip });
  }

  setOlaPort(port: string) {
    return this.http.post(`${this.baseUrl}/set_ola_port`, { port });
  }

  getOlaIp() {
    return this.http.get(`${this.baseUrl}/get_ola_ip`);
  }
}
