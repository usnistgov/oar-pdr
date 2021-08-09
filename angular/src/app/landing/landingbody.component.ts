import { Component, Input, ViewChild, ElementRef } from '@angular/core';

import { AppConfig } from '../config/config';
import { NerdmRes, NERDResource } from '../nerdm/nerdm';
import { ResourceMetadataComponent } from './sections/resourcemetadata.component';
import { Console } from 'console';

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
    private _showMetadata: boolean = false;
    private _sectionId: string = "";

    // passed in by the parent component:
    @Input() md: NerdmRes = null;
    @Input() inBrowser: boolean = false;
    @Input() editEnabled: boolean;
    // @Input() showMetadata: boolean = false;

    @ViewChild(ResourceMetadataComponent)
    resourceMetadataComponent: ResourceMetadataComponent;

    @ViewChild('top') top: ElementRef;
    @ViewChild('description') description: ElementRef;
    @ViewChild('dataAccess') dataAccess: ElementRef;
    @ViewChild('reference') reference: ElementRef;
    @ViewChild('metadata') metadata: ElementRef;
    
    // Show/hide metadata
    get showMetadata() { return this._showMetadata; }
    set showMetadata(newValue) {
        this.resourceMetadataComponent.showMetadata = newValue;
        // logic
        this._showMetadata = newValue;
    }

    // Go to section
    get sectionId() { return this._sectionId; }
    set sectionId(newValue) {
        if(newValue == null) newValue = "top";

        switch(newValue) { 
            case "description": { 
                this.description.nativeElement.scrollIntoView({behavior: 'smooth'}); 
               break; 
            } 
            case "dataAccess": { 
                this.dataAccess.nativeElement.scrollIntoView({behavior: 'smooth'}); 
               break; 
            } 
            case "reference": {
                this.reference.nativeElement.scrollIntoView({behavior: 'smooth'}); 
                break;
            }
            case "metadata": {
                this.metadata.nativeElement.scrollIntoView({behavior: 'smooth'}); 
                break;
            }
            default: { // GO TOP
                window.scrollTo({
                    top: 0,
                    left: 0,
                    behavior: 'smooth'
                  });
                // window.scrollTo(0, 0);
                // this.top.nativeElement.scrollIntoView({behavior: 'smooth'}); 
               break; 
            } 
        } 

        this._sectionId = newValue;
    }

    /**
     * create an instance of the Identity section
     */
    constructor(private cfg: AppConfig)
    { }
}
