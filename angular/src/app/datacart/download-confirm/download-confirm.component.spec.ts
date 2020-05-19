import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DownloadConfirmComponent } from './download-confirm.component';

describe('DownloadConfirmComponent', () => {
  let component: DownloadConfirmComponent;
  let fixture: ComponentFixture<DownloadConfirmComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DownloadConfirmComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DownloadConfirmComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
