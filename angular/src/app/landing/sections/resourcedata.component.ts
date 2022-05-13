import { Component, OnChanges, SimpleChanges, Input, Output, EventEmitter } from '@angular/core';

import { AppConfig } from '../../config/config';
import { NerdmRes, NerdmComp, NERDResource } from '../../nerdm/nerdm';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { Themes, ThemesPrefs } from '../../shared/globals/globals';

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
        trigger(
          'enterAnimation', [
            transition(':enter', [
              style({height: '0px', opacity: 0}),
              animate('500ms', style({height: '100%', opacity: 1}))
            ]),
            transition(':leave', [
              style({height: '100%', opacity: 1}),
              animate('500ms', style({height: 0, opacity: 0}))
            //   animate('500ms', style({transform: 'translateY(0)', opacity: 1}))
            ])
          ]
        )
    ]
})
export class ResourceDataComponent implements OnChanges {
    accessPages: NerdmComp[] = [];
    dynamicResourcePages: NerdmComp[] = [];
    showDescription: boolean = false;
    showRestrictedDescription: boolean = false;
    currentState = 'initial';
    recordType: string = "";
    scienceTheme = Themes.SCIENCE_THEME;
    defaultTheme = Themes.DEFAULT_THEME;

    // passed in by the parent component:
    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;
    @Input() editEnabled: boolean; 
    @Input() theme: string;

    // pass out download status for metrics refresh
    @Output() dlStatus: EventEmitter<string> = new EventEmitter();

    /**
     * create an instance of the Identity section
     */
    constructor(private cfg: AppConfig,
                private gaService: GoogleAnalyticsService)
    { }

    ngOnInit(): void {
        this.recordType = (new NERDResource(this.record)).resourceLabel();
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
        this.accessPages = []
        if (this.record['components']){
            if(this.theme == this.defaultTheme)
                this.accessPages = this.selectAccessPages(this.record['components']);
            else
                this.dynamicResourcePages = this.selectDynamicPages(this.record['components']);
        }
    }

    /**
     * return an array of AccessPage components from the given input components array
     * @param comps     the list of NERDm components to select from.  This can be from the 
     *                  full list from the NERDm Resource record 
     */
    selectAccessPages(comps : NerdmComp[]) : NerdmComp[] {
        let use : NerdmComp[];
        use = comps.filter(cmp => cmp['@type'].includes("nrdp:AccessPage") &&
        ! cmp['@type'].includes("nrd:Hidden"));

        use = (JSON.parse(JSON.stringify(use))) as NerdmComp[];
        return use.map((cmp) => {
            if (! cmp['title']) cmp['title'] = cmp['accessURL'];

            cmp['showDesc'] = false;
            cmp['backcolor'] = 'white';

            return cmp;
        });
    }


    /**
     * return an array of Dynamic Resource components from the given input components array
     * @param comps the list of NERDm components to select from.  This can be from the 
     *                  full list from the NERDm Resource record 
     * @returns an array of Dynamic Resource components
     */
    selectDynamicPages(comps : NerdmComp[]) : NerdmComp[] {
        let use : NerdmComp[] = (new NERDResource(this.record)).selectDynamicResourceComps();
        return use.map((cmp) => {
            if (! cmp['title']) cmp['title'] = cmp['accessURL'];

            cmp['showDesc'] = false;
            cmp['backcolor'] = 'white';

            return cmp;
        });
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

