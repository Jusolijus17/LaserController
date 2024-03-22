import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { LaserControllerComponent } from './components/laser-controller/laser-controller.component';
import { WebSocketService } from './services/web-socket.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, LaserControllerComponent],
  providers: [WebSocketService],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  title = 'dmxMaster';
  currentBpm = 0;

  get roundedBpm() {
    return Math.round(this.currentBpm);
  }

  constructor(private webSocketService: WebSocketService) {}

  ngOnInit(): void {
    this.webSocketService.getBpmUpdates().subscribe(bpm => {
      this.currentBpm = bpm;
      console.log('Current BPM:', this.currentBpm);
    });
  }
}
