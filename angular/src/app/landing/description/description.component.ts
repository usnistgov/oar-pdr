import { Component, Input,ChangeDetectorRef } from '@angular/core';
import { TreeNode} from 'primeng/api';
import { CartService} from '../../datacart/cart.service';
import { Data} from '../../datacart/data';
import { OverlayPanel} from 'primeng/overlaypanel';
import { stringify } from '@angular/compiler/src/util';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { SelectItem, DropdownModule, ConfirmationService,Message } from 'primeng/primeng';

@Component({
  moduleId: module.id,
  styleUrls: ['../landing.component.css'],
  selector: 'description-resources',
  templateUrl: `description.component.html`,
  providers: [ConfirmationService]
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
    cartMap: any[];
    allSelected: boolean = false;
    allDownloaded: boolean = false;

    /* Function to Return Keys object properties */
    keys() : Array<string> {
        return Object.keys(this.fileDetails);
    }

    constructor(private cartService: CartService,
        private cdr: ChangeDetectorRef,
        private downloadService: DownloadService,
        private confirmationService: ConfirmationService) {
            this.cartService.watchAddAllFilesCart().subscribe(value => {
            this.addAllFileSpinner = value;
        });
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
        // this.cartService.clearTheCart();
        // this.cdr.detectChanges();
        if(this.files.length != 0)
            this.files  =<TreeNode[]>this.files[0].data;
        this.cols = [
            { field: 'name', header: 'Name', width: '50%' },
            { field: 'mediatype', header: 'MediaType', width: '15%' },
            { field: 'size', header: 'Size', width: '12%' },
            { field: 'download', header: 'Download', width: '12%' },
            { field: 'cart', header: 'Cart', width: '10%' },];
    
        this.fileNode = {"data":{ "name":"", "size":"", "mediatype":"", "description":"", "filetype":"" }};

        this.cartMap = this.cartService.getCart();
        this.updateCartStatus(this.files);
        this.updateDownloadStatus(this.files);
    }
 
    ngOnChanges(){
       this.checkAccesspages();
    }

    updateCartStatus(files: any){
        for (let comp of files) {
            if(comp.children.length > 0){
                this.updateCartStatus(comp.children);
            }else{
                comp.data.isSelected = this.selected(comp.data.resId);
            }
        }   
        this.checkIfAllSelected(this.files);     
    }

//     //Datacart related code
    addFilesToCart(files: any) {
        let data: Data;
        let compValue: any;
        this.cartService.updateAllFilesSpinnerStatus(true);

        // for (let comp of this.record["components"]) {
        //     if (typeof comp["downloadURL"] != "undefined") {
                // data = {
                //     'resId': comp["@resId"].replace(/^.*[\\\/]/, ''),
                //     'resTitle': this.record["title"],
                //     'id': this.record["title"],
                //     'fileName': comp["title"],
                //     'filePath': comp["filepath"],
                //     'fileSize': comp["size"],
                //     'downloadURL': comp["downloadURL"],
                //     'fileFormat': comp["mediaType"],
                //     'downloadedStatus': null,
                //     'resFilePath': ''
                // };
                // this.cartService.addDataToCart(data);
                // data = null;
        //     }
        // }

        for (let comp of files) {
            if(comp.children.length > 0){
                this.addFilesToCart(comp.children);
            }else{
                this.addtoCart(comp.data);
            }
        }

        setTimeout(() => {
            this.cartService.updateAllFilesSpinnerStatus(false);
        }, 3000);
        setTimeout(() => {
            this.addFileStatus = true;
        }, 3000);
    }

    removeFilesFromCart(files: any){
        for (let comp of files) {
            if(comp.children.length > 0){
                this.removeFilesFromCart(comp.children);
            }else{
                this.addtoCart(comp.data);
                this.cartService.removeResId(comp.data.resId);
                comp.data.isSelected = false;
            }
        }
        this.checkIfAllSelected(this.files);
    }

    addtoCart(rowData:any){
        this.cartService.updateFileSpinnerStatus(true);
        let data : Data;
        data = {'resId':rowData.resId,
                'resTitle':this.record['title'],
                'resFilePath':rowData.fullPath,
                'id':rowData.name,
                'fileName':rowData.name,
                'filePath':rowData.fullPath,
                'fileSize':rowData.size,
                'downloadURL':rowData.downloadUrl,
                'fileFormat':rowData.mediatype,
                'downloadedStatus': null };

        this.cartService.addDataToCart(data);
        rowData.isSelected = this.selected(rowData.resId);
        this.checkIfAllSelected(this.files);

        setTimeout(()=> {
            this.cartService.updateFileSpinnerStatus(false);
        }, 3000);
    }

    checkIfAllSelected(files: any){
        this.allSelected = true;
        for (let comp of files) {
            if(comp.children.length > 0){
                this.checkIfAllSelected(comp.children);
            }else{
                if(!comp.data.isSelected){
                    this.allSelected = false;
                }
            }
        }   
    }

    updateDownloadStatus(files: any){
        this.allDownloaded = true;
        for (let comp of files) {
            if(comp.children.length > 0){
                this.updateDownloadStatus(comp.children);
            }else{
                if(comp.data.downloadedStatus != 'downloaded'){
                    this.allDownloaded = false;
                }
            }
        }   
    }

    selected(resId:string){
        this.cartMap = this.cartService.getCart();

        for (let key in this.cartMap) {
            let value = this.cartMap[key];
            if (value.data.resId == resId) {
                return true;
            }
        }
        return false;
    }

    removeCart(rowData:any, resId: string){
        this.cartService.updateFileSpinnerStatus(true);
        this.cartService.removeResId(resId);
        rowData.isSelected = this.selected(resId);
        this.checkIfAllSelected(this.files);

        setTimeout(()=> {
            this.cartService.updateFileSpinnerStatus(false);
        }, 3000);
    }

    setDownloadStatus(rowData:any){
        rowData.downloadedStatus = 'downloaded';
    }

    downloadFile(rowData:any){
        let filename = decodeURI(rowData.downloadUrl).replace(/^.*[\\\/]/, '');
        rowData.downloadedStatus = 'downloading';
        this.cartService.updateFileSpinnerStatus(true);

        this.downloadService.getFile(rowData.downloadUrl).subscribe(blob => {
            this.downloadService.saveToFileSystem(blob, filename);
            rowData.downloadedStatus = 'downloaded';
            this.cartService.updateFileSpinnerStatus(false);
            this.updateDownloadStatus(this.files);
            },
            error => console.log('Error downloading the file.')
        )
    }

    downloadAllFile(files:any){
        for (let comp of files) {
            if(comp.children.length > 0){
                this.downloadAllFile(comp.children);
            }else{
                if(comp.data.downloadUrl){
                    this.downloadFile(comp.data);
                }
            }
        }   
    }

    downloadAllConfirm(header:string, massage:string, key:string) {
        this.confirmationService.confirm({
          message: massage,
          header: header,
          key: key,
          accept: () => {
            this.downloadAllFile(this.files);
          },
          reject: () => {
          }
        });
    }

    resetDownloadStatus(rowData){
        rowData.downloadedStatus = null;
    }
}
