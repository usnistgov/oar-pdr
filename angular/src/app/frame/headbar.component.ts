import { Component, ElementRef } from '@angular/core';
import { AppConfig } from '../config/config';

/**
 * A Component that serves as the header of the landing page.  
 * 
 * Features include:
 * * Set as black bar at the top of the page
 * * NIST PDR logo that links to the PDR home page (currently the SDP)
 * * PDR-wide links:
 *   * About page
 *   * Search page (the SDP)
 *   * User's Datacart
 * * Labels indicating the version and status of the PDR
 *   * this uses the badge style from bootstrap
 */
@Component({
    moduleId: module.id,
    selector: 'pdr-headbar',
    templateUrl: 'headbar.component.html',
    styleUrls: ['headbar.component.css']
})
export class HeadbarComponent {

    layoutCompact : boolean = true;
    layoutMode : string = 'horizontal';
    searchLink : string = "";
    status : string = "";
    appVersion : string = "";

    constructor(private el: ElementRef, private cfg : AppConfig) {
        if (! (cfg instanceof AppConfig))
            throw new Error("HeadbarComponent: Wrong config type provided: "+cfg);
        this.searchLink = cfg.get("locations.pdrSearch", "/sdp/");
        this.status = cfg.get("status", "");
        this.appVersion = cfg.get("appVersion","");
    }
  
}
