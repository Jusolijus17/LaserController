import { Component } from '@angular/core';
import { MODES } from '../../constants';
import { DmxService } from '../../services/dmx.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-mode-selector',
  standalone: true,
  imports: [CommonModule],
  providers: [],
  templateUrl: './mode-selector.component.html',
  styleUrl: './mode-selector.component.css'
})
export class ModeSelectorComponent {
  modes = MODES;

  currentLaserMode: string = MODES[0];

  constructor(private dmxService: DmxService) {}

  changeLaserMode(mode: string) {
    this.currentLaserMode = mode;
    this.dmxService.setMode(mode).subscribe();
  }
}
