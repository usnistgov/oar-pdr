import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ResultitemComponent } from './resultitem.component';

describe('ResultitemComponent', () => {
  let component: ResultitemComponent;
  let fixture: ComponentFixture<ResultitemComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ResultitemComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ResultitemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
