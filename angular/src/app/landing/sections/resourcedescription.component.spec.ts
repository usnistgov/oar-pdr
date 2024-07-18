import { ComponentFixture, TestBed, ComponentFixtureAutoDetect, waitForAsync  } from '@angular/core/testing';
import { DatePipe } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';

import { ToastrModule } from 'ngx-toastr';

import { AppConfig } from '../../config/config';
import { NerdmRes } from '../../nerdm/nerdm';
import { ResourceDescriptionComponent } from './resourcedescription.component';
import { SectionsModule } from './sections.module';
import { EditControlModule } from '../editcontrol/editcontrol.module';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';
import { AuthService, WebAuthService, MockAuthService } from '../editcontrol/auth.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';

import { config, testdata } from '../../../environments/environment';

describe('ResourceDescriptionComponent', () => {
    let component : ResourceDescriptionComponent;
    let fixture : ComponentFixture<ResourceDescriptionComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec : NerdmRes = testdata['test1'];
    let authsvc : AuthService = new MockAuthService()

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ HttpClientModule, SectionsModule ],
            declarations: [  ],
            providers: [
                { provide: AppConfig, useValue: cfg },
                { provide: AuthService, useValue: authsvc }, 
                GoogleAnalyticsService, UserMessageService, MetadataUpdateService, DatePipe
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(ResourceDescriptionComponent);
        component = fixture.componentInstance;
        component.record = JSON.parse(JSON.stringify(rec));
        // fixture.detectChanges();
    }

    beforeEach(waitForAsync(() => {
        makeComp();
        component.inBrowser = true;
        component.collection = "Semiconductors";
        fixture.detectChanges();
    }));

    it('should initialize', () => {
        expect(component).toBeDefined();
        let cmpel = fixture.nativeElement;
        
        let el = cmpel.querySelector("h3");
        expect(el).not.toBeNull();
        expect(el.textContent).toContain("Description");
    });

    it('isDataPublication', () => {
        expect(component).toBeDefined();
        expect(component.isDataPublication()).toBeFalsy();
        let cmpel = fixture.nativeElement;
        
        component.record['@type'].push("nrdp:DataPublication");
        expect(component.isDataPublication()).toBeTruthy();
        component.useMetadata();
        
        fixture.detectChanges();
        let el = cmpel.querySelector("h3");
        expect(el).not.toBeNull();
        expect(el.textContent).toContain("Abstract");
    });
})
