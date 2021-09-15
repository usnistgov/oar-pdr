import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';

@Component({
  selector: 'metadata-detail',
  templateUrl: './metadata.component.html',
  styleUrls: ['./metadata.component.css']
})
export class MetadataComponent implements OnChanges {
    nerdmRecord: any = {};
    showJson: boolean = true;
    isOpen: boolean = false;
    // JSON viewer expand depth. Default is all.
    _jsonExpandDepth = "";

    private _collapsed: boolean = true;
    @Input() record: NerdmRes;
    @Input() inBrowser: boolean;

    // Flag to tell if current screen size is mobile or small device
    @Input() mobileMode : boolean|null = false;

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
        let out = this.cfg.get("locations.mdService", "/unconfigured");
        console.log('mdService', out);
        if (out.search("/rmm/") >= 0) {
            if(!out.endsWith("records/")){
                out += "records/";
            }
            out += "?@id=" + this.record['@id'];
        }else {
            if (out.slice(-1) != '/') out += '/';
            out += this.record['ediid'];
        }

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
}
