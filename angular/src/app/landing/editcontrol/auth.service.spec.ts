import { async, TestBed } from '@angular/core/testing';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { AuthService, WebAuthService, MockAuthService } from './auth.service';
import { CustomizationService } from './customization.service';
import { AppConfig } from '../../config/config';

import { testdata, config } from '../../../environments/environment';

fdescribe('WebAuthService', () => {

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

fdescribe('MockAuthService', () => {

    let rec = testdata['test1'];
    let svc : MockAuthService = null;

    beforeEach(() => {
        svc = new MockAuthService(rec);
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

