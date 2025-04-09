import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, Routes } from '@angular/router';
import { BulkDownloadComponent } from './bulk-download.component';
import * as mock from '../testing/mock.services';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

describe('BulkDownloadComponent', () => {
  let component: BulkDownloadComponent;
  let fixture: ComponentFixture<BulkDownloadComponent>;
  let route : ActivatedRoute;

  beforeEach(async () => {
    let path = "/bulkdownload";
    let params = {};
    let r : unknown = new mock.MockActivatedRoute(path, params);
    route = r as ActivatedRoute;

    await TestBed.configureTestingModule({
      declarations: [ BulkDownloadComponent ],
      imports: [ NoopAnimationsModule ],
      providers: [
        { provide: ActivatedRoute,  useValue: route },
      ]
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
