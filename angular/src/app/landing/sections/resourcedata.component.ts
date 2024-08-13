import { Component, OnChanges, SimpleChanges, Input, Output, EventEmitter, ViewChild, ElementRef } from '@angular/core';

import { AppConfig } from '../../config/config';
import { NerdmRes, NerdmComp, NERDResource } from '../../nerdm/nerdm';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { Themes, ThemesPrefs, Collections, Collection, CollectionThemes, FilterTreeNode, ColorScheme } from '../../shared/globals/globals';
import { D3Service } from '../../shared/d3-service/d3.service';
import { CollectionService } from '../../shared/collection-service/collection.service';

/**
 * a component that lays out the "Data Access" section of a landing page.  This includes (as applicable)
 * the list of data files, links to data access pages, and access policies.  
 */
@Component({
    selector:      'pdr-resource-data',
    templateUrl:   './resourcedata.component.html',
    styleUrls:   [
        './resourcedata.component.css',
        '../landing.component.css'
    ],
    animations: [
        trigger('detailExpand', [
            state('void', style({height: '0px', minHeight: '0px'})),
            state('collapsed', style({height: '0px', minHeight: '0px'})),
            state('expanded', style({height: '*'})),
            transition('expanded <=> collapsed', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
            transition('expanded <=> void', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
            ])
    ]
})
export class ResourceDataComponent implements OnChanges {
    accessPages: NerdmComp[] = [];
    hasDRS: boolean = false;
    showDescription: boolean = false;
    showRestrictedDescription: boolean = false;
    currentState = 'initial';
    recordType: string = "";
    scienceTheme = Themes.SCIENCE_THEME;
    defaultTheme = Themes.DEFAULT_THEME;
    sectionWidth: number;
    backColor: string = '#003c97';
    sectionTitle: string = "Data Access";
    svg: any;
    colorScheme: ColorScheme;

    // passed in by the parent component:
    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;
    @Input() editEnabled: boolean; 
    @Input() theme: string;
    @Input() collection: string;

    @ViewChild('dataAccessHeader') dataAccessHeader: ElementRef;

    // pass out download status for metrics refresh
    @Output() dlStatus: EventEmitter<string> = new EventEmitter();

    /**
     * create an instance of the Identity section
     */
    constructor(private cfg: AppConfig,
                private gaService: GoogleAnalyticsService,
                public collectionService: CollectionService,
                public d3Service: D3Service)
    { }

    ngOnInit(): void {
        this.recordType = (new NERDResource(this.record)).resourceLabel();
        this.colorScheme = this.collectionService.getColorScheme(this.collection);
    }

    ngAfterViewInit(): void {
        //Called after ngAfterContentInit when the component's view has been initialized. Applies to components only.
        //Add 'implements AfterViewInit' to the class.
        this.sectionWidth = this.dataAccessHeader.nativeElement.offsetWidth;
        console.log("this.sectionWidth", this.sectionWidth);
        // this.drawSectionHeaderBackground();
        this.d3Service.drawSectionHeaderBackground(this.svg, this.sectionTitle, this.sectionWidth, this.colorScheme.default, 165, "#dataAccessHeader");    
    }

    /**
     * On screen resize, re-draw section header
     */
    onResize(){
        if (this.inBrowser) {
            this.sectionWidth = this.dataAccessHeader.nativeElement.offsetWidth;

            // this.drawSectionHeaderBackground();

            // this.d3Service.drawSectionHeaderBackground(this.svg, this.sectionTitle, this.sectionWidth, this.backColor, 165, "#dataAccessHeader");
        }
    }

    /**
     * This function returns alter text/tooltip text for the expand symbol next to the given treenode title
     * @param fileNode the TreeNode
     * @returns 
     */
    expandButtonAlterText(accessPage: any) {
        if(accessPage['showDesc'])
            return "Close access page description";
        else
            return "Open access page description";
    }

    ngOnChanges(ch : SimpleChanges) {
        if (this.record)
            this.useMetadata();  // initialize internal component data based on metadata
    }

    /**
     * initial this component's internal data used to drive the display based on the 
     * input resource metadata
     */
    useMetadata(): void {
        this.accessPages = [];
        if (this.record['components']) {
            this.accessPages = this.selectAccessPages();

            // If this is a science theme and the collection contains one or more components that contain both AccessPage (or SearchPage) and DynamicSourceSet, we want to remove it from accessPages array since it's already displayed in the search result.
            if(this.theme == this.scienceTheme) 
                this.accessPages = this.accessPages.filter(cmp => ! cmp['@type'].includes("nrda:DynamicResourceSet"));

            this.hasDRS = this.hasDynamicResourceSets();
        }
    }

    /**
     * select the AccessPage components to display, adding special disply options
     */
    selectAccessPages() : NerdmComp[] {
        let use: NerdmComp[] = (new NERDResource(this.record)).selectAccessPages();
        use = (JSON.parse(JSON.stringify(use))) as NerdmComp[];

        return use.map((cmp) => {
            if (! cmp['title']) cmp['title'] = cmp['accessURL'];

            cmp['showDesc'] = false;
            cmp['backcolor'] = 'white';

            return cmp;
        });
    }

    /**
     * return true if the components include non-hidden DynamicResourceSets.  If there are, the 
     * results from the DynamicResourceSet searches will be display in a special in-page 
     * search results display.
     */
    hasDynamicResourceSets(): boolean {
        return (new NERDResource(this.record)).selectDynamicResourceComps().length > 0;
    }

    /**
     * Emit download status
     * @param downloadStatus
     */
    setDownloadStatus(downloadStatus){
        this.dlStatus.emit(downloadStatus);
    }
    /**
     * For animation
     * initial - mouse out
     * final - mouse in
     */
    changeState() {
        this.currentState = this.currentState === 'initial' ? 'final' : 'initial';
    }

    /**
     * Google Analytics track event
     * @param url - URL that user visit
     * @param event - action event
     * @param title - action title
     */
     googleAnalytics(url: string, event, title) {
        this.gaService.gaTrackEvent('homepage', event, title, url);
    }
}

