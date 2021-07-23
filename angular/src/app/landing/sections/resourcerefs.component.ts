import { Component, OnChanges, SimpleChanges, Input } from '@angular/core';

import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';

/**
 * a component that lays out the "references" section of a landing page.
 * 
 */
@Component({
    selector:      'pdr-resource-refs',
    templateUrl:   './resourcerefs.component.html',
    styleUrls:   [
        '../landing.component.css'
    ]
})
export class ResourceRefsComponent implements OnChanges {

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

    }

    /**
     * Function to Check whether given record has references that need to be displayed
     */
    hasDisplayableReferences() {
        if (this.record['references'] && this.record['references'].length > 0) 
            return true;
        return false;
    }

    /**
     * Return the link text of the given reference.  The text returned will be one of
     * the following, in order or preference:
     * 1. the value of the citation property (if set and is not empty)
     * 2. the value of the label property (if set and is not empty)
     * 3. to "URL: " appended by the value of the location property.
     * @param ref   the NERDm reference object
     */
    getReferenceText(ref){
        if(ref['citation']) 
            return ref['citation'];
        if(ref['label'])
            return ref['label'];
        return ref['location'];
    }
}


    
