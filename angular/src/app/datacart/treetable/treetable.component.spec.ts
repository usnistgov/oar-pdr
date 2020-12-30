import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { TreetableComponent } from './treetable.component';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { CartService } from '../../datacart/cart.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestDataService } from '../../shared/testdata-service/testDataService';

describe('TreetableComponent', () => {
  let component: TreetableComponent;
  let fixture: ComponentFixture<TreetableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TreetableComponent ],
      schemas: [NO_ERRORS_SCHEMA],
      imports: [
        HttpClientTestingModule],
      providers: [
        CartService,
        DownloadService,
        TestDataService,
        GoogleAnalyticsService]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TreetableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
