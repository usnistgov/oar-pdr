import { async, ComponentFixture, TestBed, ComponentFixtureAutoDetect } from '@angular/core/testing';
import { DatePipe } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';

import { LandingBodyComponent } from './landingbody.component';
import { SectionsModule } from './sections/sections.module';

import { AppConfig } from '../config/config';
import { NerdmRes, NerdmComp } from '../nerdm/nerdm';
import { MetadataUpdateService } from './editcontrol/metadataupdate.service';
import { UserMessageService } from '../frame/usermessage.service';
import { AuthService, WebAuthService, MockAuthService } from './editcontrol/auth.service';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';
import { CartService } from '../datacart/cart.service';

import { config, testdata } from '../../environments/environment';

describe('LandingBodyComponent', () => {
    let component: LandingBodyComponent;
    let fixture: ComponentFixture<LandingBodyComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec : NerdmRes = testdata['test1'];
    let authsvc : AuthService = new MockAuthService()

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ HttpClientModule, SectionsModule, RouterTestingModule ],
            declarations: [ LandingBodyComponent ],
            providers: [
                { provide: AppConfig, useValue: cfg },
                { provide: AuthService, useValue: authsvc }, 
                GoogleAnalyticsService, UserMessageService, MetadataUpdateService, DatePipe,
                CartService
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(LandingBodyComponent);
        component = fixture.componentInstance;
    }

    beforeEach(async(() => {
        makeComp();
        component.inBrowser = true;
        component.md = JSON.parse(JSON.stringify(rec));
        fixture.detectChanges();
    }));

    it('should initialize', () => {
        expect(component).toBeTruthy();
        let cmpel = fixture.nativeElement;
        expect(cmpel.querySelector("#resourcebody")).toBeTruthy();

        let sect = cmpel.querySelector("#identity");
        expect(sect).toBeTruthy();
        expect(sect.querySelector("h2")).toBeTruthy();

        sect = cmpel.querySelector("#description")
        expect(sect).toBeTruthy();
        expect(sect.querySelector("h3")).toBeTruthy();

        sect = cmpel.querySelector("#dataAccess")
        expect(sect).toBeTruthy();
        expect(sect.querySelector("h3")).toBeTruthy();

        sect = cmpel.querySelector("#references")
        expect(sect).toBeTruthy();
        expect(sect.querySelector("h3")).toBeTruthy();

    });
});
