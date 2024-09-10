import { ComponentFixture, TestBed, ComponentFixtureAutoDetect, waitForAsync  } from '@angular/core/testing';
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
import { D3Service } from '../../shared/d3-service/d3.service';
import { config, testdata } from '../../../environments/environment';
import { Themes, ThemesPrefs } from '../../shared/globals/globals';
import { CollectionService } from '../../shared/collection-service/collection.service';

describe('ResourceDataComponent', () => {
    let component: ResourceDataComponent;
    let fixture: ComponentFixture<ResourceDataComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec : NerdmRes = require('../../../assets/sampleRecord.json');

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ HttpClientModule, SectionsModule, RouterTestingModule ],
            declarations: [  ],
            providers: [
                { provide: AppConfig, useValue: cfg },
                GoogleAnalyticsService, UserMessageService, MetadataUpdateService, DatePipe,
                CartService, D3Service, CollectionService
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(ResourceDataComponent);
        component = fixture.componentInstance;
        component.colorScheme = {
            default: "#003c97",
            light: "#e3efff",
            lighter: "#f7f7fa",
            dark: "#00076c",
            hover: "#ffffff"
        };
        console.log("component.colorScheme.default", component.colorScheme.default)
    }

    beforeEach(waitForAsync(() => {
        makeComp();
        component.inBrowser = true;
        component.record = JSON.parse(JSON.stringify(rec));
        component.theme = Themes.DEFAULT_THEME;

        component.ngOnChanges({});
        fixture.detectChanges();
    }));

    it('should initialize', () => {
        expect(component).toBeTruthy();
        let cmpel = fixture.nativeElement;
        expect(cmpel.querySelector("#dataAccess")).toBeTruthy();

        // lists access pages
        expect(cmpel.querySelector("#accessPages")).toBeTruthy();

        // shows access rights
        expect(cmpel.querySelector("#accessRights")).toBeTruthy();

        // lists files
        expect(cmpel.querySelector("#filelisting")).toBeTruthy();
    });
});
