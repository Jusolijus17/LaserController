import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { LaserControllerComponent } from './components/laser-controller/laser-controller.component';
import { WebSocketService } from './services/web-socket.service';
import { BehaviorSubject } from 'rxjs';
import { CommonModule } from '@angular/common';
import { DmxService } from './services/dmx.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, LaserControllerComponent, CommonModule],
  providers: [WebSocketService, DmxService],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  title = 'dmxMaster';
  currentBpm = 0;
  multiplier = new BehaviorSubject<number>(1);
  displayMultiplier = 'x1';

  get roundedBpm() {
    return Math.round(this.currentBpm);
  }

  constructor(
    private webSocketService: WebSocketService,
    private dmxService: DmxService
  ) {}

  updateDisplayMultiplier(value: number): void {
    if (value >= 1) {
      this.displayMultiplier = `x${value}`;
    } else {
      this.displayMultiplier = `÷${1 / value}`;
    }
  }

  increment() {
    const newValue = this.multiplier.value * 2;
    this.multiplier.next(newValue);
    this.updateDisplayMultiplier(newValue);
    this.dmxService.setBpmMultiplier(newValue).subscribe();
  }

  decrement() {
    const newValue = this.multiplier.value / 2;
    this.multiplier.next(newValue);
    this.updateDisplayMultiplier(newValue);
    this.dmxService.setBpmMultiplier(newValue).subscribe();
  }

  ngOnInit(): void {
    this.webSocketService.getBpmUpdates().subscribe(bpm => {
      this.currentBpm = bpm;
      console.log('Current BPM:', this.currentBpm);
    });
  }
}
