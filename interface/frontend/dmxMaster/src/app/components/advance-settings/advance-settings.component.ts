import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DmxService } from '../../services/dmx.service';
import { DEFAULT_OLA_IP, DEFAULT_OLA_PORT } from '../../constants';

@Component({
  selector: 'app-advance-settings',
  standalone: true,
  imports: [HttpClientModule, CommonModule, FormsModule],
  templateUrl: './advance-settings.component.html',
  styleUrl: './advance-settings.component.css'
})
export class AdvanceSettingsComponent {
  advancedSettingsEnabled: boolean = false;
  verticalAdjust: number = 63;
  verticalAnimationEnabled: boolean = false;
  verticalAnimationSpeed: number = 127;
  horizontalAnimationEnabled: boolean = false;
  horizontalAnimationSpeed: number = 127;

  olaIp: string = '';
  olaPort: string = '';
  ipSaved: boolean = true;
  portSaved: boolean = true;

  get horizontalAnimationSpeedPercent() {
    return Math.round(
      ((this.horizontalAnimationSpeed - 127) / (190 - 127)) * 100
    );
  }

  get verticalAnimationSpeedPercent() {
    return Math.round(
      ((this.verticalAnimationSpeed - 127) / (190 - 127)) * 100
    );
  }

  constructor(private dmxService: DmxService) {
    this.getIp();
  }

  onVerticalAdjustChange() {
    this.dmxService.setHorizontalAdjust(this.verticalAdjust).subscribe();
  }

  resetVerticalAdjust() {
    this.verticalAdjust = 63;
    this.dmxService.setHorizontalAdjust(this.verticalAdjust).subscribe();
  }

  onVerticalAnimationChange() {
    this.dmxService
      .setVerticalAnimation(
        this.verticalAnimationEnabled,
        this.verticalAnimationSpeed
      )
      .subscribe();
  }

  onHorizontalAnimationChange() {
    this.dmxService
      .setHorizontalAnimation(
        this.horizontalAnimationEnabled,
        this.horizontalAnimationSpeed
      )
      .subscribe();
  }

  onHorizontalAnimationEnable() {
    this.dmxService
      .setHorizontalAnimation(
        this.horizontalAnimationEnabled,
        this.horizontalAnimationSpeed
      )
      .subscribe();
  }

  onVerticalAnimationEnable() {
    this.dmxService
      .setVerticalAnimation(
        this.verticalAnimationEnabled,
        this.verticalAnimationSpeed
      )
      .subscribe();
  }

  onIpChange() {
    this.ipSaved = false;
  }

  onPortChange() {
    this.portSaved = false;
  }

  saveIp() {
    const ip = this.olaIp.length === 0 ? DEFAULT_OLA_IP : this.olaIp;
    const port = this.olaPort.length === 0 ? DEFAULT_OLA_PORT : this.olaPort;
    if (!this.ipSaved) {
      this.dmxService.setOlaIp(ip).subscribe(() => {
        this.ipSaved = true;
      });
    }
    if (!this.portSaved) {
      this.dmxService.setOlaPort(port).subscribe(() => {
        this.portSaved = true;
      });
    }
  }

  getIp() {
    this.dmxService.getOlaIp().subscribe((data: any) => {
      if (data.ip !== DEFAULT_OLA_IP) {
        this.olaIp = data.ip;
      }
      if (data.port !== DEFAULT_OLA_PORT) {
        this.olaPort = data.port;
      }
    });
  }
}
