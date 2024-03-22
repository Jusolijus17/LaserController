import { Component } from '@angular/core';
import { DmxService } from '../../services/dmx.service';
import { HttpClientModule } from '@angular/common/http';
import { COLORS } from '../../interfaces/color';
import { Pattern, PATTERNS } from '../../interfaces/patterns';
import { CommonModule } from '@angular/common';

export enum BPMSyncTypes {
  PATTERN = 'pattern',
  COLOR = 'color',
  ALL = 'all',
  NONE = 'none'
}

@Component({
  selector: 'app-laser-controller',
  standalone: true,
  imports: [HttpClientModule, CommonModule],
  providers: [DmxService],
  templateUrl: './laser-controller.component.html',
  styleUrl: './laser-controller.component.css'
})
export class LaserControllerComponent {
  // Exposers
  patterns = PATTERNS;
  bpmSyncTypes = BPMSyncTypes;

  // Private
  currentColorIndex = 0;
  currentPatternIndex = 0;
  currentBpmSyncType = BPMSyncTypes.NONE;

  get currentColor() {
    return COLORS[this.currentColorIndex];
  }

  get currentPattern() {
    return PATTERNS[this.currentPatternIndex];
  }

  constructor(private dmxService: DmxService) {}

  bpmSync(type: BPMSyncTypes) {
    if (type === this.currentBpmSyncType) {
      this.currentBpmSyncType = BPMSyncTypes.NONE;
    } else {
      this.currentBpmSyncType = type;
    }
    this.dmxService.setSyncMode(this.currentBpmSyncType).subscribe();
  }

  changeLaserColor() {
    this.currentColorIndex = (this.currentColorIndex + 1) % COLORS.length;
    this.dmxService.setColor(this.currentColor.name).subscribe({});
  }

  setPattern(pattern: Pattern) {
    this.currentPatternIndex = PATTERNS.indexOf(pattern);
    this.dmxService.setPattern(pattern.name).subscribe();
  }

  sendDmx() {
    this.dmxService.setDmx({}).subscribe();
  }
}
