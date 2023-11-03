import { Component, AfterViewInit, OnInit, PLATFORM_ID, Inject } from '@angular/core';
import { Router, NavigationStart, NavigationEnd, NavigationCancel, NavigationError } from '@angular/router';
import './content/modal.less';
import { GoogleAnalyticsService } from './shared/ga-service/google-analytics.service'
import { AppConfig } from './config/config';
import { isPlatformBrowser } from '@angular/common';

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.css']
})
export class AppComponent {
    title = 'PDR Resource Landing Page';
    gaCode: string;
    ga4Code: string = null;
    inBrowser: boolean = false;

    constructor(private gaService: GoogleAnalyticsService,
                private cfg: AppConfig,
                @Inject(PLATFORM_ID) private platformId: Object)
    { 
        this.inBrowser = isPlatformBrowser(platformId);
    }

    ngOnInit() {
    }

    ngAfterViewInit(): void {
        // Called after ngAfterContentInit when the component's view has been initialized.
        // Applies to components only.
        if(this.inBrowser){
            this.gaCode = this.cfg.get("gaCode", "") as string;
            this.ga4Code = this.cfg.get("ga4Code", "") as string;

            this.gaService.appendGaTrackingCode(this.gaCode, this.ga4Code);
        }
    }
}

