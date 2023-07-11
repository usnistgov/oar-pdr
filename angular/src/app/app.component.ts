import { Component, AfterViewInit, OnInit, PLATFORM_ID, Inject } from '@angular/core';
import { Router, NavigationStart, NavigationEnd, NavigationCancel, NavigationError, RouterState, ActivatedRoute } from '@angular/router';
import './content/modal.less';
import { GoogleAnalyticsService } from './shared/ga-service/google-analytics.service'
import { AppConfig } from './config/config';
import { isPlatformBrowser } from '@angular/common';
import { Title } from '@angular/platform-browser';
import { DOCUMENT } from '@angular/common';

declare const gtag: Function;

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
                @Inject(PLATFORM_ID) private platformId: Object,
                public router: Router,
                private titleService: Title,
                @Inject(DOCUMENT) private document: Document)
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

            //Add GA4 code to track page view
            this.handleRouteEvents();

        }
    }

    /**
     * GA4 code to track page view when user navigates to different pages
     */
    handleRouteEvents() {
        this.router.events.subscribe(event => {
            if (event instanceof NavigationEnd) {
                console.log('event', event);
                const title = this.getTitle(this.router.routerState, this.router.routerState.root).join('-');
                console.log('title', title);
                this.titleService.setTitle(title);
                gtag('event', 'page_view', {
                    page_title: title,
                    page_path: event.urlAfterRedirects,
                    page_location: this.document.location.href
                })
            }
        });
    }
    
    /**
     * Get page title if any
     * @param state router state
     * @param parent Activated route
     * @returns 
     */
    getTitle(state: RouterState, parent: ActivatedRoute): string[] {
        const data = [];
        if (parent && parent.snapshot.data && parent.snapshot.data['title']) {
            data.push(parent.snapshot.data['title']);
        }
        if (state && parent && parent.firstChild) {
            data.push(...this.getTitle(state, parent.firstChild));
        }
        return data;
    }

}

