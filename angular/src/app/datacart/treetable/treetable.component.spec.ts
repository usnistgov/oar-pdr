import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { TreetableComponent } from './treetable.component';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { CartService } from '../../datacart/cart.service';
import { DataCart } from '../../datacart/cart';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestDataService } from '../../shared/testdata-service/testDataService';
import { TreeTableModule } from 'primeng/treetable';

describe('TreetableComponent', () => {
  let component: TreetableComponent;
  let fixture: ComponentFixture<TreetableComponent>;

  beforeEach(async(() => {
    let dc: DataCart = DataCart.openCart("goob");
    dc._forget();
    dc.addFile("foo", { filePath: "bar/goo",  count: 3, downloadURL: "http://here", resTitle: "fooishness" },
               false, false);
    dc.addFile("foo", { filePath: "bar/good", count: 3, downloadURL: "http://here", resTitle: "fooishness" },
               false, false);
    dc.save();
    
    TestBed.configureTestingModule({
      declarations: [ TreetableComponent ],
      schemas: [NO_ERRORS_SCHEMA],
      imports: [
        TreeTableModule,
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
    component.cartName = "goob";
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
