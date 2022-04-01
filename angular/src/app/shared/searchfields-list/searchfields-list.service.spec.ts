import { TestBed } from '@angular/core/testing';

import { SearchfieldsListService } from './searchfields-list.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { RouterModule } from '@angular/router';
import { Location } from '@angular/common';
import { AppConfig } from '../../config/config'
import { TransferState } from '@angular/platform-browser';
import { AngularEnvironmentConfigService } from '../../config/config.service';

describe('SearchfieldsListService', () => {
    let plid : Object = "browser";
    let ts : TransferState = new TransferState();
    let cfg : AppConfig = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;

    beforeEach(() => TestBed.configureTestingModule({
        imports: [HttpClientTestingModule, RouterModule, RouterTestingModule],
        providers: [
            Location,
            { provide: AppConfig,       useValue: cfg }
        ]
    }));

    it('should be created', () => {
        const service: SearchfieldsListService = TestBed.get(SearchfieldsListService);
        expect(service).toBeTruthy();
    });
});
