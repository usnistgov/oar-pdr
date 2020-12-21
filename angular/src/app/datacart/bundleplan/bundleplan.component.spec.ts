import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { BundleplanComponent } from './bundleplan.component';

describe('BundleplanComponent', () => {
  let component: BundleplanComponent;
  let fixture: ComponentFixture<BundleplanComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ BundleplanComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BundleplanComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
