import { ComponentFixture, TestBed, waitForAsync as  } from '@angular/core/testing';
import { AppConfig } from '../../config/config';
import { CartcontrolComponent } from './cartcontrol.component';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { DataCart } from '../../datacart/cart';
import { CartService } from '../../datacart/cart.service';
import { TestDataService } from '../../shared/testdata-service/testDataService';

describe('CartcontrolComponent', () => {
    let component: CartcontrolComponent;
    let fixture: ComponentFixture<CartcontrolComponent>;
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();

    beforeEach(waitForAsync(() => {
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
        let dc: DataCart = new DataCart("goob");
        dc._forget();
        fixture = TestBed.createComponent(CartcontrolComponent);
        component = fixture.componentInstance;
        component.cartName = "goob";
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
        expect(component.cartName).toBe("goob");
        expect(component.datacart).toBeTruthy();
    });

    it('anyDownloaded()', () => {
        component.totalDownloaded = 0;
        expect(component.anyDownloaded()).toBeFalsy();
        component.totalDownloaded = 1;
        expect(component.anyDownloaded()).toBeTruthy();
    });

    it('getButtonColor()', () => {
        component.totalDownloaded = 0;
        expect(component.getButtonColor()).toEqual("#1E6BA1");

        component.totalDownloaded = 1;
        expect(component.getButtonColor()).toEqual("#307F38");
    });

    it('getDownloadedColor()', () => {
        component.totalDownloaded = 0;
        expect(component.getDownloadedColor()).toEqual("rgb(82, 82, 82)");

        component.totalDownloaded = 1;
        expect(component.getDownloadedColor()).toEqual("white");
    });

    it('getDownloadedBkColor()', () => {
        component.totalDownloaded = 0;
        expect(component.getDownloadedBkColor()).toEqual("white");

        component.totalDownloaded = 1;
        expect(component.getDownloadedBkColor()).toEqual("green");
    });

    it('cart update', waitForAsync(() => {
        expect(component.totalDownloaded).toBe(0);
        expect(component.selectedFileCount).toBe(0);
        component.datacart.addFile("gov", { filePath: "hank", count: 8, downloadStatus: "downloaded",
                                            downloadURL: "http://here" }, true);
        expect(component.totalDownloaded).toBe(1);
        expect(component.selectedFileCount).toBe(1);
    }));
        
});
