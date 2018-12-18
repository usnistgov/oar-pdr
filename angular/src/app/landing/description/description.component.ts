import { Component, Input,ChangeDetectorRef } from '@angular/core';
import { TreeNode} from 'primeng/api';
import { CartService} from '../../datacart/cart.service';
import { Data} from '../../datacart/data';
import { OverlayPanel} from 'primeng/overlaypanel';
import { stringify } from '@angular/compiler/src/util';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { SelectItem, DropdownModule, ConfirmationService,Message } from 'primeng/primeng';
import { DownloadData } from '../../datacart/downloadData';
import { ZipData } from '../../shared/download-service/zipData';
import { CommonVarService } from '../../shared/common-var';
import { environment } from '../../../environments/environment';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse, HttpEvent } from '@angular/common/http'; 


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
    showZipFiles: boolean = false;

    private distApi : string = environment.DISTAPI;

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
        this.updateDownloadStatusFromCart();

        this.updateCartStatus(this.files);
        this.updateDownloadStatus(this.files);
        this.ediid = this.commonVarService.getEdiid();

        this.totalFiles = 0;
        this.getTotalFiles(this.files);

        this.expandAll(this.files, true);

        const newPart = {
            data : {
              id: 0,
              name : "files",
              mediatype: "",
              size: null,
              downloadURL: null,
              description: null,
              filetype: null,
              resId: "files",
              fullPath: "/",
              isSelected: false,
              downloadProgress: 0,
              downloadInstance: null,
              zipFile: null
            },children: []
          };
          newPart.children = this.files;
          this.treeRoot.push(newPart);
    }

    expandAll(dataFiles: any, option: boolean){
        for ( let i=0; i < dataFiles.length;i++) {
            dataFiles[i].expanded = option;
            if(dataFiles[i].children.length > 0){
                this.expandAll(dataFiles[i].children, option);
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
    updateDownloadStatusFromCart(){
        for (let key in this.cartMap) {
            let value = this.cartMap[key];
            if(value.data.downloadStatus != undefined){
                this.setFilesDownloadStatus(this.files, value.data.resId, value.data.downloadStatus);
            }
        }
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
    setFilesDownloadStatus(files, resId, downloadStatus){
        for (let comp of files) {
            if(comp.children.length > 0){
                this.setFilesDownloadStatus(comp.children, resId, downloadStatus);
            }else{
                if(comp.data.resId == resId){
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

    updateCartStatus(files: any){
        for (let comp of files) {
            if(comp.children.length > 0){
                this.updateCartStatus(comp.children);
            }else{
                comp.data.isSelected = this.isInDataCart(comp.data.resId);
            }
        }   
        this.updateAllSelectStatus(this.files);     
    }

    addSubFilesToCart(rowData: any) {
        let data: Data;
        let compValue: any;
        this.cartService.updateAllFilesSpinnerStatus(true);

        if(!this.isFile(rowData)){
            let subFiles: any = null;
            for (let comp of this.files) {
                subFiles = this.searchTree(comp, rowData.id);
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
        console.log("this.allSelected:");
        console.log(this.allSelected);

        setTimeout(() => {
            this.cartService.updateAllFilesSpinnerStatus(false);
        }, 3000);
        setTimeout(() => {
            this.addFileStatus = true;
        }, 3000);
    }

    searchTree(element, id){
        if(element.data.id == id){
             return element;
        }else if (element.children.length > 0){
             var i;
             var result = null;
             for(i=0; result == null && i < element.children.length; i++){
                  result = this.searchTree(element.children[i], id);
             }
             return result;
        }
        return null;
   }

   addAllFilesToCart(){
       this.addFilesToCart(this.files);
       this.allSelected = true;
       this.updateAllSelectStatus(this.files);
       console.log("this.allSelected:");
       console.log(this.allSelected);
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

        setTimeout(() => {
            this.cartService.updateAllFilesSpinnerStatus(false);
        }, 3000);
        setTimeout(() => {
            this.addFileStatus = true;
        }, 3000);
    }

    removeFromNode(rowData:any){
        this.removeCart(rowData);
        this.allSelected = true;
        this.updateAllSelectStatus(this.files);
    }

    removeCart(rowData:any){
        if(!this.isFile(rowData)){
            let subFiles: any = null;
            for (let comp of this.files) {
                subFiles = this.searchTree(comp, rowData.id);
                if(subFiles != null){
                    break;
                }
            }
            if(subFiles != null){
                this.removeFilesFromCart(subFiles.children);
                rowData.isSelected = false; 
            }
        }else{
            this.cartService.removeResId(rowData.resId);
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
                this.cartService.removeResId(comp.data.resId);
                comp.data.isSelected = false;
            }
        }
        
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
                'downloadURL':rowData.downloadURL,
                'fileFormat':rowData.mediatype,
                'downloadStatus': null };

        this.cartService.addDataToCart(data);
        rowData.isSelected = this.isInDataCart(rowData.resId);

        setTimeout(()=> {
            this.cartService.updateFileSpinnerStatus(false);
        }, 3000);
    }

    updateAllSelectStatus(files: any){
        var allSelected = true;
        for (let comp of files) {
            if(comp.children.length > 0){
                comp.data.isSelected = this.updateAllSelectStatus(comp.children);
                // console.log("comp.data.isSelected:");
                // console.log(comp.data.isSelected);
            }else{
                if(!comp.data.isSelected){
                    this.allSelected = false;
                    allSelected = false;
                }
            }
        }   

        // console.log("Returning:");
        // console.log(allSelected);

        return allSelected;
    }

    updateDownloadStatus(files: any){
        this.allDownloaded = true;
        for (let comp of files) {
            if(comp.children.length > 0){
                this.updateDownloadStatus(comp.children);
            }else{
                if(comp.data.downloadStatus != 'downloaded'){
                    this.allDownloaded = false;
                }
            }
        }   
    }

    /**
    * Function to check if resId is in the data cart.
    **/ 
    isInDataCart(resId:string){
        this.cartMap = this.cartService.getCart();

        for (let key in this.cartMap) {
            let value = this.cartMap[key];
            if (value.data.resId == resId) {
                return true;
            }
        }
        return false;
    }

    /**
    * Function to remove a resId from the data cart.
    **/ 
    // removeCart(rowData:any, resId: string){
    //     this.cartService.updateFileSpinnerStatus(true);
    //     this.cartService.removeResId(resId);
    //     rowData.isSelected = this.isInDataCart(resId);
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
                    this.cartService.updateCartItemDownloadStatus(rowData.resId,'downloaded');
                    this.updateDownloadStatus(this.files);
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
            this.downloadById(rowData.id);
        }else{
            this.downloadOneFile(rowData);
        };

        rowData.downloadStatus = 'downloaded';
        // this.cartService.updateFileSpinnerStatus(true);

        // this.downloadService.getFile(rowData.downloadURL, '').subscribe(blob => {
        //     this.downloadService.saveToFileSystem(blob, filename);
        //     rowData.downloadStatus = 'downloaded';
        //     this.cartService.updateCartItemDownloadStatus(rowData.resId,'downloaded');
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
                this.downloadFromRoot();
            },
            reject: () => {
            }
        });
    }

    downloadFromRoot(){
        // const tree = [];
          this.downloadAllFilesFromAPI(this.treeRoot[0]);
    }

    getDownloadData(files: any){
        let existItem: any;
        for (let comp of files) {
            if(comp.children.length > 0){
                this.getDownloadData(comp.children);
            }else{
                if (comp.data['fullPath'] != null && comp.data['fullPath'] != undefined) {
                    if (comp.data['fullPath'].split(".").length > 1) {
                        existItem = this.downloadData.filter(item => item.filePath === this.ediid+comp.data['fullPath'] 
                            && item.downloadURL === comp.data['downloadURL']);
        
                        if (existItem.length == 0) {
                            this.downloadData.push({"filePath":this.ediid+comp.data['fullPath'], 'downloadURL':comp.data['downloadURL']});
                        }
                    }
                }
            }
        }        
    }

    searchTreeByFullPath(element, fullPath){
        if(element.data.fullPath == fullPath){
             return element;
        }else if (element.children.length > 0){
             var i;
             var result = null;
             for(i=0; result == null && i < element.children.length; i++){
                  result = this.searchTreeByFullPath(element.children[i], fullPath);
             }
             return result;
        }
        return null;
   }

   resetZipName(element){
        if(element.data != undefined){
            element.data.zipFile = null;
        }
        if (element.children.length > 0){
            this.resetZipName(element.children);
        } 
    }

    /**
    * Function to download all files from API call.
    **/ 
    downloadAllFilesFromAPI(files: any){
        let existItem: any;
        let postMessage: any[] = [];
        this.downloadData = [];
        this.zipData = null;
        this.zipData = [];
        this.displayDownloadFiles = true;
        this.cancelAllDownload = false;

        console.log("Downloading from: ");
        console.log(files);

        // Sending data to _bundle_plan and get back the plan
        this.getDownloadData(files.children);
        console.log("downloadData:");
        console.log(this.downloadData);

        var randomnumber = Math.floor(Math.random() * (this.commonVarService.getRandomMaximum() - this.commonVarService.getRandomMinimum() + 1)) + this.commonVarService.getRandomMinimum();

        files.data.downloadFileName = "download" + randomnumber + ".zip";
        files.data.downloadStatus = 'downloading';

        postMessage.push({"bundleName":files.data.downloadFileName, "includeFiles":this.downloadData});

        console.log("postMessage:");
        console.log(postMessage);

        // now use postMessage to request a bundle plan

        // this.downloadService.postFile(this.distApi + "_bundle", JSON.stringify(postMessage)).subscribe(blob => {
        //     this.downloadService.saveToFileSystem(blob, this.downloadFileName);
        //     console.log('All downloaded.');
        //     this.downloadStatus = 'downloaded';
        //     this.setAllDownloaded(this.files);
        //     this.allDownloaded = true;
        // });

        // Once get bundle plan back, put it into a zipData array and send post request one by one
        // sample return data:

        let bundlePlan: any[] = [];
        let tempData: any[] = [];
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/aluminum/srd13_Al-002.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-002.json"});
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/aluminum/srd13_Al-003.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-003.json"});

        bundlePlan.push({"bundleName":"download4281_01.zip","includeFiles":tempData});

        tempData = [];
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/aluminum/srd13_Al-004.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-004.json"});
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/aluminum/srd13_Al-005.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-005.json"});

        bundlePlan.push({"bundleName":"download4281_02.zip","includeFiles":tempData});

        tempData = [];
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/chloride/srd13_Al-014.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-014.json"});
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/chloride/srd13_Al-015.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-015.json"});

        bundlePlan.push({"bundleName":"download4281_03.zip","includeFiles":tempData});

        tempData = [];
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/chloride/srd13_Al-016.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-016.json"});
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/chloride/srd13_Al-017.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-017.json"});

        bundlePlan.push({"bundleName":"download4281_04.zip","includeFiles":tempData});

        tempData = [];
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/chloride/srd13_Al-018.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-018.json"});
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/chloride/srd13_Al-019.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-019.json"});

        bundlePlan.push({"bundleName":"download4281_05.zip","includeFiles":tempData});

        tempData = [];
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/chloride/srd13_Al-020.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-020.json"});
        tempData.push({filePath: "ECBCC1C1301D2ED9E04306570681B10735/aluminum/chloride/srd13_Al-021.json", downloadURL: "http://www.nist.gov/srd/srd_data/srd13_Al-021.json"});

        bundlePlan.push({"bundleName":"download4281_06.zip","includeFiles":tempData}); 

        let tempUrl: any[] = ["https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip", "https://s3.amazonaws.com/nist-midas/1858/RawCameraData.zip","https://s3.amazonaws.com/nist-midas/1858/RawCameraData.zip"];
        var i = 0;

        for(let bundle of bundlePlan){
            this.zipData.push({"fileName":bundle.bundleName, "downloadProgress": 0, "downloadStatus":null, "downloadInstance": null, "bundle": bundle, "downloadUrl": tempUrl[i]});
            i++;
        }

        // Associate zipData with files
        for(let zip of this.zipData){
            for(let includeFile of zip.bundle.includeFiles){
                let fullPath = includeFile.filePath.substring(includeFile.filePath.indexOf('/'));
                let treeNode = this.searchTreeByFullPath(this.treeRoot[0], fullPath);
                if(treeNode != null){
                    treeNode.data.zipFile = zip.fileName;
                }
            }
        }

        console.log("this.files:");
        console.log(this.files);

        // Start downloading the first one, this will set the downloaded zip file to 1
        this.downloadService.watchDownloadingNumber().subscribe(value => {
            if(!this.cancelAllDownload){
                this.downloadService.downloadNextZip(this.zipData);
                files.data.downloadProgress = Math.round(100*this.getDownloadedNumber() / this.zipData.length);
                if(this.downloadService.allDownloaded(this.zipData)){
                    files.data.downloadStatus = 'downloaded';
                    this.downloadStatus = 'downloaded';
                }
            }
        });
    }

    getDownloadedNumber(){
        let totalDownloadedZip: number = 0;
        for (let zip of this.zipData) {
            if(zip.downloadStatus == 'downloaded'){
                totalDownloadedZip += 1;
            }
        }
        return totalDownloadedZip;
    }

    cancelDownloadZip(zip: any){
        zip.downloadInstance.unsubscribe();
        zip.downloadInstance = null;
        zip.downloadProgress = 0;
        zip.downloadStatus = null;
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
        this.downloadStatus = null;
        this.cancelAllDownload = true;
        this.displayDownloadFiles = false;
        this.resetZipName(this.treeRoot[0]);
    }

    /**
    * Function to set the download status of all files to downloaded.
    **/ 
    setAllDownloaded(files:any){
        for (let comp of files) {
            if(comp.children.length > 0){
                this.setAllDownloaded(comp.children);
            }else{
                comp.data.downloadStatus = 'downloaded';
                this.cartService.updateCartItemDownloadStatus(comp.data.resId,'downloaded');
                this.cartService.updateFileSpinnerStatus(false);
            }
        }   
    }

    /**
    * Function to reset the download status of a file.
    **/ 
    resetDownloadStatus(rowData){
        rowData.downloadStatus = null;
        rowData.downloadProgress = 0;
        this.cartService.updateCartItemDownloadStatus(rowData.resId,null);
        this.allDownloaded = false;
    }

    /**
    * Function to check if a node if leaf.
    **/ 
    isFile(rowData: any){
        return rowData.name.match(/\./g) == null? false : true; 
    }
}
