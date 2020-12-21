import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CartcontrolComponent } from './cartcontrol.component';

describe('CartcontrolComponent', () => {
  let component: CartcontrolComponent;
  let fixture: ComponentFixture<CartcontrolComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CartcontrolComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CartcontrolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
