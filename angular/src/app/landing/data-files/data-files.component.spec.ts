import { NO_ERRORS_SCHEMA } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { async, fakeAsync, tick, ComponentFixture, TestBed } from '@angular/core/testing';
import { DataFilesComponent } from './data-files.component';
import { FormsModule } from '@angular/forms';
import { CartService } from '../../datacart/cart.service';
import { DataCart } from '../../datacart/cart';
import { CartConstants } from '../../datacart/cartconstants';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { TestDataService } from '../../shared/testdata-service/testDataService';
import { AppConfig } from '../../config/config';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { ToastrModule } from 'ngx-toastr';
import { TreeTableModule } from 'primeng/treetable';

describe('DataFilesComponent', () => {
  let component: DataFilesComponent;
  let fixture: ComponentFixture<DataFilesComponent>;
  let cfg: AppConfig;
  let plid: Object = "browser";
  let ts: TransferState = new TransferState();

  beforeEach(async(() => {
    let dc: DataCart = DataCart.openCart(CartConstants.cartConst.GLOBAL_CART_NAME);
    dc._forget();

    cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
    cfg.locations.pdrSearch = "https://goob.nist.gov/search";
    cfg.status = "Unit Testing";
    cfg.appVersion = "2.test";

    TestBed.configureTestingModule({
      declarations: [DataFilesComponent],
      imports: [FormsModule,
        RouterTestingModule,
        HttpClientTestingModule,
        TreeTableModule,
        ToastrModule.forRoot()],
      schemas: [NO_ERRORS_SCHEMA],
      providers: [
        CartService,
        DownloadService,
        TestDataService,
        GoogleAnalyticsService,
        DatePipe,
        { provide: AppConfig, useValue: cfg }]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    let record: any = require('../../../assets/sampleRecord.json');
    fixture = TestBed.createComponent(DataFilesComponent);
    component = fixture.componentInstance;
    component.record = record;
    // component.distdownload = "/od/ds/zip?id=ark:/88434/mds0149s9z";
    // component.filescount = 8;
    // component.recordEditmode = false;
    component.inBrowser = true;
    component.ngOnChanges({});
    fixture.detectChanges();
  });

  afterEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
    expect(component.files.length > 0).toBeTruthy();
    expect(component.fileCount).toBe(3);
    expect(component.downloadStatus).not.toBe("downloaded");
    expect(component.allInCart).toBeFalsy();
  });

  it('Should have title Files', () => {
    expect(fixture.nativeElement.querySelectorAll('#filelist-heading').length).toEqual(1);
    expect(fixture.nativeElement.querySelector('#filelist-heading').innerText).toEqual('Files ');
  });

  it('Should have file tree table', () => {
    expect(fixture.nativeElement.querySelectorAll('th').length).toBeGreaterThan(0);
  });

  it('Empty display when there are no files', () => {
    let rec: any = JSON.parse(JSON.stringify(require('../../../assets/sampleRecord.json')));
    rec['components'] = []
    component.record = rec
    component.ngOnChanges({});
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('#filelist-heading').length).toEqual(0);
  });

  it('toggleAllFilesInGlobalCart() should be called', () => {
    let cmpel = fixture.nativeElement;
    let aels = cmpel.querySelectorAll(".icon-cart")[0];
    spyOn(component, 'toggleAllFilesInGlobalCart');
    aels.click();
    expect(component.toggleAllFilesInGlobalCart).toHaveBeenCalled();
  });

  it('_updateNodesFromCart()', async(() => {
    let dc: DataCart = DataCart.openCart("goob");
    dc.addFile(component.ediid, component.record.components[1]);
    expect(component._updateNodesFromCart(component.files, dc)).toBeFalsy();
  }));

  it('toggleAllFilesInGlobalCart()', fakeAsync(() => {
    let dc: DataCart = DataCart.openCart(CartConstants.cartConst.GLOBAL_CART_NAME);
    expect(dc.size()).toBe(0);
    component.toggleAllFilesInGlobalCart();
    tick(1);
    dc.restore();
    expect(dc.size()).toBe(2);
    component.toggleAllFilesInGlobalCart()
    tick(1);
    dc.restore();
    expect(dc.size()).toBe(0);
  }));
});
