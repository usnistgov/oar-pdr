import { Component, Input, Pipe,PipeTransform } from '@angular/core';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';

@Component({
  selector: 'metadata-detail',
  template: `
    <div class="ui-g">
     <div *ngIf="inBrowser">
       <div [hidden]="!metadata" class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12" >
         <h3><b>Metadata</b></h3>
          <span style="">
            For more information about the metadata, consult the <a href="/od/dm/nerdm/" (click)="gaService.gaTrackEvent('outbound', undefined, 'Resource title: ' + record.title, '/od/dm/nerdm/')">NERDm documentation</a>. 
          </span>
          <a [href]='this.serviceApi' style="position:relative; float:right;">
          <button style="background-color: #1371AE;" type="button" pButton icon="faa faa-file-code-o"
                    title="Get Metadata in JSON format." label="json" (click)="onjson()"></button></a>
          <br>
          <span style="font-size:8pt;color:grey;" >* item[number] indicates an array not a key name</span>
          <br><br>
         <div *ngIf="inBrowser"><fieldset-view [entry]="record"></fieldset-view></div>
        </div>
      </div>
    </div>
  `
})

export class MetadataComponent {
  
  @Input() record: any[];
  @Input() serviceApi : string;
  @Input() metadata : boolean;
  @Input() inBrowser : boolean;

  constructor(private gaService: GoogleAnalyticsService){

  }

  ngOnInit() {
    if(this.record != undefined && this.record != null){
      delete this.record["_id"];
    }
  }
   
  generateArray(obj){
     return Object.keys(obj).map((key)=>{ return obj[key]; });
  }

  private testKeys: Object;
  private testVals;
   
   createKeyVal(objArray){
     this.testKeys = Object.keys(objArray);
     this.testVals = this.generateArray(objArray);
     let tempString ="";
     for(let v of this.testVals)
      tempString += v +",";
     return tempString;
  }

  isArray(obj : any ) {
     return Array.isArray(obj);
  }

  onjson(){
    this.gaService.gaTrackEvent('download', undefined, this.record['title'], this.serviceApi);
    //alert(this.serviceApi);
    // window.open(this.serviceApi);
  }
}
