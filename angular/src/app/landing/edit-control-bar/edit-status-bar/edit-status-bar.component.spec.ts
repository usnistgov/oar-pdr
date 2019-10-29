import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientModule } from '@angular/common/http';
import { EditStatusBarComponent } from './edit-status-bar.component';
import { AppConfig } from '../../../config/config';
import { AngularEnvironmentConfigService } from '../../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { SharedService } from '../../../shared/shared';
import { RouterTestingModule } from '@angular/router/testing';
import { DatePipe } from '@angular/common';

describe('EditStatusBarComponent', () => {
    let component: EditStatusBarComponent;
    let fixture: ComponentFixture<EditStatusBarComponent>;
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();

    beforeEach(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";

        TestBed.configureTestingModule({
            imports: [HttpClientModule, RouterTestingModule],
            declarations: [EditStatusBarComponent],
            providers: [
                SharedService,
                DatePipe,
                { provide: AppConfig, useValue: cfg }]
        })
            .compileComponents();
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(EditStatusBarComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
