import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { VersionComponent } from '../version/version.component';
import { MetricsData } from "../metrics-data";
import { trigger, state, style, animate, transition } from '@angular/animations';
import { formatBytes } from '../../utils';
import { Themes, ThemesPrefs } from '../../shared/globals/globals';

@Component({
    selector: 'aboutdataset-detail',
    templateUrl: './aboutdataset.component.html',
    styleUrls: ['./aboutdataset.component.scss'],
    animations: [
        trigger(
          'enterAnimation', [
            transition(':enter', [
              style({height: '0px', opacity: 0}),
              animate('700ms', style({height: '100%', opacity: 1}))
            ]),
            transition(':leave', [
              style({height: '100%', opacity: 1}),
              animate('700ms', style({height: 0, opacity: 0}))
            //   animate('500ms', style({transform: 'translateY(0)', opacity: 1}))
            ])
          ]
        )
    ]
})
export class AboutdatasetComponent implements OnChanges {
    nerdmRecord: any = {};
    showJson: boolean = true;
    isOpen: boolean = false;
    // JSON viewer expand depth. Default is all.
    _jsonExpandDepth = "1";
    citetext: string;
    citeCopied: boolean = false;
    nerdmDocUrl: string;
    resourceType: string;
    scienceTheme = Themes.SCIENCE_THEME;
    defaultTheme = Themes.DEFAULT_THEME;
    scienceThemeResourceType = ThemesPrefs.getResourceLabel(Themes.SCIENCE_THEME);
    isPartOf: string[][] = null;
    
    private _collapsed: boolean = false;
    @Input() record: NerdmRes;
    @Input() inBrowser: boolean;
    @Input() theme: string;

    // Flag to tell if current screen size is mobile or small device
    @Input() mobileMode : boolean|null = false;

    @Input() metricsData: MetricsData;
    @Input() showJsonViewer: boolean = false;

    /**
     * Setter and getter of JSON viewer collapse flag
     */
    public get collapsed() { return this._collapsed; }
    public set collapsed(newValue) {
        // logic
        this._collapsed = true;
        setTimeout(() => {
            this._collapsed = newValue;
        }, 0);
        
        this.showJson = false;
        setTimeout(() => {
            this.showJson = true;
        }, 0);
    }

    /**
     * Setter and getter of JSON viewer expand depth
     */
    public get jsonExpandDepth() { return this._jsonExpandDepth; }
    public set jsonExpandDepth(newValue) {this._jsonExpandDepth = newValue}

    constructor(private cfg: AppConfig, 
                public gaService: GoogleAnalyticsService) {  }

    ngOnInit(): void {
        this.nerdmRecord["Native JSON (NERDm)"] = this.record;
        this.nerdmDocUrl = this.cfg.get("locations.nerdmAbout", "/od/dm/nerdm");
        this.citetext = (new NERDResource(this.record)).getCitation();
        this.resourceType = ThemesPrefs.getResourceLabel(this.theme);

        // set the isPartOf rendering, listing all of the collections this dataset is formally
        // a part of (as indicated by the NERDm isPartOf property.
        let article: string, title: string, suffix: string; 
        if (this.record["isPartOf"] && Array.isArray(this.record['isPartOf']) &&
            this.record['isPartOf'].length > 0)
        {
            this.isPartOf = [];
            for (var coll of this.record["isPartOf"]) {
                if (! coll['@id'])
                    continue
                article = "";
                title = "another collection";
                suffix = "";
                if (coll['title']) {
                    title = coll['title'];
                    if (NERDResource.objectMatchesTypes(coll, "ScienceTheme")) {
                        article = "the";
                        suffix = " Collection";
                    }
                }
                this.isPartOf.push([
                    article,
                    this.cfg.get("locations.landingPageService") + coll['@id'],
                    title,
                    suffix
                ]);
            }
            if (this.isPartOf.length == 1 && ! this.isPartOf[0][3]) {
                this.isPartOf[0][0] = "the";
                this.isPartOf[0][3] = " collection";
            }
        }
    }

    ngOnChanges(changes: SimpleChanges) {
        if (this.record && this.record["_id"]) 
            delete this.record["_id"];
    }

    /**
     * Once user export JSON, add an entry to Google Analytics
     */
    onjson() {
        this.gaService.gaTrackEvent('download', undefined, this.record['title'], this.getDownloadURL());
    }

    /**
     * return the URL that will download the NERDm metadata for the current resource
     */
    getDownloadURL() : string {
        let out = this.cfg.get("locations.mdService", "/od/id/");

        // We're now assuming use of resolver service; force NERDm JSON format
        if (out.slice(-1) != '/') out += '/';
        out += this.record['@id'] + "?format=nerdm";

        return out;
    }

    /**
     * Expand the JSON viewer to certain level.
     * @param depth : the level the JSON viewer will expand to.
     */
    expandToLevel(depth){
        this.jsonExpandDepth = depth;
        this.collapsed = false;
    }

    /**
     * Reture record level total download size
     */
    get totalDownloadSize() {
        if(this.metricsData != undefined)
            return formatBytes(this.metricsData.totalDownloadSize, 2);
        else
            return "";
    }

    copyToClipboard(val: string){
        const selBox = document.createElement('textarea');
        selBox.style.position = 'fixed';
        selBox.style.left = '0';
        selBox.style.top = '0';
        selBox.style.opacity = '0';
        selBox.value = val;
        document.body.appendChild(selBox);
        selBox.focus();
        selBox.select();
        document.execCommand('copy');
        document.body.removeChild(selBox);

        this.citeCopied = true;
        setTimeout(() => {
            this.citeCopied = false;
        }, 2000);

    }
}
