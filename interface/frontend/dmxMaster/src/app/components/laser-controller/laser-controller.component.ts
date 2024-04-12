import { Component } from '@angular/core';
import { DmxService } from '../../services/dmx.service';
import { HttpClientModule } from '@angular/common/http';
import { COLORS } from '../../interfaces/color';
import { Pattern, PATTERNS } from '../../interfaces/patterns';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export enum BPMSyncTypes {
  PATTERN = 'pattern',
  COLOR = 'color',
  ALL = 'all',
  NONE = 'none'
}

@Component({
  selector: 'app-laser-controller',
  standalone: true,
  imports: [HttpClientModule, CommonModule, FormsModule],
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
  patternIntervalId: any;
  activeSyncTypes = new Set<BPMSyncTypes>();

  get currentColor() {
    return COLORS[this.currentColorIndex];
  }

  get currentPattern() {
    return PATTERNS[this.currentPatternIndex];
  }

  constructor(private dmxService: DmxService) { }

  toggleBpmSync(type: BPMSyncTypes) {
    if (this.activeSyncTypes.has(type)) {
      this.activeSyncTypes.delete(type);
      if (type === BPMSyncTypes.PATTERN) {
        clearInterval(this.patternIntervalId);
        this.patternIntervalId = null;
      }
    } else {
      this.activeSyncTypes.add(type);
      if (type === BPMSyncTypes.PATTERN) {
        this.patternIntervalId = setInterval(() => {
          this.currentPatternIndex =
            (this.currentPatternIndex + 1) % PATTERNS.length;
        }, 500);
      }
    }

    this.updateSyncMode();
  }

  updateSyncMode() {
    const syncModes = Array.from(this.activeSyncTypes).join(',');
    this.dmxService.setSyncMode(syncModes).subscribe();
  }

  changeLaserColor(specificColorName?: string) {
    if (specificColorName) {
      const colorIndex = COLORS.findIndex(
        color => color.name === specificColorName
      );
      if (colorIndex !== -1) {
        this.currentColorIndex = colorIndex;
      } else {
        console.warn(
          `La couleur spécifiée '${specificColorName}' n'existe pas dans COLORS.`
        );
      }
    } else {
      this.currentColorIndex = (this.currentColorIndex + 1) % COLORS.length;
    }
    this.dmxService.setColor(COLORS[this.currentColorIndex].name).subscribe({});
  }

  onIncludeChange() {
    console.log('onIncludeChange');
    this.dmxService.setPatternInclude(this.patterns).subscribe();
  }

  setPattern(pattern: Pattern) {
    this.currentPatternIndex = PATTERNS.indexOf(pattern);
    this.dmxService.setPattern(pattern.name).subscribe();
  }

  sendDmx() {
    this.dmxService.setDmx({}).subscribe();
  }
}
