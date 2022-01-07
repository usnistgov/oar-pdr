import { ComponentFixture, TestBed, waitForAsync as  } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { AuthorComponent } from './author.component';
import { FormsModule } from '@angular/forms';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { AppConfig } from '../../config/config';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { RouterTestingModule } from '@angular/router/testing';
import { DatePipe } from '@angular/common';
import { ToastrModule } from 'ngx-toastr';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';
import { AuthService, WebAuthService, MockAuthService } from '../editcontrol/auth.service';
import { testdata } from '../../../environments/environment';

describe('AuthorComponent', () => {
    let component: AuthorComponent;
    let fixture: ComponentFixture<AuthorComponent>;
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();
    let authsvc: AuthService = new MockAuthService(undefined);
    let rec = testdata['test2'];

    beforeEach(waitForAsync(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";

        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule, FormsModule, RouterTestingModule, ToastrModule.forRoot()],
            declarations: [AuthorComponent],
            schemas: [NO_ERRORS_SCHEMA],
            providers: [
                MetadataUpdateService, UserMessageService, DatePipe,
                { provide: AppConfig, useValue: cfg },
                { provide: AuthService, useValue: authsvc }
            ]
        })
            .compileComponents();
    }));

    beforeEach(() => {
        // let record: any = require('../../../assets/sampleRecord.json');
        fixture = TestBed.createComponent(AuthorComponent);
        component = fixture.componentInstance;
        component.record = rec;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
        expect(component.fieldName).toEqual("authors");
    });

    it('should have ORCID icon image displayed', () => {
        expect(component).toBeTruthy();
        expect(component.record['authors']).toBeTruthy();
        expect(component.record['authors'].length).toEqual(2);
        let cmpel = fixture.nativeElement;

        let els = cmpel.querySelectorAll(".authorsbrief img"); 
        expect(els).toBeTruthy();
        expect(els.length).toEqual(1);
    });
});
