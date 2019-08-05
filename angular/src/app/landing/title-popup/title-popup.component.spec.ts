import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TitlePopupComponent } from './title-popup.component';

describe('TitlePopupComponent', () => {
  let component: TitlePopupComponent;
  let fixture: ComponentFixture<TitlePopupComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TitlePopupComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TitlePopupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
