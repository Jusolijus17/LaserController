import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdvanceSettingsComponent } from './advance-settings.component';

describe('AdvanceSettingsComponent', () => {
  let component: AdvanceSettingsComponent;
  let fixture: ComponentFixture<AdvanceSettingsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdvanceSettingsComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(AdvanceSettingsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
