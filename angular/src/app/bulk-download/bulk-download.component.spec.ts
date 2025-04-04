import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BulkDownloadComponent } from './bulk-download.component';

describe('BulkDownloadComponent', () => {
  let component: BulkDownloadComponent;
  let fixture: ComponentFixture<BulkDownloadComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BulkDownloadComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BulkDownloadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
