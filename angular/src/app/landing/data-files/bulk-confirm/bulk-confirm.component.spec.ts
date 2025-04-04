import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BulkConfirmComponent } from './bulk-confirm.component';

describe('BulkConfirmComponent', () => {
  let component: BulkConfirmComponent;
  let fixture: ComponentFixture<BulkConfirmComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BulkConfirmComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BulkConfirmComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
