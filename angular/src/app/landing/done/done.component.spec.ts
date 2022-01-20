import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';

import { DoneComponent } from './done.component';

describe('DoneComponent', () => {
  let component: DoneComponent;
  let fixture: ComponentFixture<DoneComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DoneComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DoneComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
