import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientModule } from '@angular/common/http';
import { EditControlsComponent } from './edit-controls.component';
import { AppConfig } from '../../../config/config';
import { AngularEnvironmentConfigService } from '../../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { SharedService } from '../../../shared/shared';
import { RouterTestingModule } from '@angular/router/testing';
import { DatePipe } from '@angular/common';
import { ToastrModule } from 'ngx-toastr';

describe('EditControlsComponent', () => {
    let component: EditControlsComponent;
    let fixture: ComponentFixture<EditControlsComponent>;
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();

    beforeEach(async(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";

        TestBed.configureTestingModule({
            imports: [HttpClientModule, RouterTestingModule, ToastrModule.forRoot()],
            declarations: [EditControlsComponent],
            providers: [
                SharedService,
                DatePipe,
                { provide: AppConfig, useValue: cfg }]
        })
            .compileComponents();
    }));

    beforeEach(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";
        fixture = TestBed.createComponent(EditControlsComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
