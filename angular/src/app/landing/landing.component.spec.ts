import { ElementRef } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { TransferState } from '@angular/platform-browser';
import { Title }    from '@angular/platform-browser';
import { ActivatedRoute, Router, Routes } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ModalService } from '../shared/modal-service';
import { ToastrModule } from 'ngx-toastr';

import { LandingModule } from './landing.module';
import { LandingComponent } from './landing.component';
import { AngularEnvironmentConfigService } from '../config/config.service';
import { AppConfig } from '../config/config'
import { NerdmRes } from '../nerdm/nerdm'
import { UserMessageService } from '../frame/usermessage.service';
import { CartService } from "../datacart/cart.service";
import { DownloadService } from "../shared/download-service/download-service.service";
import { TestDataService } from '../shared/testdata-service/testDataService';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';
import * as mock from '../testing/mock.services';
import {RouterTestingModule} from "@angular/router/testing";
import { DatePipe } from '@angular/common';
import { MetadataUpdateService } from './editcontrol/metadataupdate.service';
import { AuthService, WebAuthService, MockAuthService } from './editcontrol/auth.service';

import { testdata } from '../../environments/environment';

describe('LandingComponent', () => {
    let component : LandingComponent;
    let fixture : ComponentFixture<LandingComponent>;
    let cfg : AppConfig;
    let plid : Object = "browser";
    let ts : TransferState = new TransferState();
    let nrd : NerdmRes;
    let route : ActivatedRoute;
    let router : Router;
    let routes : Routes = [ ];
    let authsvc : AuthService = new MockAuthService(undefined);

    beforeEach(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";
        cfg.editEnabled = true;

        nrd = JSON.parse(JSON.stringify(testdata['test1']));
        /*
        nrd = {
            "@type": [ "nrd:SRD", "nrdp:DataPublication", "nrdp:DataPublicResource" ],
            "@id": "goober",
            title: "All About Me!"
        }
        */

        let r : unknown = new mock.MockActivatedRoute("/id/goober", {id: "goober"});
        route = r as ActivatedRoute;
    });

    let setupComponent = function() {
        TestBed.configureTestingModule({
            imports: [
                HttpClientModule, BrowserAnimationsModule, LandingModule,
                RouterTestingModule.withRoutes(routes),
                ToastrModule.forRoot({
                    toastClass: 'toast toast-bootstrap-compatibility-fix'
                })
            ],
            providers: [
                { provide: ActivatedRoute,  useValue: route },
                { provide: ElementRef,      useValue: null },
                { provide: AppConfig,       useValue: cfg },
                { provide: AuthService,     useValue: authsvc },
                UserMessageService,
                CartService, DownloadService, TestDataService, GoogleAnalyticsService, ModalService,
                MetadataUpdateService, DatePipe
            ]
        }).compileComponents();

        router = TestBed.get(Router);
        fixture = TestBed.createComponent(LandingComponent);
        component = fixture.componentInstance;
        component.record = nrd;
        component.inBrowser = true;
        component.requestId = "goober";
        fixture.detectChanges();
    }

    it("includes landing display", function() {
        setupComponent();
        let cmpel = fixture.nativeElement;
        let el = cmpel.querySelector("h2"); 
        expect(el.textContent).toContain(nrd.title);
    });
});
