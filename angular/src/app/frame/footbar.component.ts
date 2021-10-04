import { Component } from '@angular/core';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';

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
    // Social media list
    socialMediaList: any[] = [
        {   
            name: 'twitter', 
            url: 'https://twitter.com/nist',
            icon: 'faa faa-twitter' 
        },
        { 
            name: 'facebook', 
            url: 'https://www.facebook.com/NIST/',
            icon: 'faa faa-facebook' 
        },
        { 
            name: 'linkedin', 
            url: 'https://www.linkedin.com/company/nist',
            icon: 'faa faa-linkedin' 
        },
        { 
            name: 'Instagram', 
            url: 'https://www.instagram.com/nist/',
            icon: 'faa faa-instagram' 
        },
        { 
            name: 'youtube', 
            url: 'https://www.youtube.com/nist',
            icon: 'faa faa-youtube' 
        },
        { 
            name: 'rss', 
            url: 'https://www.nist.gov/news-events/nist-rss-feeds',
            icon: 'faa faa-rss' 
        },
        { 
            name: 'govdelivery', 
            url: 'https://service.govdelivery.com/accounts/USNIST/subscriber/new',
            icon: 'faa faa-envelope' 
        }
    ]

    // Footer link line #1
    footerLinks01: any[] = [
        {
            title: "Site Privacy",
            url: "https://www.nist.gov/privacy-policy"
        },
        {
            title: "Accessibility",
            url: "https://www.nist.gov/oism/accessibility"
        },
        {
            title: "Privacy Program",
            url: "https://www.nist.gov/privacy"
        },
        {
            title: "Copyrights",
            url: "https://www.nist.gov/oism/copyrights"
        },
        {
            title: "Vulnerability Disclosure",
            url: "https://www.commerce.gov/vulnerability-disclosure-policy"
        },
        {
            title: "No Fear Act Policy",
            url: "https://www.nist.gov/no-fear-act-policy"
        },
        {
            title: "FOIA",
            url: "https://www.nist.gov/foia"
        },
        {
            title: "Environmental Policy",
            url: "https://www.nist.gov/environmental-policy-statement"
        },
        {
            title: "Scientific Integrity",
            url: "https://www.nist.gov/summary-report-scientific-integrity"
        },
        {
            title: "Information Quality Standards",
            url: "https://www.nist.gov/nist-information-quality-standards"
        }
    ]

    // Footer link line #2
    footerLinks02: any[] = [
        {
            title: "Commerce.gov",
            url: "https://www.commerce.gov/"
        },
        {
            title: "Science.gov",
            url: "http://www.science.gov/"
        },
        {
            title: "USA.gov",
            url: "http://www.usa.gov/"
        }
    ]

    constructor(public gaService: GoogleAnalyticsService){}

    getLinkClass(index: number, linkArray: any[]) {
        console.log("index", index);
        let className = "menu__item is-leaf leaf menu-depth-1";

        if( index == 0){
            className = "menu__item is-leaf first leaf menu-depth-1";
        } else if(index == linkArray.length-1) {
            className = "menu__item is-leaf last leaf menu-depth-1";
        }

        console.log("className", className);
        return className;
    }

}
