import { Component, Input,ChangeDetectorRef ,Inject, Injectable,PLATFORM_ID} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { TreeNode} from 'primeng/api';
import { CartService} from '../../datacart/cart.service';
import { Data} from '../../datacart/data';
import {OverlayPanelModule} from 'primeng/overlaypanel';
import { OverlayPanel} from 'primeng/overlaypanel';
import {DialogModule} from 'primeng/dialog';
import { CommonModule } from "@angular/common";

@Component({
  moduleId: module.id,
  styleUrls: ['../landing.component.css'],
  selector: 'description-resources',
  templateUrl: `description.component.html`
})

export class DescriptionComponent {

 @Input() record: any[];
 @Input() files: TreeNode[];
 @Input() distdownload: string;
 @Input() editContent: boolean;
 @Input() filescount: number;

 addAllFileSpinner:boolean = false;
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
 selectedNodes: TreeNode[];
 addFileStatus:boolean = false;
 selectedNode : TreeNode;
 cols: any[];
 fileNode: TreeNode;
 

//  onNodeSelect(event, sdata){
//      alert("Node select ::"+sdata.name);
//  }
// nodeSelect(event) {
//     var test = this.getComponentDetails(this.record["components"],event.node.data);
//     let i =0;
//     this.fileDetails = '';
//     for(let t of test){
//         this.isFileDetails = true;
//         this.fileDetails = t;
//     }
//     alert("TEST");
// }

// getComponentDetails(data,filepath) {
//   return data.filter(
//       function(data){return data.filepath == filepath }
//   );
// }

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
 
 isNodeSelected: boolean = false;
 openDetails(event,fileNode: TreeNode, overlaypanel: OverlayPanel) {
    // console.log(JSON.stringify(fileNode));
    this.isNodeSelected = true;
    this.fileNode = fileNode;
    overlaypanel.hide();
     setTimeout(() => {
         overlaypanel.show(event);
     },100);
 }
 ngOnInit(){
    this.cdr.detectChanges();
    this.files  =<TreeNode[]>this.files[0].data;
    
    //console.log(this.files);
    this.cols = [
        { field: 'name', header: 'Name', width: '60%' },
        { field: 'mediatype', header: 'MediaType', width: '15%' },
        { field: 'size', header: 'Size', width: '12%' },
        { field: 'download', header: 'Download', width: '10%' },
    ];
    //this.selectedNode = this.files[0];
    this.fileNode = {"data":{
        "name":"",
        "size":"",
        "mediatype":"",
        "description":"",
        "filetype":""
    }}
 }
 ngOnChanges(){
    this.checkAccesspages();
 }
 editDecription(){

 }
 //Datacart related code
 addFilesToCart() {

    let data: Data;
    let compValue: any;
    this.cartService.updateAllFilesSpinnerStatus(true);
    for (let comp of this.record["components"]) {
        if (typeof comp["downloadURL"] != "undefined") {
            data = {
                'resId': this.record["@id"],
                'resTitle': this.record["title"],
                'id': comp["title"],
                'fileName': comp["title"],
                'filePath': comp["filepath"],
                'fileSize': comp["size"],
                'downloadURL': comp["downloadURL"],
                'fileFormat': comp["mediaType"],
                'downloadedStatus': null,
                'resFilePath': ''
            };
            this.cartService.addDataToCart(data);
            data = null;
        }
    }

    setTimeout(() => {
        this.cartService.updateAllFilesSpinnerStatus(false);
    }, 3000);
    setTimeout(() => {
         this.addFileStatus = true;
    }, 3000);
}
//record["ediid"], record["title"], fileDetails["title"], fileDetails["title"],
//fileDetails["filepath"],fileDetails["filepath"],fileDetails["size"],
//fileDetails["downloadURL"], fileDetails["mediaType"],"resource",null)
// addtoCart(resFilePath:string,id:string,fileName:string,
//     filePath:string,fileSize:number,downloadURL:string,
//     fileFormat:string,dataset:string,downloadedStatus:boolean){
//     this.cartService.updateFileSpinnerStatus(true);
//     let data : Data;
//     data = {'resId':this.record['ediid'],'resTitle':this.record['title'],'resFilePath':'resFilePath',
//             'id':id,'fileName':fileName,'filePath':filePath,
//             'fileSize':fileSize,'downloadURL':downloadURL,
//             'fileFormat':fileFormat,'downloadedStatus':downloadedStatus };
//     this.cartService.addDataToCart(data);
//     setTimeout(()=> {
//         this.cartService.updateFileSpinnerStatus(false);
//     }, 3000);
// }
addtoCart(fileName:string,fileSize:number,fileFormat:string,
    downloadURL:string,
    dataset:string,downloadedStatus:boolean){
    this.cartService.updateFileSpinnerStatus(true);
    let data : Data;
    data = {'resId':this.record['ediid'],'resTitle':this.record['title'],
            'resFilePath':'resFilePath',
            'id':fileName,'fileName':fileName,'filePath':fileName,
            'fileSize':fileSize,'downloadURL':downloadURL,
            'fileFormat':fileFormat,'downloadedStatus': null };
    this.cartService.addDataToCart(data);
    setTimeout(()=> {
        this.cartService.updateFileSpinnerStatus(false);
    }, 3000);
}
 constructor(private cartService: CartService,private cdr: ChangeDetectorRef) {
     this.cartService.watchAddAllFilesCart().subscribe(value => {
     this.addAllFileSpinner = value;
     });
 }

 display: boolean = false;

//  showDialog(selectedNode: TreeNode) {
//      this.selectedNode = selectedNode;
//      this.display = true;
//  }
 /**
   * Function to display bytes in appropriate format.
   **/ 
  formatBytes(bytes,numAfterDecimal){
    if(0==bytes)return"0 Bytes";
    var base=1000,
    d=numAfterDecimal||2,
     e=["Bytes","kB","MB","GB","TB","PB","EB","ZB","YB"],
     f=Math.floor(Math.log(bytes)/Math.log(base));
    return (bytes/Math.pow(base,f)).toFixed(d)+" "+e[f]
}
 
}
