import { Component, OnChanges, SimpleChanges, Input, ViewChild, ElementRef } from '@angular/core';
import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { Themes, ThemesPrefs, Collections, Collection, CollectionThemes, FilterTreeNode, ColorScheme } from '../../shared/globals/globals';
import { CollectionService } from '../../shared/collection-service/collection.service';
import { D3Service } from '../../shared/d3-service/d3.service';

/**
 * a component that lays out the "references" section of a landing page.
 * 
 */
@Component({
    selector:      'pdr-resource-refs',
    templateUrl:   './resourcerefs.component.html',
    styleUrls:   [
        '../landing.component.css',
        './resourcerefs.component.css'
    ]
})
export class ResourceRefsComponent implements OnChanges {
    refTitle : string = "References";
    colorScheme: ColorScheme;
    sectionWidth: number;
    svg: any;

    // passed in by the parent component:
    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;
    @Input() collection: string;

    @ViewChild('refHeader') refHeader: ElementRef;
    
    /**
     * create an instance of the Identity section
     */
    constructor(
        private cfg: AppConfig,
        public collectionService: CollectionService,
        public d3Service: D3Service)
    { }

    ngOnInit(): void {
        this.colorScheme = this.collectionService.getColorScheme(this.collection);
        
    }

    ngAfterViewInit(): void {
        if(this.refHeader) {
            this.sectionWidth = this.refHeader.nativeElement.offsetWidth;
            console.log("this.sectionWidth", this.sectionWidth);
            // this.drawSectionHeaderBackground();
            this.d3Service.drawSectionHeaderBackground(this.svg, this.refTitle, this.sectionWidth, this.colorScheme.default, 155, "#refHeader");  
        }
  
    }

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


    
