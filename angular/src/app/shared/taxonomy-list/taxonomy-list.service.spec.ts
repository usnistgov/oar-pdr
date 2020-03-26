import { TestBed } from '@angular/core/testing';

import { TaxonomyListService } from './taxonomy-list.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { RouterModule } from '@angular/router';
import { Location } from '@angular/common';
import { AppConfig } from '../../config/config'
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';

describe('TaxonomyListService', () => {
  let cfg : AppConfig;
  let plid : Object = "browser";
  let ts : TransferState = new TransferState();

  it('should be created', () => {
    cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterModule, RouterTestingModule],
      providers: [Location,{ provide: AppConfig, useValue: cfg}]
    })

    const service: TaxonomyListService = TestBed.get(TaxonomyListService);
    expect(service).toBeTruthy();
  });
});
