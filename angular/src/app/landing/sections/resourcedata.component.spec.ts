import { async, ComponentFixture, TestBed, ComponentFixtureAutoDetect } from '@angular/core/testing';
import { DatePipe } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';

import { ResourceDataComponent } from './resourcedata.component';
import { SectionsModule } from './sections.module';

import { AppConfig } from '../../config/config';
import { NerdmRes, NerdmComp } from '../../nerdm/nerdm';
import { EditControlModule } from '../editcontrol/editcontrol.module';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';
import { AuthService, WebAuthService, MockAuthService } from '../editcontrol/auth.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { CartService } from '../../datacart/cart.service';

import { config, testdata } from '../../../environments/environment';

fdescribe('ResourceDataComponent', () => {
    let component: ResourceDataComponent;
    let fixture: ComponentFixture<ResourceDataComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec : NerdmRes = require('../../../assets/sampleRecord.json');
    let authsvc : AuthService = new MockAuthService()

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ HttpClientModule, SectionsModule, RouterTestingModule ],
            declarations: [  ],
            providers: [
                { provide: AppConfig, useValue: cfg },
                { provide: AuthService, useValue: authsvc }, 
                GoogleAnalyticsService, UserMessageService, MetadataUpdateService, DatePipe,
                CartService
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(ResourceDataComponent);
        component = fixture.componentInstance;
    }

    beforeEach(async(() => {
        makeComp();
        component.inBrowser = true;
        component.record = JSON.parse(JSON.stringify(rec));
        component.ngOnChanges({});
        fixture.detectChanges();
    }));

    it('should initialize', () => {
        expect(component).toBeTruthy();
        let cmpel = fixture.nativeElement;
        expect(cmpel.querySelector("#dataAccess")).toBeTruthy();

        // has a title
        let el = cmpel.querySelector("h3");
        expect(el).toBeTruthy();
        expect(el.textContent).toContain("Data Access");

        // lists access pages
        expect(cmpel.querySelector("#accessPages")).toBeTruthy();

        // shows access rights
        expect(cmpel.querySelector("#accessRights")).toBeTruthy();

        // lists files
        expect(cmpel.querySelector("#filelisting")).toBeTruthy();
    });

    it('selectAccessPages()', () => {
        expect(component).toBeTruthy();
        expect(component.record).toBeTruthy();
        expect(component.record['components']).toBeTruthy();
        expect(component.record['components'].length).toBeGreaterThan(0);

        let aps: NerdmComp[] = component.selectAccessPages(component.record['components']);
        expect(aps.length).toBe(1);
        expect(aps[0]['accessURL']).toBeTruthy();
    });
});
