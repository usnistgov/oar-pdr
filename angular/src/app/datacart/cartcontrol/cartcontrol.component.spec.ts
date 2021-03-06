import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { AppConfig } from '../../config/config';
import { CartcontrolComponent } from './cartcontrol.component';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { CartService } from '../../datacart/cart.service';
import { TestDataService } from '../../shared/testdata-service/testDataService';

describe('CartcontrolComponent', () => {
    let component: CartcontrolComponent;
    let fixture: ComponentFixture<CartcontrolComponent>;
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();

    beforeEach(async(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";

        TestBed.configureTestingModule({
        declarations: [ CartcontrolComponent ],
        imports: [
            HttpClientTestingModule],
        providers: [
            CartService,
            DownloadService,
            TestDataService,
            { provide: AppConfig, useValue: cfg }
        ]
        })
        .compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(CartcontrolComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('getButtonColor()', () => {
        component.noFileDownloaded = true;
        expect(component.getButtonColor()).toEqual("#1E6BA1");

        component.noFileDownloaded = false;
        expect(component.getButtonColor()).toEqual("#307F38");
    });

    it('getDownloadedColor()', () => {
        component.noFileDownloaded = true;
        expect(component.getDownloadedColor()).toEqual("rgb(82, 82, 82)");

        component.noFileDownloaded = false;
        expect(component.getDownloadedColor()).toEqual("white");
    });

    it('getDownloadedBkColor()', () => {
        component.noFileDownloaded = true;
        expect(component.getDownloadedBkColor()).toEqual("white");

        component.noFileDownloaded = false;
        expect(component.getDownloadedBkColor()).toEqual("green");
    });
});
