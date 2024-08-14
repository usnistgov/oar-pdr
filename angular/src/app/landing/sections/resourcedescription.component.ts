import { Component, OnChanges, Input, ViewChild, ElementRef } from '@angular/core';
import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { D3Service } from '../../shared/d3-service/d3.service';
import { Themes, ThemesPrefs, Collections, Collection, CollectionThemes, FilterTreeNode, ColorScheme } from '../../shared/globals/globals';
import { CollectionService } from '../../shared/collection-service/collection.service';

/**
 * a component that lays out the "Description" section of a landing page which includes the prose 
 * description, subject keywords, and research topics.
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
    recordType: string = "";
    sectionWidth: number;
    backColor: string = '#003c97';
    svg: any;
    colorScheme: ColorScheme;

    // passed in by the parent component:
    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;
    @Input() collection: string;

    @ViewChild('sectionHeader') sectionHeader: ElementRef;
    
    /**
     * create an instance of the Identity section
     */
    constructor(
        private cfg: AppConfig, 
        public d3Service: D3Service,
        public collectionService: CollectionService)
    { }

    ngOnInit(): void {
        this.recordType = (new NERDResource(this.record)).resourceLabel();
        this.colorScheme = this.collectionService.getColorScheme(this.collection);
    }

    ngAfterViewInit(): void {
        this.sectionWidth = this.sectionHeader.nativeElement.offsetWidth;

        if(this.colorScheme)
            this.d3Service.drawSectionHeaderBackground(this.svg, this.desctitle, this.sectionWidth, this.colorScheme.default, 155, "#sectionHeader");    
    }

    /**
     * On screen resize, re-draw section header
     */
    onResize(){
        if (this.inBrowser) {
            this.sectionWidth = this.sectionHeader.nativeElement.offsetWidth;

            // this.drawSectionHeaderBackground();
            // this.d3Service.drawSectionHeaderBackground(this.svg, this.desctitle, this.sectionWidth, this.backColor, 155, "#sectionHeader");
        }
    }

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


    
