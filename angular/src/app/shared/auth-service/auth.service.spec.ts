import { TestBed, async } from '@angular/core/testing';

import { AuthService } from './auth.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { CommonVarService } from '../common-var/common-var.service';
import { RouterTestingModule } from '@angular/router/testing';
import { AppConfig } from '../../config/config';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';

describe('AuthService', () => {
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();
    beforeEach(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        TestBed.configureTestingModule({
        imports: [HttpClientTestingModule, RouterTestingModule],
        providers: [
            { provide: CommonVarService },
            { provide: AppConfig, useValue: cfg }
        ]
    })});

    it('should be created', async(() => {
        const service: AuthService = TestBed.get(AuthService);
        expect(service).toBeTruthy();
    }));
});
