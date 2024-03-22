import { Injectable } from '@angular/core';
import { io, Socket } from 'socket.io-client';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket: Socket;
  private bpmSubject = new BehaviorSubject<number>(0); // Initialise avec 0 ou une valeur de départ

  constructor() {
    this.socket = io('http://127.0.0.1:5000'); // URL de votre serveur Flask-SocketIO
    this.connect();
  }

  connect(): void {
    this.socket.on('connect', () =>
      console.log('Connected to WebSocket server')
    );

    this.socket.on('tempo_update', (data: any) => {
      console.log('Tempo update received:', data);
      this.bpmSubject.next(data.tempo);
    });
  }

  getBpmUpdates() {
    return this.bpmSubject.asObservable();
  }
}
