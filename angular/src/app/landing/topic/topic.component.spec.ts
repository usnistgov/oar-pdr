import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { TopicModule, TopicComponent } from './topic.module';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { FormsModule } from '@angular/forms';
import { AppConfig } from '../../config/config';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { DatePipe } from '@angular/common';
import { ToastrModule } from 'ngx-toastr';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';
import { AuthService, WebAuthService, MockAuthService } from '../editcontrol/auth.service';

describe('TopicComponent', () => {
    let component: TopicComponent;
    let fixture: ComponentFixture<TopicComponent>;
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();
    let authsvc : AuthService = new MockAuthService(undefined);

    beforeEach(waitForAsync(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";

        TestBed.configureTestingModule({
            imports: [TopicModule, FormsModule, HttpClientTestingModule, RouterTestingModule,
                      ToastrModule.forRoot()],
            declarations: [],
            providers: [
                MetadataUpdateService, UserMessageService, DatePipe,
                { provide: AppConfig, useValue: cfg },
                { provide: AuthService, useValue: authsvc }
            ]
        })
            .compileComponents();
    }));

    beforeEach(() => {
        let record: any = require('../../../assets/sample-data/pdr0-0002-new.json');
        console.log('record.topic', record.topic);
        fixture = TestBed.createComponent(TopicComponent);
        component = fixture.componentInstance;
        component.record = record;
        component.inBrowser = true;
        component.collection = "Semiconductors";
        component.allCollections["Semiconductors"] = {};
        component.allCollections["Semiconductors"].tag = "CHIPS Metrology Topics";
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('Research Topics should contains Materials: Ceramics', () => {
        let cmpel = fixture.nativeElement;
        let aels = cmpel.querySelectorAll(".topics");
        expect(aels.length).toEqual(6);
        expect(aels[0].innerText).toContain('Materials: Ceramics');
      });
    
});
