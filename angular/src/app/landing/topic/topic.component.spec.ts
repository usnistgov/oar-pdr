import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientModule } from '@angular/common/http';
import { TopicComponent } from './topic.component';
import { RouterTestingModule } from '@angular/router/testing';
import { SharedService } from '../../shared/shared';
import { FormsModule } from '@angular/forms';
import { AppConfig } from '../../config/config';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { DatePipe } from '@angular/common';
import { ToastrModule } from 'ngx-toastr';

describe('TopicComponent', () => {
    let component: TopicComponent;
    let fixture: ComponentFixture<TopicComponent>;
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();

    beforeEach(async(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";

        TestBed.configureTestingModule({
            imports: [FormsModule, HttpClientModule, RouterTestingModule, ToastrModule.forRoot()],
            declarations: [TopicComponent],
            providers: [
                SharedService,
                DatePipe,
                { provide: AppConfig, useValue: cfg }]
        })
            .compileComponents();
    }));

    beforeEach(() => {
        let record: any = require('../../../assets/sampleRecord.json');
        fixture = TestBed.createComponent(TopicComponent);
        component = fixture.componentInstance;
        component.record = record;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
