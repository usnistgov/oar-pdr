import { Component, OnChanges, SimpleChanges, Input, ViewChild, ElementRef } from '@angular/core';
import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { AboutdatasetComponent } from '../aboutdataset/aboutdataset.component';
import { MetricsData } from "../metrics-data";
import { D3Service } from '../../shared/d3-service/d3.service';
import { Themes, ThemesPrefs, Collections, Collection, CollectionThemes, FilterTreeNode, ColorScheme } from '../../shared/globals/globals';
import { CollectionService } from '../../shared/collection-service/collection.service';

/**
 * a component that lays out the "About This Dataset" section of a landing page
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
    aboutTitle : string = "About This ";
    resourceType: string;
    svg: any;
    sectionWidth: number;
    backColor: string = '#003c97';
    colorScheme: ColorScheme;

    // passed in by the parent component:
    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;

    // Flag to tell if current screen size is mobile or small device
    @Input() mobileMode : boolean|null = false;

    @Input() metricsData: MetricsData;
    @Input() showJsonViewer: boolean = false;
    @Input() theme: string;
    @Input() collection: string;

    @ViewChild(AboutdatasetComponent, { static: true })
    aboutdatasetComponent: AboutdatasetComponent;

    @ViewChild('aboutHeader') aboutHeader: ElementRef;
    
    /**
     * create an instance of the Identity section
     */
    constructor(
        private cfg: AppConfig, 
        public d3Service: D3Service,
        public collectionService: CollectionService)
    { }

    ngOnInit(): void {
        this.colorScheme = this.collectionService.getColorScheme(this.collection);

        if (this.record)
            this.useMetadata();  
    }

    ngAfterViewInit(): void {
        this.sectionWidth = this.aboutHeader.nativeElement.offsetWidth;
        
        if(this.colorScheme)
            this.d3Service.drawSectionHeaderBackground(this.svg, this.aboutTitle, this.sectionWidth, this.colorScheme.default, 245, "#aboutHeader");    
    }

    /**
     * On screen resize, re-draw section header
     */
    onResize(){
        if (this.inBrowser) {
            this.sectionWidth = this.aboutHeader.nativeElement.offsetWidth;
        }
    }

    ngOnChanges(ch: SimpleChanges) {
        // this.aboutdatasetComponent.collapsed = !this.showNerdm;
        if (this.record)
            this.useMetadata();  // initialize internal component data based on metadata
    }

    /**
     * initial this component's internal data used to drive the display based on the 
     * input resource metadata
     */
    useMetadata(): void {
        this.resourceType = ThemesPrefs.getResourceLabel(this.theme);
        this.aboutTitle = "About This " + this.resourceType;
    }
}
