import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';

@Component({
  selector: 'metadata-detail',
  template: `
    <div class="ui-g" id="metadata-nerdm">
      <div *ngIf="inBrowser">
        <p style="margin-bottom: 0pt;">
          <span style="">
            For more information about the metadata, consult the 
            <a href="/od/dm/nerdm/" (click)="gaService.gaTrackEvent('outbound', undefined, 'Resource title: ' + record.title, '/od/dm/nerdm/')">NERDm documentation</a>. 
          </span>
          <a [href]='getDownloadURL()' style="position:relative; float:right;">
          <button style="background-color: #1371AE; color: white;" type="button" pButton 
                  icon="faa faa-file-code-o" title="Get Metadata in JSON format." label="JSON" 
                  (click)="onjson()"></button></a>
          <br/>
          <span style="font-size:8pt;color:grey;" >* "item [<i>number</i>]" indicates an item in a list</span>
        </p>
        <div *ngIf="inBrowser"><fieldset-view [entry]="record"></fieldset-view></div>
      </div>
    </div>
  `
})
export class MetadataComponent implements OnChanges {
    @Input() record: NerdmRes;
    @Input() inBrowser : boolean;

    constructor(private cfg: AppConfig, private gaService: GoogleAnalyticsService) {  }

    ngOnChanges(changes: SimpleChanges) {
        if (this.record && this.record["_id"]) 
            delete this.record["_id"];
    }
     
    onjson() {
        this.gaService.gaTrackEvent('download', undefined, this.record['title'], this.getDownloadURL());
    }

    /**
     * return the URL that will download the NERDm metadata for the current resource
     */
    getDownloadURL() : string {
        let out = this.cfg.get("locations.mdService", "/unconfigured");

        if (out.search("/rmm/") >= 0) 
            out += "?@id=" + this.record['@id'];
        else {
            if (out.slice(-1) != '/') out += '/';
            out += this .record['ediid'];
        }

        return out;
    }
}
