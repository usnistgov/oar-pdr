import { Component, PLATFORM_ID, Inject } from '@angular/core';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';
import * as footerlinks from '../../assets/site-constants/footer-links.json';
import { isPlatformBrowser } from '@angular/common';

/**
 * A Component that serves as the footer of the landing page.  
 * 
 * Features include:
 * * Set as black bar at the bottom of the page
 */
@Component({
  moduleId: module.id,
  selector: 'pdr-footbar',
  templateUrl: 'footbar.component.html',
  styleUrls: ['footbar.component.css']
})
export class FootbarComponent { 
    inBrowser: boolean = false;
    footerLinks: any = (footerlinks as any).default;

    // Social media list
    socialMediaList : any[];

    // Footer link line #1
    footerLinks01: any[];

    // Footer link line #2
    footerLinks02: any[];

    constructor(
        public gaService: GoogleAnalyticsService,
        @Inject(PLATFORM_ID) private platformId: Object){
        this.inBrowser = isPlatformBrowser(platformId);
    }

    ngOnInit(): void {
        if(this.inBrowser) {
            this.socialMediaList =  this.footerLinks.socialMediaList;
            this.footerLinks01 = this.footerLinks.footerLinks01;
            this.footerLinks02 = this.footerLinks.footerLinks02;
        }
    }
    getLinkClass(index: number, linkArray: any[]) {
        let className = "menu__item is-leaf leaf menu-depth-1";

        if( index == 0){
            className = "menu__item is-leaf first leaf menu-depth-1";
        } else if(index == linkArray.length-1) {
            className = "menu__item is-leaf last leaf menu-depth-1";
        }

        return className;
    }

}
