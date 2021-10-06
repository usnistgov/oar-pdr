import { Component, PLATFORM_ID, Inject } from '@angular/core';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';
import * as footerlinks from '../../assets/site-constants/footer-links.json';

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
    footerLinks: any;

    // Social media list
    socialMediaList : any[];

    // Footer link line #1
    footerLinks01: any[];

    // Footer link line #2
    footerLinks02: any[];

    constructor(
        public gaService: GoogleAnalyticsService){

        // For some reason, footerlinks does not have "default" field in unit test
        // So we have to use following condition to make both production and unit test work. 
        if((footerlinks as any).default)
            this.footerLinks = (footerlinks as any).default;
        else
            this.footerLinks = footerlinks as any;

        // Add footerLinks to the condition to avoid unit test error
        this.socialMediaList = this.footerLinks.socialMediaList;
        this.footerLinks01 = this.footerLinks.footerLinks01;
        this.footerLinks02 = this.footerLinks.footerLinks02;

    }

    /**
     * The classes for the first and last items are different from the items in the link array. 
     * This function return different class name based on the index of an item. 
     * @param index - index number of the given array
     * @param linkArray - the link array. The array's length is used to decide the position of the given index.
     * @returns class name
     */
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
