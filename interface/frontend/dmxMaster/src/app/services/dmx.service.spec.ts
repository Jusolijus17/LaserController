import { TestBed } from '@angular/core/testing';

import { DmxService } from './dmx.service';

describe('DmxService', () => {
  let service: DmxService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(DmxService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
