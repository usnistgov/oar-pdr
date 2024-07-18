import { Component, Input, ViewChild, ElementRef, Output, EventEmitter } from '@angular/core';

import { AppConfig } from '../config/config';
import { NerdmRes, NERDResource } from '../nerdm/nerdm';
import { ResourceMetadataComponent } from './sections/resourcemetadata.component';
import { Console } from 'console';
import { MetricsData } from "./metrics-data";

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
    recordType: string = "";

    // passed in by the parent component:
    @Input() md: NerdmRes = null;
    @Input() inBrowser: boolean = false;
    @Input() editEnabled: boolean;
    @Input() collection: string;

    // Pass out download status
    @Output() dlStatus: EventEmitter<string> = new EventEmitter();
    // Flag to tell if current screen size is mobile or small device
    @Input() mobileMode : boolean|null = false;

    @Input() metricsData: MetricsData;
    @Input() showJsonViewer: boolean = false;
    @Input() theme: string;

    @ViewChild(ResourceMetadataComponent)
    resourceMetadataComponent: ResourceMetadataComponent;

    @ViewChild('description') description: ElementRef;
    @ViewChild('dataAccess') dataAccess: ElementRef;
    @ViewChild('references') references: ElementRef;
    @ViewChild('about') about: ElementRef;

    /**
     * create an instance of the Identity section
     */
    constructor(private cfg: AppConfig)
    { }

    ngOnInit(): void {
        this.recordType = (new NERDResource(this.md)).resourceLabel();
    }
    /**
     * scroll the view to the named section.  The available sections are: "top", "description",
     * "dataAccess", "references", and "metadata".  Any other value will be treated as "top".  
     * (Note that the "references" section may be omitted if there are no references to be displayed.)
     */
    goToSection(sectionId) {
        if(sectionId == null) sectionId = "top";

        switch(sectionId) { 
            case "description": { 
                this.description.nativeElement.scrollIntoView({behavior: 'smooth'}); 
               break; 
            } 
            case "dataAccess": { 
                this.dataAccess.nativeElement.scrollIntoView({behavior: 'smooth'}); 
               break; 
            } 
            case "references": {
                this.references.nativeElement.scrollIntoView({behavior: 'smooth'}); 
                break;
            }
            case "about": {
                this.about.nativeElement.scrollIntoView({behavior: 'smooth'}); 
                break;
            }
            default: { // GO TOP
                window.scrollTo({
                    top: 0,
                    left: 0,
                    behavior: 'smooth'
                  });
                break; 
            } 
        } 
    }

    /**
     * Emit the download status
     * @param downloadStatus - download status ('downloading' or 'downloaded')
     */
     setDownloadStatus(downloadStatus){
        this.dlStatus.emit(downloadStatus);
    }
}
