import { Component, Input,ChangeDetectorRef ,Inject, Injectable,PLATFORM_ID} from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { LandingComponent } from './landing.component';
import { MenuItem } from 'primeng/primeng';
import { TreeTableModule} from 'primeng/treetable';
import { TreeNode} from 'primeng/api';

@Component({
  moduleId: module.id,
  styleUrls: ['landing.component.css'],
  selector: 'description-resources',
  template: `
          <!--div class="ui-g">
          <div class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12"-->
          <h3 id="description" name="desscription"><b>Description</b></h3>
          <i *ngIf="loginuser" style="float:right" class="faa faa-edit"></i>
                <div contenteditable="true" id="recordDescription" class="well welldesc">
                <p  *ngFor="let topic of record['description']; let i =index">
                {{ record["description"][i] }}
                </p>
                </div>

            <div *ngIf="checkTopics()">
            <strong contenteditable="{{editContent}}" >Research Topics:</strong>
            <span  *ngFor="let topic of record['topic']; let i =index">
                {{ topic.tag }}
                <span *ngIf="i < record['topic'].length-1 ">,</span>
            </span>
            <i *ngIf="loginuser" style="float:right" class="faa faa-edit"></i>
            </div>
            <div *ngIf="checkKeywords()">
                <b>Subject Keywords:</b>
                <span contenteditable="true"  *ngFor="let keyword of record['keyword']; let i =index">
                    {{ keyword }}<span *ngIf="i < record['keyword'].length-1 ">,</span>
                </span> 
                <i *ngIf="loginuser" style="float:right" class="faa faa-edit"></i>
            </div>
            <br>
            
            <div>
             <h3><b>Data Access</b></h3>
             <span *ngIf="record['accessLevel'] === 'public'"><i class="faa faa-globe"></i> 
                These data are public . 
             </span>
             <span *ngIf="record['accessLevel'] === 'restricted public'"><i class="faa faa-lock"></i> 
                This data has access restrictions. 
             </span>   
             <br>
             <span *ngIf="record['rights']"> 
                The access rights are {{ record.rights }} 
             </span>
             <br>
             <span style="margin-left:0em" *ngIf="isAccessPage">Data is available via the following locations: 
             <br>   
                <span style="padding-left:2.75em" *ngFor="let title of accessTitles; let i =index">
                    <i class="faa faa-external-link"> <a href="{{accessUrls[i]}}">{{title}}</a> 
                    </i><br>
                </span>
             </span>
            
            
            </div> 
            <div *ngIf="files.length != 0">           
                <h3 id="files" name="files"><b>Files</b>
                   <a href="{{distdownload}}" class="faa faa-file-archive-o" title="Download All Files" ></a>
                </h3> <i *ngIf="loginuser" style="float:right" class="faa faa-edit"></i>
                <div class="ui-g">
                    <div class="ui-g-6 ui-md-6 ui-lg-6 ui-sm-12">
                    <p-treeTable [value]="files">
                    <ng-template pTemplate="header">
                        <tr>
                            <th>Name</th>
                            <th>Size</th>
                            <th>Type</th>
                        </tr>
                    </ng-template>
                    <ng-template pTemplate="body" let-rowNode let-rowData="rowData">
                        <tr>
                            <td>
                                <p-treeTableToggler [rowNode]="rowNode"></p-treeTableToggler>
                                {{rowData.name}}
                            </td>
                            <td></td>
                            <td></td>
                        </tr>            
                    </ng-template>
                </p-treeTable>
                    </div>
                    <div class="ui-g-6 ui-md-6 ui-lg-6 ui-sm-12">
                        <div *ngIf="isBrowser" ng2-sticky>
                            <div *ngIf="isFileDetails">
                                <filedetails-resources [fileDetails]="fileDetails"></filedetails-resources>
                            </div>
                            <div *ngIf="!isFileDetails">
                                <div class="fileinfocard ">
                                    <div class="ui-g fileinfosection">
                                        <span>Click on the file name to view details.</span>   
                                    </div>
                                </div>         
                            </div>
                        </div>
                    </div>
                </div>
            </div>
          
            <div *ngIf="checkReferences()">
             <h3 id="reference" name="reference"><b>References:</b></h3>
                <span *ngIf="isDocumentedBy"> 
                    This data is discussed in :
                    <span style="padding-left:2.75em" *ngFor="let refs of record['references']">
                        <span *ngIf="refs['refType'] == 'IsDocumentedBy'">
                            <br> <i class="faa faa-external-link">
                                 <a href={{refs.location}} target="blank">{{ refs.label }}</a>
                                 </i>
                        </span>
                        <i *ngIf="loginuser" style="float:right" class="faa faa-edit"></i>
                    </span>
                    <br>
                </span>
                <span *ngIf="isReferencedBy"> 
                    This data is referenced in :
                    <span style="padding-left:2.75em" *ngFor="let refs of record['references']">
                        <span *ngIf="refs['refType'] == 'IsReferencedBy'">
                            <br> <i class="faa faa-external-link">
                            <a href={{refs.location}} target="blank">{{ refs.location }}</a>
                            </i>
                        </span>
                    </span>
                    <i *ngIf="loginuser" style="float:right" class="faa faa-edit"></i>
                </span>
            </div>
        <!--/div-->
     <!--/div-->
  `
})

export class DescriptionComponent {

 @Input() record: any[];
 @Input() files: TreeNode[];
 @Input() distdownload: string;
 @Input() editContent: boolean;
 @Input() loginuser: boolean;

 fileDetails:string = '';
 isFileDetails: boolean = false;
 isReference: boolean = false;
 selectedFile: TreeNode;
 isAccessPage : boolean = false;
 accessPages: Map <string, string> = new Map();
 accessUrls : string[] =[];
 accessTitles : string[] =[];
 isReferencedBy : boolean = false;
 isDocumentedBy : boolean = false;
 

 nodeSelect(event) {
    var test = this.getComponentDetails(this.record["components"],event.node.data);
    let i =0;
    this.fileDetails = '';
    for(let t of test){
        this.isFileDetails = true;
        this.fileDetails = t;
    }
  }
getComponentDetails(data,filepath) {
  return data.filter(
      function(data){return data.filepath == filepath }
  );
}

keys() : Array<string> {
    return Object.keys(this.fileDetails);
}

checkReferences(){
      if(Array.isArray(this.record['references']) ){
        for(let ref of this.record['references'] ){
            if(ref.refType === 'IsDocumentedBy') this.isDocumentedBy = true;
            if(ref.refType === 'IsReferencedBy') this.isReferencedBy = true;
        }
        if(this.isDocumentedBy || this.isReferencedBy)
        return true;
      }
 }


 checkKeywords(){
    if(Array.isArray(this.record['keyword']) ){
        if(this.record['keyword'].length > 0)
            return true;
        else 
            return false;    
    }
    else {
        return false;
    }
 }
 checkTopics(){
    if(Array.isArray(this.record['topic']) ){
        if(this.record['topic'].length > 0)
            return true;
        else 
            return false;    
    }
    else {
        return false;
    }
 }
 checkAccesspages(){
    if(Array.isArray(this.record['inventory']) ){
        if(this.record['inventory'][0].forCollection == "") {
            for(let inv of this.record['inventory'][0].byType ){
                if(inv.forType == "nrdp:AccessPage") 
                    this.isAccessPage = true;
            }
        }
    }
    if(this.isAccessPage){
        this.accessPages = new Map();
        for(let comp of this.record['components']){
            if(comp['@type'].includes("nrdp:AccessPage"))
            { 
                if(comp["title"] !== "" && comp["title"] !== undefined)
                    this.accessPages.set(comp["title"], comp["accessURL"]);
                else   
                    this.accessPages.set(comp["accessURL"], comp["accessURL"]);
            }
        }
    }

    this.accessTitles = Array.from(this.accessPages.keys());
    
    this.accessUrls = Array.from(this.accessPages.values());
 }
 

 ngOnInit(){
    this.cdr.detectChanges();
    console.log("Test 1:"+JSON.stringify(this.files));
    this.files  = this.files[0].data;
    console.log("Test 2:"+JSON.stringify(this.files));
    // this.http.get('assets/testdata.json')
    // .toPromise()
    // .then(res => this.files= <TreeNode[]> res["data"]);
    // console.log("Test 2:"+this.files);
 }
 ngOnChanges(){
    this.checkAccesspages();
 }
 editDecription(){

 }
 constructor(private cdr: ChangeDetectorRef, private http: HttpClient) {
        
    
    } 
}
