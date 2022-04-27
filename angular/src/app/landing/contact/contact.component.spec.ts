import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ContactComponent } from './contact.component';
import { FormsModule } from '@angular/forms';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { AppConfig } from '../../config/config';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { RouterTestingModule } from '@angular/router/testing';
import { DatePipe } from '@angular/common';
import { ToastrModule } from 'ngx-toastr';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';
import { AuthService, WebAuthService, MockAuthService } from '../editcontrol/auth.service';

describe('ContactComponent', () => {
    let component: ContactComponent;
    let fixture: ComponentFixture<ContactComponent>;
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();
    let authsvc: AuthService = new MockAuthService(undefined);

    beforeEach(waitForAsync(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";

        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule, FormsModule, RouterTestingModule, ToastrModule.forRoot()],
            declarations: [ContactComponent],
            schemas: [NO_ERRORS_SCHEMA],
            providers: [
                MetadataUpdateService, UserMessageService, DatePipe,
                GoogleAnalyticsService,
                { provide: AppConfig, useValue: cfg },
                { provide: AuthService, useValue: authsvc }
            ]
        })
            .compileComponents();
    }));

    beforeEach(() => {
        let record: any = require('../../../assets/sampleRecord.json');
        fixture = TestBed.createComponent(ContactComponent);
        component = fixture.componentInstance;
        component.record = record;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
