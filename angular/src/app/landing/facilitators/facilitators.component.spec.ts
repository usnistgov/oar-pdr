import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FacilitatorsComponent } from './facilitators.component';

describe('FacilitatorsComponent', () => {
  let component: FacilitatorsComponent;
  let fixture: ComponentFixture<FacilitatorsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ FacilitatorsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(FacilitatorsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
