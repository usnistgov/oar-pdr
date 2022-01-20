import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { DownloadConfirmComponent } from './download-confirm.component';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { config } from '../../../environments/environment';
import { AppConfig } from '../../config/config';

describe('DownloadConfirmComponent', () => {
  let component: DownloadConfirmComponent;
  let fixture: ComponentFixture<DownloadConfirmComponent>;
  let cfg : AppConfig = new AppConfig(config);

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DownloadConfirmComponent ],
      providers: [{ provide: AppConfig, useValue: cfg }, NgbActiveModal]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DownloadConfirmComponent);
    component = fixture.componentInstance;
    component.bundle_plan_size = 1000;
    component.zipData = [{
            fileName: "",
            downloadProgress: 0,
            downloadStatus: null,
            downloadInstance: null,
            bundle: null,
            downloadUrl: null,
            downloadErrorMessage: '',
            bundleSize: 0,
            downloadTime: 0
    }];
    component.totalFiles = 10;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('ContinueDownload()', waitForAsync(() => {
    spyOn(component.returnValue, 'emit');
    component.ContinueDownload();
    expect(component.returnValue.emit).toHaveBeenCalledWith(true);
  }));

  it('CancelDownload()', waitForAsync(() => {
    spyOn(component.returnValue, 'emit');

    component.CancelDownload();
     expect(component.returnValue.emit).toHaveBeenCalledWith(false);
  }));

  it('getBackColor()', waitForAsync(() => {
    expect(component.getBackColor(0)).toEqual('white');
    expect(component.getBackColor(1)).toEqual('rgb(231, 231, 231)');
  }));
});
