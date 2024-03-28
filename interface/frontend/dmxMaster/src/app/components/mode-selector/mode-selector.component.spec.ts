import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModeSelectorComponent } from './mode-selector.component';

describe('ModeSelectorComponent', () => {
  let component: ModeSelectorComponent;
  let fixture: ComponentFixture<ModeSelectorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ModeSelectorComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ModeSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
