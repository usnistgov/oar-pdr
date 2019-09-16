import { async, TestBed } from '@angular/core/testing';

import { CustomizationServiceService } from './customization-service.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { CommonVarService } from '../common-var/common-var.service';
import { RouterTestingModule } from '@angular/router/testing';
import { AppConfig } from '../../config/config';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';

describe('CustomizationServiceService', () => {
  let cfg: AppConfig;
  let plid: Object = "browser";
  let ts: TransferState = new TransferState();

  beforeEach(() => {
    cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
    cfg.customizationAPI = "http://localhost:8085/customization/";
    TestBed.configureTestingModule({
    imports: [HttpClientTestingModule, RouterTestingModule],
    providers: [
      { provide: CommonVarService },
      { provide: AppConfig, useValue: cfg }
    ]
  })});

  it('should be created', () => {
    const service: CustomizationServiceService = TestBed.get(CustomizationServiceService);
    expect(service).toBeTruthy();
  });
});
