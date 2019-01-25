import { Component, Input,ChangeDetectorRef } from '@angular/core';
import { TreeNode} from 'primeng/api';
import { CartService} from '../../datacart/cart.service';
import { Data} from '../../datacart/data';
import { OverlayPanel} from 'primeng/overlaypanel';
import { stringify, error } from '@angular/compiler/src/util';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { SelectItem, DropdownModule, ConfirmationService,Message } from 'primeng/primeng';
import { DownloadData } from '../../shared/download-service/downloadData';
import { ZipData } from '../../shared/download-service/zipData';
import { CommonVarService } from '../../shared/common-var';
import { environment } from '../../../environments/environment';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse, HttpEvent } from '@angular/common/http'; 
import { TestBed } from '@angular/core/testing';


declare var saveAs: any;

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
    displayDownloadFiles: boolean = false;
    cartMap: any[];
    allSelected: boolean = false;
    allDownloaded: boolean = false;
    ediid:any;
    downloadStatus: any = null;
    totalFiles: any;
    downloadData: DownloadData[];
    zipData: ZipData[] = [];
    isExpanded: boolean = true;
    visible: boolean = true;
    cancelAllDownload: boolean = false;
    cartLength : number;
    treeRoot = [];
    showZipFiles: boolean = true;
    subscriptions: any = [];
    allProcessed: boolean = false;
    downloadStatusExpanded: boolean = true;
    bundlePlanStatus: any;
    bundlePlanMessage: any[];
    bundlePlanUnhandledFiles: any[] = null;
    showUnhandledFiles: boolean = true;
    showZipFilesNmaes: boolean = true;
    showMessageBlock: boolean = false;
    messageColor: any;
    noFileDownloaded: boolean; // will be true if any item in data cart is downloaded

    private distApi : string = environment.DISTAPI;
    // private distApi : string = "";

    /* Function to Return Keys object properties */
    keys() : Array<string> {
        return Object.keys(this.fileDetails);
    }

    constructor(private cartService: CartService,
        private cdr: ChangeDetectorRef,
        private downloadService: DownloadService,
        private commonVarService:CommonVarService,
        private http: HttpClient,
        private confirmationService: ConfirmationService) {
            this.cartService.watchAddAllFilesCart().subscribe(value => {
            this.addAllFileSpinner = value;
            });
            this.cartService.watchStorage().subscribe(value => {
                this.cartLength = value;
            });
    }

    ngOnInit(){
        // this.cartService.clearTheCart();
        // this.cdr.detectChanges();

        if(this.files.length != 0)
            this.files  =<TreeNode[]>this.files[0].data;
        this.cols = [
            { field: 'name', header: 'Name', width: '60%' },
            { field: 'mediatype', header: 'MediaType', width: '15%' },
            { field: 'size', header: 'Size', width: '12%' },
            { field: 'download', header: 'Download', width: '10%' }];
    
        this.fileNode = {"data":{ "name":"", "size":"", "mediatype":"", "description":"", "filetype":"" }};

        this.cartMap = this.cartService.getCart();
        this.ediid = this.commonVarService.getEdiid();

        const newPart = {
            data : {
                cartId: "/",
                ediid: this.ediid,
                name : "files",
                mediatype: "",
                size: null,
                downloadURL: null,
                description: null,
                filetype: null,
                resId: "files",
                filePath: "/",
                downloadProgress: 0,
                downloadInstance: null,
                isSelected: false,
                zipFile: null
            },children: []
          };
          newPart.children = this.files;
          this.treeRoot.push(newPart);

          this.updateStatusFromCart();

          // this.updateCartStatus(this.files);
          this.updateAllSelectStatus(this.files);
          this.downloadStatus = this.updateDownloadStatus(this.files)?"downloaded":null;
  
          this.totalFiles = 0;
          this.getTotalFiles(this.files);
  
          this.expandToLevel(this.files, true, 2);

          this.downloadService.watchDownloadProcessStatus("landingPage").subscribe(
            value => {
                this.allProcessed = value;
                if(this.allProcessed){
                    this.downloadStatus = "downloaded";
                }
                this.downloadStatus = this.updateDownloadStatus(this.files)?"downloaded":null;
            }
        );
        this.downloadService.watchAnyFileDownloaded().subscribe(
            value => {
                this.noFileDownloaded = !value;
            }
        );
        //   console.log("this.downloadStatus:");
        //   console.log(this.downloadStatus);
    }

    expandToLevel(dataFiles: any, option: boolean, targetLevel: any){
        this.expandAll(dataFiles, option, 0, targetLevel)
    }

    expandAll(dataFiles: any, option: boolean, level: any, targetLevel: any){
        let currentLevel = level + 1;
        for ( let i=0; i < dataFiles.length; i++ ) {
            dataFiles[i].expanded = option;
            if(targetLevel != null){
                if(dataFiles[i].children.length > 0 && currentLevel < targetLevel){
                    this.expandAll(dataFiles[i].children, option, currentLevel, targetLevel);
                }
            }else{
                if(dataFiles[i].children.length > 0){
                    this.expandAll(dataFiles[i].children, option, currentLevel, targetLevel);
                }
            }
        }
        this.isExpanded = option;
        this.visible = false;
        setTimeout(() => {
            this.visible = true;
        },0);
    }

    /**
     * Function to sync the download status from data cart.
     */
    updateStatusFromCart(){
        for (let key in this.cartMap) {
            let value = this.cartMap[key];
            if(value.data.downloadStatus != undefined){
                this.setFilesDownloadStatus(this.files, value.data.cartId, value.data.downloadStatus);
            }
            if(value.data.cartId != undefined){           
                let treeNode = this.searchTree(this.treeRoot[0], value.data.cartId);
                if(treeNode != null){
                    treeNode.data.isSelected = true;
                }
            }
        }
        // this.updateDownloadStatus(this.files);
    }

    /**
     * Function to get total number of files.
     */
    getTotalFiles(files){
        for (let comp of files) {
            if(comp.children.length > 0){
                this.getTotalFiles(comp.children);
            }else{
                this.totalFiles = this.totalFiles + 1;
            }
        }        
    }

    /**
     * Function to set files download status.
     */
    setFilesDownloadStatus(files, cartId, downloadStatus){
        for (let comp of files) {
            if(comp.children.length > 0){
                this.setFilesDownloadStatus(comp.children, cartId, downloadStatus);
            }else{
                if(comp.data.cartId == cartId){
                    comp.data.downloadStatus = downloadStatus;
                }
            }
        }
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
 
    ngOnChanges(){
       this.checkAccesspages();
    }

    // updateCartStatus(files: any){
    //     for (let comp of files) {
    //         if(comp.children.length > 0){
    //             this.updateCartStatus(comp.children);
    //         }else{
    //             comp.data.isSelected = this.isInDataCart(comp.data.cartId);
    //         }
    //     }   
    //     this.updateAllSelectStatus(this.files);     
    // }

    addSubFilesToCart(rowData: any) {
        let data: Data;
        let compValue: any;
        // this.cartService.updateAllFilesSpinnerStatus(true);

        if(!this.isFile(rowData)){
            let subFiles: any = null;
            for (let comp of this.files) {
                subFiles = this.searchTree(comp, rowData.cartId);
                if(subFiles != null){
                    break;
                }
            }
            if(subFiles != null){
                this.addFilesToCart(subFiles.children);
                rowData.isSelected = true;
            }
        }else{
            this.addtoCart(rowData);
        }

        this.allSelected = true;
        this.updateAllSelectStatus(this.files);

        // setTimeout(() => {
        //     this.cartService.updateAllFilesSpinnerStatus(false);
        // }, 3000);
        // setTimeout(() => {
        //     this.addFileStatus = true;
        // }, 3000);
    }

    searchTree(element, cartId){
        if(element.data.cartId == cartId){
             return element;
        }else if (element.children.length > 0){
             var i;
             var result = null;
             for(i=0; result == null && i < element.children.length; i++){
                  result = this.searchTree(element.children[i], cartId);
             }
             return result;
        }
        return null;
   }

   addAllFilesToCart(){
       this.addFilesToCart(this.files);
       this.allSelected = true;
       this.updateAllSelectStatus(this.files);
   }

//     //Datacart related code
    addFilesToCart(files: any) {
        let data: Data;
        let compValue: any;
        // this.cartService.updateAllFilesSpinnerStatus(true);

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
                //     'downloadStatus': null,
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

        // setTimeout(() => {
        //     this.cartService.updateAllFilesSpinnerStatus(false);
        // }, 3000);
        // setTimeout(() => {
        //     this.addFileStatus = true;
        // }, 3000);
    }

    removeFromNode(rowData:any){
        this.removeCart(rowData);
        this.allSelected = false;
        this.updateAllSelectStatus(this.files);
    }

    removeCart(rowData:any){
        if(!this.isFile(rowData)){
            let subFiles: any = null;
            for (let comp of this.files) {
                subFiles = this.searchTree(comp, rowData.cartId);
                if(subFiles != null){
                    break;
                }
            }
            if(subFiles != null){
                this.removeFilesFromCart(subFiles.children);
                rowData.isSelected = false; 
            }
        }else{
            this.cartService.removeCartId(rowData.cartId);
            rowData.isSelected = false;        
        }
    }

    removeFilesFromCart(files: any){
        this.removeFromCart(files);
        this.allSelected = true;
        this.updateAllSelectStatus(this.files);
    }

    removeFromCart(files: any){
        for (let comp of files) {
            if(comp.children.length > 0){
                comp.data.isSelected = false;
                this.removeFromCart(comp.children);
            }else{
                this.cartService.removeCartId(comp.data.cartId);
                comp.data.isSelected = false;
            }
        }
        
    }

    addtoCart(rowData:any){
        // this.cartService.updateFileSpinnerStatus(true);
        let data : Data;
        data = {'cartId':rowData.cartId,
                'ediid' :this.ediid,
                'resId':rowData.resId,
                'resTitle':this.record['title'],
                'resFilePath':rowData.filePath,
                'id':rowData.name,
                'fileName':rowData.name,
                'filePath':rowData.filePath,
                'fileSize':rowData.size,
                'filetype' :rowData.filetype,
                'downloadURL':rowData.downloadURL,
                'mediatype':rowData.mediatype,
                'downloadStatus': null,
                'description':rowData.description
        };

        this.cartService.addDataToCart(data);
        rowData.isSelected = this.isInDataCart(rowData.cartId);

        // setTimeout(()=> {
        //     this.cartService.updateFileSpinnerStatus(false);
        // }, 3000);
    }

    updateAllSelectStatus(files: any){
        var allSelected = true;
        for (let comp of files) {
            if(comp.children.length > 0){
                comp.data.isSelected = this.updateAllSelectStatus(comp.children);
                allSelected = allSelected && comp.data.isSelected;
            }else{
                if(!comp.data.isSelected){
                    this.allSelected = false;
                    allSelected = false;
                }
            }
        }   

        return allSelected;
    }

    updateDownloadStatus(files: any){
        var allDownloaded = true;
        var noFileDownloadedFlag = true;
        for (let comp of files) {
            if(comp.children.length > 0){
                var status = this.updateDownloadStatus(comp.children);
                if(status){
                    comp.data.downloadStatus = 'downloaded';
                    this.cartService.updateCartItemDownloadStatus(comp.data.cartId,'downloaded');
                }
                allDownloaded = allDownloaded && status;
            }else{
                if(comp.data.downloadStatus != 'downloaded'){
                    allDownloaded = false;
                }
                if(comp.data.downloadStatus == 'downloaded' && comp.data.isSelected){
                    noFileDownloadedFlag = true;
                }
            }
        }   

        this.downloadService.setFileDownloadedFlag(!noFileDownloadedFlag);
        return allDownloaded;
    }

    /**
    * Function to check if cartId is in the data cart.
    **/ 
    isInDataCart(cartId:string){
        this.cartMap = this.cartService.getCart();

        for (let key in this.cartMap) {
            let value = this.cartMap[key];
            if (value.data.cartId == cartId) {
                return true;
            }
        }
        return false;
    }

    /**
    * Function to remove a cartId from the data cart.
    **/ 
    // removeCart(rowData:any, cartId: string){
    //     this.cartService.updateFileSpinnerStatus(true);
    //     this.cartService.removeCartId(cartId);
    //     rowData.isSelected = this.isInDataCart(cartId);
    //     this.checkIfAllSelected(this.files);

    //     setTimeout(()=> {
    //         this.cartService.updateFileSpinnerStatus(false);
    //     }, 3000);
    // }

    downloadById(id: any){
        let subFiles: any = null;
        for (let comp of this.files) {
            subFiles = this.searchTree(comp, id);
            if(subFiles != null){
                break;
            }
        }
        if(subFiles != null){
            this.downloadAllFilesFromAPI(subFiles);
            // subFiles.isSelected = true;
        }
    }

    downloadOneFile(rowData: any){
        let filename = decodeURI(rowData.downloadURL).replace(/^.*[\\\/]/, '');
        rowData.downloadStatus = 'downloading';
        rowData.downloadProgress = 0;

        const req = new HttpRequest('GET', rowData.downloadURL, {
            reportProgress: true, responseType: 'blob'
        });

        rowData.downloadInstance = this.http.request(req).subscribe(event => {
            switch (event.type) {
                case HttpEventType.Response:
                    this.downloadService.saveToFileSystem(event.body, filename);
                    rowData.downloadStatus = 'downloaded';
                    this.cartService.updateCartItemDownloadStatus(rowData.cartId,'downloaded');
                    this.downloadStatus = this.updateDownloadStatus(this.files)?"downloaded":null;
                    if(rowData.isSelected){
                        this.downloadService.setFileDownloadedFlag(true);
                    }
                    break;
                case HttpEventType.DownloadProgress:
                    rowData.downloadProgress = Math.round(100*event.loaded / event.total);
                    break;
            }
        })
    }
    /**
    * Function to download a single file based on download url.
    **/ 
    downloadFile(rowData:any){
        if(!this.isFile(rowData)){
            this.downloadById(rowData.cartId);
        }else{
            this.downloadOneFile(rowData);
        };

        rowData.downloadStatus = 'downloaded';
        if(rowData.isSelected){
            this.downloadService.setFileDownloadedFlag(true);
        }
        // this.cartService.updateFileSpinnerStatus(true);

        // this.downloadService.getFile(rowData.downloadURL, '').subscribe(blob => {
        //     this.downloadService.saveToFileSystem(blob, filename);
        //     rowData.downloadStatus = 'downloaded';
        //     this.cartService.updateCartItemDownloadStatus(rowData.cartId,'downloaded');
        //     this.cartService.updateFileSpinnerStatus(false);
        //     this.updateDownloadStatus(this.files);
        //     },
        //     error => console.log('Error downloading the file.')
        // )
    }

    /**
    * Function to cancel current download.
    **/ 
    cancelDownload(rowData:any){
        if(!this.isFile(rowData)){
            this.cancelDownloadAll();
            rowData.downloadProgress = 0;
            rowData.downloadStatus = null;
        }else{
            rowData.downloadInstance.unsubscribe();
            rowData.downloadInstance = null;
            rowData.downloadProgress = 0;
            rowData.downloadStatus = null;
        }
    }

    /**
    * Function to download all files based on download url.
    **/ 
    downloadAllFilesFromUrl(files:any){
        for (let comp of files) {
            if(comp.children.length > 0){
                this.downloadAllFilesFromUrl(comp.children);
            }else{
                if(comp.data.downloadURL){
                    this.downloadOneFile(comp.data);
                }
            }
        }   
    }

    /**
    * Function to confirm download all.
    **/ 
    downloadAllConfirm(header:string, massage:string, key:string) {
        this.confirmationService.confirm({
            message: massage,
            header: header,
            key: key,
            accept: () => {
                this.cancelAllDownload = false;
                this.downloadFromRoot();
            },
            reject: () => {
            }
        });
    }

    downloadFromRoot(){
        this.downloadAllFilesFromAPI(this.treeRoot[0]);
    }

    // getDownloadData(files: any){
    //     let existItem: any;
    //     for (let comp of files) {
    //         if(comp.children.length > 0){
    //             this.getDownloadData(comp.children);
    //         }else{
    //             if (comp.data['filePath'] != null && comp.data['filePath'] != undefined) {
    //                 if (comp.data['filePath'].split(".").length > 1) {
    //                     existItem = this.downloadData.filter(item => item.filePath === comp.data['ediid']+comp.data['filePath'] 
    //                         && item.downloadURL === comp.data['downloadURL']);
        
    //                     if (existItem.length == 0) {
    //                         this.downloadData.push({"filePath":comp.data['ediid']+comp.data['filePath'], 'downloadURL':comp.data['downloadURL']});
    //                     }
    //                 }
    //             }
    //         }
    //     }        
    // }


    /**
    * Function to download all files from API call.
    **/ 
    downloadAllFilesFromAPI(files: any){
        let postMessage: any[] = [];
        this.downloadData = [];
        this.zipData = [];
        this.displayDownloadFiles = true;
        this.cancelAllDownload = false;
        this.downloadStatus = 'downloading';
        this.downloadService.setDownloadProcessStatus(false, "landingPage");

        // Sending data to _bundle_plan and get back the plan
        this.downloadService.getDownloadData(files.children, this.downloadData);

        var randomnumber = Math.floor(Math.random() * (this.commonVarService.getRandomMaximum() - this.commonVarService.getRandomMinimum() + 1)) + this.commonVarService.getRandomMinimum();

        var zipFileBaseName = "download" + randomnumber;
        files.data.downloadFileName = zipFileBaseName + ".zip"
        files.data.downloadStatus = 'downloading';

        postMessage.push({"bundleName":files.data.downloadFileName, "includeFiles":this.downloadData});

        // now use postMessage to request a bundle plan
        this.downloadService.getBundlePlan(this.distApi + "_bundle_plan", JSON.stringify(postMessage)).subscribe(
            blob => {
                 this.processBundle(blob, zipFileBaseName, files);
            },
            err => {
                console.log(err);
                this.bundlePlanMessage = err;
                this.bundlePlanStatus = "error";
            }
        );

        // Once get bundle plan back, put it into a zipData array and send post request one by one
        // sample return data:
    }

    processBundle(res: any, zipFileBaseName, files: any){
        this.bundlePlanStatus = res.status.toLowerCase( );
        this.messageColor = this.getColor();
        this.bundlePlanUnhandledFiles = res.notIncluded;
        let bundlePlan: any[] = res.bundleNameFilePathUrl;
        let downloadUrl: any = this.distApi + res.postEach;
        this.bundlePlanMessage = res.messages;
        let tempData: any[] = [];

        console.log(this.bundlePlanUnhandledFiles);

        for(let bundle of bundlePlan){
            this.zipData.push({"fileName":bundle.bundleName, "downloadProgress": 0, "downloadStatus":null, "downloadInstance": null, "bundle": bundle, "downloadUrl": downloadUrl, "downloadErrorMessage":""});
        }

        // Associate zipData with files
        for(let zip of this.zipData){
            for(let includeFile of zip.bundle.includeFiles){
                let filePath = includeFile.filePath.substring(includeFile.filePath.indexOf('/'));
                let treeNode = this.downloadService.searchTreeByfilePath(this.treeRoot[0], filePath);
                if(treeNode != null){
                    treeNode.data.zipFile = zip.fileName;
                }
            }
        }

        this.downloadService.downloadNextZip(this.zipData, this.treeRoot[0], "landingPage");

        // Start downloading the first one, this will set the downloaded zip file to 1
        this.subscriptions.push(this.downloadService.watchDownloadingNumber("landingPage").subscribe(
            value => {
                if(!this.cancelAllDownload){
                    this.downloadService.downloadNextZip(this.zipData, this.treeRoot[0], "landingPage");
                    files.data.downloadProgress = Math.round(100*this.downloadService.getDownloadedNumber(this.zipData) / this.zipData.length);
                    // if(this.downloadService.allDownloadFinished(this.zipData)){
                    //     files.data.downloadStatus = 'downloaded';
                    //     this.downloadStatus = 'downloaded';
                    // }
                }

                this.downloadStatus = this.updateDownloadStatus(this.files)?"downloaded":null;
            }
        ));
    }

    // getDownloadedNumber(){
    //     let totalDownloadedZip: number = 0;
    //     for (let zip of this.zipData) {
    //         if(zip.downloadStatus == 'downloaded'){
    //             totalDownloadedZip += 1;
    //         }
    //     }
    //     return totalDownloadedZip;
    // }

    cancelDownloadZip(zip: any){
        zip.downloadInstance.unsubscribe();
        zip.downloadInstance = null;
        zip.downloadProgress = 0;
        zip.downloadStatus = "cancelled";
    }

    cancelDownloadAll(){
        for (let zip of this.zipData) {
            if(zip.downloadInstance != null){
                zip.downloadInstance.unsubscribe();
            }
            zip.downloadInstance = null;
            zip.downloadProgress = 0;
            zip.downloadStatus = null;
        }

        for(let sub of this.subscriptions){
            sub.unsubscribe();
        }

        this.downloadService.setDownloadingNumber(0, "landingPage");
        this.zipData = [];
        this.downloadStatus = null;
        this.cancelAllDownload = true;
        this.displayDownloadFiles = false;
        this.downloadService.resetZipName(this.treeRoot[0]);
        this.bundlePlanMessage = null;
        this.bundlePlanStatus = null;
        this.bundlePlanUnhandledFiles = null;
    }


    // resetZipName(element){
    //     if(element.data != undefined){
    //         element.data.zipFile = null;
    //     }
    //     if (element.children.length > 0){
    //         for(let i=0; i < element.children.length; i++){
    //             this.resetZipName(element.children[i]);
    //         }
    //     } 
    // }

    /**
    * Function to set the download status of all files to downloaded.
    **/ 
    setAllDownloaded(files:any){
        for (let comp of files) {
            if(comp.children.length > 0){
                this.setAllDownloaded(comp.children);
            }else{
                comp.data.downloadStatus = 'downloaded';
                this.cartService.updateCartItemDownloadStatus(comp.data.cartId,'downloaded');
                // this.cartService.updateFileSpinnerStatus(false);
            }
        }   
    }

    /**
    * Function to reset the download status of a file.
    **/ 
    resetDownloadStatus(rowData){
        rowData.downloadStatus = null;
        rowData.downloadProgress = 0;
        this.cartService.updateCartItemDownloadStatus(rowData.cartId,null);
        this.allDownloaded = false;
    }

    /**
    * Function to check if a node if leaf.
    **/ 
    isFile(rowData: any){
        return rowData.name.match(/\./g) == null? false : true; 
    }

    getColor(){
        if(this.bundlePlanStatus == 'warnings'){
            return "darkorange";
        }else if(this.bundlePlanStatus == 'error'){
            return "red";
        }else{
            return "black";
        }
    }
}
