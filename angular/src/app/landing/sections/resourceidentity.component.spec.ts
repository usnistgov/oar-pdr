import { ComponentFixture, TestBed, ComponentFixtureAutoDetect, waitForAsync  } from '@angular/core/testing';
import { DatePipe } from '@angular/common';

import { ToastrModule } from 'ngx-toastr';

import { AppConfig } from '../../config/config';
import { NerdmRes } from '../../nerdm/nerdm';
import { ResourceIdentityComponent } from './resourceidentity.component';
import { SectionsModule } from './sections.module';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';
import { AuthService, WebAuthService, MockAuthService } from '../editcontrol/auth.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { config, testdata } from '../../../environments/environment';

describe('ResourceIdentityComponent', () => {
    let component : ResourceIdentityComponent;
    let fixture : ComponentFixture<ResourceIdentityComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec : NerdmRes = testdata['test1'];
    let authsvc : AuthService = new MockAuthService()

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ SectionsModule ],
            declarations: [  ],
            providers: [
                { provide: AppConfig, useValue: cfg },
                { provide: AuthService, useValue: authsvc },
                DatePipe, GoogleAnalyticsService, UserMessageService, MetadataUpdateService
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(ResourceIdentityComponent);
        component = fixture.componentInstance;
        rec["@type"][0] = "nrdp:PublicDataResource";
        rec["references"][0]["refType"] = "IsDocumentedBy";
        component.record = rec;
        // fixture.detectChanges();
    }

    beforeEach(waitForAsync(() => {
        makeComp();
        component.inBrowser = true;
        component.ngOnChanges()
        fixture.detectChanges();
    }));

    it('should initialize', () => {
        expect(component).toBeDefined();
        let cmpel = fixture.nativeElement;
        
        let el = cmpel.querySelector("h2"); 
        expect(el.textContent).toContain(rec.title);

        expect(component.record['version']).toBe("1.0.1");
        let descs = cmpel.querySelectorAll("p");
        expect(descs.length).toBe(1);

        // expect(component.versionCmp.newer).toBeNull();
    });

    it('should correctly render special references', () => {
        expect(component).toBeDefined();
        expect(component.primaryRefs.length).toEqual(1);
        let cmpel = fixture.nativeElement;

        let el = cmpel.querySelector(".describedin")
        expect(el).toBeTruthy();
        el = el.querySelector("a");
        expect(el.textContent).toContain("Solids: In-situ");

        let tstrec = JSON.parse(JSON.stringify(rec));
        delete tstrec['references'][0]['label'];
        component.record = tstrec;
        component.useMetadata();
        expect(component.primaryRefs[0]['label']).toEqual(component.primaryRefs[0]['title']);

        delete tstrec['references'][0]['title'];
        delete tstrec['references'][0]['label'];
        component.record = tstrec;
        component.useMetadata();
        expect(component.primaryRefs[0]['label']).toEqual(component.primaryRefs[0]['citation']);

        delete tstrec['references'][0]['citation'];
        delete tstrec['references'][0]['label'];
        component.record = tstrec;
        component.useMetadata();
        expect(component.primaryRefs[0]['label']).toEqual(component.primaryRefs[0]['location']);
    });
       
});

