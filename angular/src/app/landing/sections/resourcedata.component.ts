import { Component, OnChanges, SimpleChanges, Input } from '@angular/core';

import { AppConfig } from '../../config/config';
import { NerdmRes, NerdmComp, NERDResource } from '../../nerdm/nerdm';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';

/**
 * a component that lays out the "Data Access" section of a landing page.  This includes (as applicable)
 * the list of data files, links to data access pages, and access policies.  
 */
@Component({
    selector:      'pdr-resource-data',
    templateUrl:   './resourcedata.component.html',
    styleUrls:   [
        '../landing.component.css'
    ]
})
export class ResourceDataComponent implements OnChanges {
    accessPages: NerdmComp[] = [];

    // passed in by the parent component:
    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;
    @Input() editEnabled: boolean; 

    /**
     * create an instance of the Identity section
     */
    constructor(private cfg: AppConfig,
                private gaService: GoogleAnalyticsService)
    { }

    ngOnChanges(ch : SimpleChanges) {
        if (this.record)
            this.useMetadata();  // initialize internal component data based on metadata
    }

    /**
     * initial this component's internal data used to drive the display based on the 
     * input resource metadata
     */
    useMetadata(): void {
        this.accessPages = []
        if (this.record['components'])
            this.accessPages = this.selectAccessPages(this.record['components']);
    }

    /**
     * return an array of AccessPage components from the given input components array
     * @param comps     the list of NERDm components to select from.  This can be from the 
     *                  full list from the NERDm Resource record 
     */
    selectAccessPages(comps : NerdmComp[]) : NerdmComp[] {
        let use : NerdmComp[] = comps.filter(cmp => cmp['@type'].includes("nrdp:AccessPage") &&
                                       ! cmp['@type'].includes("nrd:Hidden"));
        use = (JSON.parse(JSON.stringify(use))) as NerdmComp[];
        return use.map((cmp) => {
            if (! cmp['title']) cmp['title'] = cmp['accessURL']
            return cmp;
        });
    }
}

