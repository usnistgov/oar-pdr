import { Component, Input,ChangeDetectorRef } from '@angular/core';
import { TreeNode} from 'primeng/api';
// import { CartService} from '../../datacart/cart.service';
// import { Data} from '../../datacart/data';
import { OverlayPanel} from 'primeng/overlaypanel';

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
 @Input() metadata: boolean;

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
 display: boolean = false;

    /* Function to Return Keys object properties */
    keys() : Array<string> {
        return Object.keys(this.fileDetails);
    }

    /**
     * Function to Check whether given record has references in it.
     */
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

    /**
     * Function to Check whether record has keyword
     */
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
    
    /**
     * Function to Check record has topics
     */
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

    /**
     * Function to Check if there are accesspages in the record inventory and components
     */
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

    /**
    * Function to display bytes in appropriate format.
    **/ 
    formatBytes(bytes, numAfterDecimal) {
        if (0==bytes) return"0 Bytes" ;
        if (1 ==bytes) return"1 Byte" ;
        var base = 1000,
            e=["Bytes","kB","MB","GB","TB","PB","EB","ZB","YB"],
            d = numAfterDecimal||1,
            f = Math.floor(Math.log(bytes)/Math.log(base));
        
        var v = bytes/Math.pow(base,f);
        if (f == 0) // less than 1 kiloByte
            d = 0;
        else if (numAfterDecimal == null && v < 10.0)
            d = 2;
        return v.toFixed(d)+" "+e[f];
    }
 
    isNodeSelected: boolean = false;
    openDetails(event,fileNode: TreeNode, overlaypanel: OverlayPanel) {
        this.isNodeSelected = true;
        this.fileNode = fileNode;
        overlaypanel.hide();
        setTimeout(() => {
            overlaypanel.show(event);
        },100);
    }
    
    ngOnInit(){
        // this.cdr.detectChanges();
        if(this.files.length != 0)
            this.files  =<TreeNode[]>this.files[0].data;
        this.cols = [
            { field: 'name', header: 'Name', width: '60%' },
            { field: 'mediatype', header: 'MediaType', width: '15%' },
            { field: 'size', header: 'Size', width: '12%' },
            { field: 'download', header: 'Download', width: '10%' },];
    
        this.fileNode = {"data":{ "name":"", "size":"", "mediatype":"", "description":"", "filetype":"" }}
    }
 
    ngOnChanges(){
       this.checkAccesspages();
    }

//     //Datacart related code
//     addFilesToCart() {
//         let data: Data;
//         let compValue: any;
//         this.cartService.updateAllFilesSpinnerStatus(true);
//         for (let comp of this.record["components"]) {
//             if (typeof comp["downloadURL"] != "undefined") {
//                 data = {
//                     'resId': this.record["@id"],
//                     'resTitle': this.record["title"],
//                     'id': comp["title"],
//                     'fileName': comp["title"],
//                     'filePath': comp["filepath"],
//                     'fileSize': comp["size"],
//                 'downloadURL': comp["downloadURL"],
//                 'fileFormat': comp["mediaType"],
//                 'downloadedStatus': null,
//                 'resFilePath': ''
//             };
//             this.cartService.addDataToCart(data);
//             data = null;
//         }
//     }

//     setTimeout(() => {
//         this.cartService.updateAllFilesSpinnerStatus(false);
//     }, 3000);
//     setTimeout(() => {
//          this.addFileStatus = true;
//     }, 3000);
// }
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
// addtoCart(fileName:string,fileSize:number,fileFormat:string,
//     downloadURL:string,
//     dataset:string,downloadedStatus:boolean){
//     this.cartService.updateFileSpinnerStatus(true);
//     let data : Data;
//     data = {'resId':this.record['ediid'],'resTitle':this.record['title'],
//             'resFilePath':'resFilePath',
//             'id':fileName,'fileName':fileName,'filePath':fileName,
//             'fileSize':fileSize,'downloadURL':downloadURL,
//             'fileFormat':fileFormat,'downloadedStatus': null };
//     this.cartService.addDataToCart(data);
//     setTimeout(()=> {
//         this.cartService.updateFileSpinnerStatus(false);
//     }, 3000);
// }
//  constructor(private cartService: CartService,private cdr: ChangeDetectorRef) {
//      this.cartService.watchAddAllFilesCart().subscribe(value => {
//      this.addAllFileSpinner = value;
//      });
//  }

}
