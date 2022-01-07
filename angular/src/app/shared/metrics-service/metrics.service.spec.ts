import { inject, TestBed, waitForAsync as  } from '@angular/core/testing';
import { AppConfig } from '../../config/config';
import { MetricsService } from './metrics.service';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { TransferState } from '@angular/platform-browser';

describe('MetricsService', () => {
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();

    beforeEach(waitForAsync(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";

        TestBed.configureTestingModule({
        imports: [RouterTestingModule, HttpClientTestingModule],
        providers: [
            { provide: AppConfig, useValue: cfg }
        ]

        })
        .compileComponents();
        // fakerecords = makeRMMData();
        // let options = new ResponseOptions({ status: 200, body: JSON.stringify(fakerecords) });
        // response = new Response(options);
    }));

    it('should be created', () => {
        const service: MetricsService = TestBed.inject(MetricsService);
        expect(service).toBeTruthy();
    });
});
