import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { AppConfig } from '../../config/config';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { MetricsinfoComponent } from './metricsinfo.component';
import { HttpClientTestingModule } from '@angular/common/http/testing';

describe('MetricsinfoComponent', () => {
  let component: MetricsinfoComponent;
  let fixture: ComponentFixture<MetricsinfoComponent>;
  let cfg: AppConfig;
  let plid: Object = "browser";
  let ts: TransferState = new TransferState();

  beforeEach(waitForAsync(() => {
    cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;

    TestBed.configureTestingModule({
      declarations: [ MetricsinfoComponent ],
      imports: [HttpClientTestingModule],
      providers: [
        { provide: AppConfig, useValue: cfg }
    ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MetricsinfoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
