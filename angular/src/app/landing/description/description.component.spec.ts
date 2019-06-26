import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { DescriptionComponent } from './description.component';
import { FormsModule } from '@angular/forms';
import { CartService } from '../../datacart/cart.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { TestDataService } from '../../shared/testdata-service/testDataService';
import { CommonVarService } from '../../shared/common-var';
import { AppConfig } from '../../config/config';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';
// import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

describe('DescriptionPopupComponent', () => {
  let component: DescriptionComponent;
  let fixture: ComponentFixture<DescriptionComponent>;
  let cfg : AppConfig;
  let plid : Object = "browser";
  let ts : TransferState = new TransferState();

  beforeEach(async(() => {
    cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
    cfg.locations.pdrSearch = "https://goob.nist.gov/search";
    cfg.status = "Unit Testing";
    cfg.appVersion = "2.test";

    TestBed.configureTestingModule({
      declarations: [ DescriptionComponent ],
      imports: [FormsModule,        
        RouterTestingModule,
        HttpClientTestingModule],
      schemas: [NO_ERRORS_SCHEMA],
      providers: [
        CartService, 
        DownloadService, 
        TestDataService, 
        CommonVarService,
        { provide: AppConfig, useValue: cfg }]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    let record: any = require('../../../assets/sampleRecord.json');
    let files: any = require('../../../assets/files.json');
    fixture = TestBed.createComponent(DescriptionComponent);
    component = fixture.componentInstance;
    component.record = record;
    component.files = files;
    component.distdownload = "/od/ds/zip?id=ark:/88434/mds0149s9z";
    component.filescount = 8;
    component.metadata = false;
    component.recordEditmode = false;
    component.inBrowser = true;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('Should have title Description', () => {
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('h3').innerText).toEqual('Description');
  });

  it('Description should contains This software provides a framework', () => {
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('#recordDescription').innerText).toContain('This software provides a framework');
  });

  it('Research Topics should contains Manufacturing: Factory communications', () => {
    let cmpel = fixture.nativeElement;
    let aels = cmpel.querySelectorAll(".topics");
    expect(aels.length).toEqual(3);
    expect(aels[0].innerText).toContain('Manufacturing: Factory communications');
  });

  it('Subject Keywords should Wireless', () => {
    let cmpel = fixture.nativeElement;
    let aels = cmpel.querySelectorAll(".keywords");
    expect(aels.length).toEqual(5);
    expect(aels[0].innerText).toContain('IoT');
    expect(aels[1].innerText).toContain('Wireless');
    expect(aels[2].innerText).toContain('RF');
    expect(aels[3].innerText).toContain('Manufacturing');
    expect(aels[4].innerText).toContain('Node.js');
  });

  it('Totle files should be 3', () => {
    expect(component.totalFiles).toEqual(3);
  });

  it('cartProcess() should be called', () => {
    let cmpel = fixture.nativeElement;
    let aels = cmpel.querySelectorAll("span")[17];
    spyOn(component, 'cartProcess');
    aels.click();
    expect(component.cartProcess).toHaveBeenCalled();
  });
});
