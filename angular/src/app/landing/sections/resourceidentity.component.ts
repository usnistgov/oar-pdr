import { Component, OnChanges, Input, ViewChild } from '@angular/core';

import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { VersionComponent } from '../version/version.component';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';

/**
 * a component that lays out the "identity" section of a landing page
 */
@Component({
    selector:      'pdr-resource-id',
    templateUrl:   './resourceidentity.component.html',
    styleUrls:   [
        './resourceidentity.component.css', '../landing.component.css'
    ]
})
export class ResourceIdentityComponent implements OnChanges {

    recordType: string = "";
    doiUrl: string = null;
    showHomePageLink: boolean = true;
    primaryRefs: any[] = [];

    // passed in by the parent component:
    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;
    @Input() editMode: boolean = false;

    /**
     * create an instance of the Identity section
     */
    constructor(private cfg: AppConfig,
                private gaService: GoogleAnalyticsService)
    { }

    ngOnChanges() {
        if (this.recordLoaded())
            this.useMetadata();  // initialize internal component data based on metadata
    }

    recordLoaded() {
        return this.record && ! (Object.keys(this.record).length === 0);
    }

    /**
     * initial this component's internal data used to drive the display based on the 
     * input resource metadata
     */
    useMetadata(): void {
        this.showHomePageLink = this.isExternalHomePage(this.record['landingPage']);
        this.recordType = this.determineResourceLabel(this.record);

        if (this.record['doi'] !== undefined && this.record['doi'] !== "")
            this.doiUrl = "https://doi.org/" + this.record['doi'].substring(4);
        this.primaryRefs = (new NERDResource(this.record)).getPrimaryReferences();
    }    

    /**
     * return true if the given URL does not appear to be a PDR-generated home page URL.
     * Note that if the input URL is not a string, false is returned.  
     */
    public isExternalHomePage(url : string) : boolean {
        if (! url)
            return false;
        let pdrhomeurl = /^https?:\/\/(\w+)(\.\w+)*\/od\/id\//
        return ((url.match(pdrhomeurl)) ? false : true);
    }

    /**
     * analyze the NERDm resource metadata and return a label indicating the type of 
     * the resource described.  This is used as a label at the top of the page, just above 
     * the title.
     */
    public determineResourceLabel(resmd: NerdmRes): string {
        if (this.record instanceof Array && this.record.length > 0) {
            switch (this.record['@type'][0]) {
                case 'nrd:SRD':
                    return "Standard Reference Data";
                case 'nrdp:DataPublication':
                    return "Data Publication";
                case 'nrdp:PublicDataResource':
                    return "Public Data Resource";
            }
        }

        return "Data Resource";
    }

    @ViewChild(VersionComponent)
    versionCmp : VersionComponent;

}
