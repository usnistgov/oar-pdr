import { Component, Input } from '@angular/core';

import { AppConfig } from '../config/config';
import { NerdmRes, NERDResource } from '../nerdm/nerdm';

/**
 * a component that presents the landing page's presentation of the resource description
 *
 * The description is organized into the following sections:
 *  * front matter, providing information that identifies the resource, namely its:
 *     - title
 *     - authors
 *     - contact 
 *     - identifier
 *     - the paper this resource is a supplement to, if applicable
 *     - a link to official landing page (if different from this one)
 *  * Description, including
 *     - the abstract/description text
 *     - the subject keywords
 *     - the applicable research topics
 *  * Data Access, including, as applicable,
 *     - list of the downloadable files
 *     - links to data access pages
 *     - statements of access policies and rights
 *  * References
 *  * Metadata 
 */
@Component({
    selector:    'pdr-landing-body',
    templateUrl: './landingbody.component.html',
    styleUrls:   [
        './landing.component.css'
    ]
})
export class LandingBodyComponent {

    // passed in by the parent component:
    @Input() md: NerdmRes = null;
    @Input() inBrowser: boolean = false;
    @Input() editEnabled: boolean;
    @Input() showMetadata: boolean = false;

    /**
     * create an instance of the Identity section
     */
    constructor(private cfg: AppConfig)
    { }
}
