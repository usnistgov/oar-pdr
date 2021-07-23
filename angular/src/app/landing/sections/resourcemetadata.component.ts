import { Component, OnChanges, SimpleChanges, Input } from '@angular/core';

import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';

/**
 * a component that lays out the "metadata" section of a landing page
 *
 * Currently, this section only provides access to the native NERDm metadata; in the future,
 * this section will provide access to other formats as well.
 */
@Component({
    selector:    'pdr-resource-md',
    templateUrl: './resourcemetadata.component.html',
    styleUrls:  [
        '../landing.component.css'
    ]
})
export class ResourceMetadataComponent implements OnChanges {

    // passed in by the parent component:
    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;

    /**
     * create an instance of the Identity section
     */
    constructor(private cfg: AppConfig)
    { }

    ngOnChanges(ch: SimpleChanges) {
        if (this.record)
            this.useMetadata();  // initialize internal component data based on metadata
    }

    /**
     * initial this component's internal data used to drive the display based on the 
     * input resource metadata
     */
    useMetadata(): void {
        // nothing currently necessary
    }
}
