import { async, TestBed } from '@angular/core/testing';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { TransferState } from '@angular/platform-browser';
import { of, throwError } from 'rxjs';

import { AuthService, WebAuthService, MockAuthService, createAuthService } from './auth.service';
import { CustomizationService } from './customization.service';
import { AppConfig } from '../../config/config';
import { AngularEnvironmentConfigService } from '../../config/config.service';

import { testdata, config } from '../../../environments/environment';

describe('WebAuthService', () => {

    let rec = testdata['test1'];
    let cfg = new AppConfig(config);
    let svc : WebAuthService = null;

    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [ HttpClientModule ]
        });
        svc = new WebAuthService(cfg, TestBed.get(HttpClient));
    });

    it('init state', () => {
        expect(svc.userID).toBeNull();
        expect(svc.endpoint).toBe(cfg.get('customizationAPI'));
        expect(svc.authToken).toBeNull();
        expect(svc.isAuthorized()).toBeFalsy();
    });
});

describe('MockAuthService', () => {

    let rec = testdata['test1'];
    let svc : MockAuthService = null;

    beforeEach(() => {
        svc = new MockAuthService();
    });

    it('init state', () => {
        expect(svc.userID).toBe("anon");
        expect(svc.isAuthorized()).toBeTruthy();
    });

    it('authorizeEditing()', async () => {
        let custsvc : CustomizationService = await svc.authorizeEditing(rec.ediid).toPromise();
        expect(custsvc).toBeTruthy();
        expect(await custsvc.getDraftMetadata().toPromise()).toEqual(rec);
    });
});

describe('createAuthService()', () => {
    let httpcli : HttpClient = null;
    let cfg : AppConfig;
    let plid : Object = "browser";
    let ts : TransferState = new TransferState();

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            imports: [ HttpClientModule ]
        });
        httpcli = TestBed.get(HttpClient);
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig();
    }));
    
    it('supports dev mode', () => {
        let as : AuthService = createAuthService(cfg, httpcli, true);
        expect(as instanceof MockAuthService).toBeTruthy();
    });

    it('supports prod mode', () => {
        let as : AuthService = createAuthService(cfg, httpcli, false);
        expect(as instanceof WebAuthService).toBeTruthy();
    });

});
