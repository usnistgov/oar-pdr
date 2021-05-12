import { TestBed, async } from '@angular/core/testing';
import { AppComponent } from './app.component';
import { RouterModule, Routes } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { SharedModule } from './shared/shared.module';
import { FrameModule } from './frame/frame.module';
import { GoogleAnalyticsService } from "./shared/ga-service/google-analytics.service";
import { ConfigModule } from './config/config.module';
import { BrowserModule, BrowserTransferStateModule } from '@angular/platform-browser';
import { TransferState, StateKey } from '@angular/platform-browser';
import { AppConfig } from './config/config';
import { AngularEnvironmentConfigService } from './config/config.service';
import { CartService } from './datacart/cart.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ToastrModule } from 'ngx-toastr';

describe('AppComponent', () => {
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();

    beforeEach(async(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;

        TestBed.configureTestingModule({

            declarations: [
                AppComponent
            ], providers: [GoogleAnalyticsService, CartService, { provide: AppConfig, useValue: cfg }]
            , imports: [RouterTestingModule, FrameModule, ConfigModule, BrowserTransferStateModule, BrowserModule, HttpClientTestingModule, ToastrModule.forRoot()],
        }).compileComponents();
    }));
    it('should create the app', async(() => {
        const fixture = TestBed.createComponent(AppComponent);
        const app = fixture.debugElement.componentInstance;
        expect(app).toBeTruthy();
    }));
    it(`should have as title 'PDR Resource Landing Page'`, async(() => {
      const fixture = TestBed.createComponent(AppComponent);
      const app = fixture.debugElement.componentInstance;
      expect(app.title).toEqual('PDR Resource Landing Page');
    }));
    it(`should contain 'DATA REPOSITORY' in the first span`, async(() => {
      const fixture = TestBed.createComponent(AppComponent);
      fixture.detectChanges();
      const compiled = fixture.debugElement.nativeElement;
      expect(compiled.querySelector('span').textContent).toContain('DATA REPOSITORY');
    }));
});
