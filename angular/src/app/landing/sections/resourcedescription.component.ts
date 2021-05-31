import { Component, OnChanges, Input, ViewChild } from '@angular/core';

import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';

/**
 * a component that lays out the "identity" section of a landing page
 */
@Component({
    selector:      'pdr-resource-desc',
    templateUrl:   './resourcedescription.component.html',
    styleUrls:   [
        '../landing.component.css'
    ]
})
export class ResourceDescriptionComponent implements OnChanges {
    desctitle : string = "Description";

    // passed in by the parent component:
    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;

    /**
     * create an instance of the Identity section
     */
    constructor(private cfg: AppConfig)
    { }

    ngOnChanges() {
        if (this.record)
            this.useMetadata();  // initialize internal component data based on metadata
    }

    /**
     * initial this component's internal data used to drive the display based on the 
     * input resource metadata
     */
    useMetadata(): void {
        this.desctitle = (this.isDataPublication()) ? "Abstract" : "Description";
    }

    /**
     * return true if the resource is considered a data publication--i.e. it includes the type
     * "DataPublication"
     */
    isDataPublication() : boolean {
        return NERDResource.objectMatchesTypes(this.record, "DataPublication");
    }
}


    