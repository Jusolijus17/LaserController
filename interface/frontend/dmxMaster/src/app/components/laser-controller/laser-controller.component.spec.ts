import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LaserControllerComponent } from './laser-controller.component';

describe('LaserControllerComponent', () => {
  let component: LaserControllerComponent;
  let fixture: ComponentFixture<LaserControllerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LaserControllerComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(LaserControllerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
