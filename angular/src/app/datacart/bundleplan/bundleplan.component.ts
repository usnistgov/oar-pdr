import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { ZipData } from '../../shared/download-service/zipData';
import { TreeNode } from 'primeng/primeng';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { CommonFunctionService } from '../../shared/common-function/common-function.service';
import { OverlayPanel } from 'primeng/overlaypanel';
import { AppConfig } from '../../config/config';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { DownloadData } from '../../shared/download-service/downloadData';
import { CartService } from '../cart.service';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { DownloadConfirmComponent } from '../download-confirm/download-confirm.component';
import { ConfirmationDialogComponent } from '../../shared/confirmation-dialog/confirmation-dialog.component';
import { DataCart } from '../cart';
import { CartConstants } from '../cartconstants';
import { DataCartStatus } from '../cartstatus';

@Component({
  selector: 'app-bundleplan',
  templateUrl: './bundleplan.component.html',
  styleUrls: ['./bundleplan.component.css', '../datacart.component.css']
})
export class BundleplanComponent implements OnInit {
    dataCart: DataCart;
    public CART_CONSTANTS: any;
    dataCartStatus: DataCartStatus;

    //Bundle
    bundlePlanStatus: any;
    bundlePlanMessage: any[];
    unhandledFiles: any[];
    bundlePlanUnhandledFiles: any[] = null;
    bundleplan: any;
    bundlePlanRef: any;

    // Overall progress
    downloadSpeed = 0.00;
    overallStatus: string = null;
    downloadStartTime: any;
    downloadEndTime: any;
    totalDownloadTime: number;

    // Display
    showCurrentTask: boolean = false;
    currentTask: string = '';
    messageColor: string;
    showUnhandledFiles: boolean = true;
    showZipFiles: boolean = true;

    //Download
    downloadData: DownloadData[];
    allDownloadCancelled: boolean = false;
    subscriptions: any = [];
    downloadStarted: boolean = false;

    //Data
    selectedTreeRoot = [];
    minimum: number = 1;
    maximum: number = 100000;
    treeRoot = [];
    zipData: ZipData[] = [];

    // For pop up
    modalRef: any;

    emailSubject: string;
    emailBody: string;
    emailBodyBase: string = 'The information below describes an error that occurred while downloading data via the data cart. %0D%0A%0D%0A [From the PDR Team:  feel free to add additional information about the failure or your questions here. Thanks for sending this message!] %0D%0A%0D%0A';

    showMessage: boolean = true;
    distApi: string;

    problemZip: ZipData = {
        fileName: "",
        downloadProgress: 0,
        downloadStatus: null,
        downloadInstance: null,
        bundle: null,
        downloadUrl: null,
        downloadErrorMessage: '',
        bundleSize: 0,
        downloadTime: 0
    };

    @Input() inBrowser: boolean;
    @Input() dataFiles: TreeNode[] = [];
    @Input() selectedData: TreeNode[];
    @Input() ediid: string;
    @Output() outputZipData = new EventEmitter<ZipData[]>();

    constructor(
        private downloadService: DownloadService,
        public commonFunctionService: CommonFunctionService,
        private cfg: AppConfig,
        public gaService: GoogleAnalyticsService,
        public cartService: CartService,
        private modalService: NgbModal
    ) { 
        this.CART_CONSTANTS = CartConstants.cartConst;

        this.cartService._watchRemoteCommand((command) => {
            switch(command.command) { 
                case 'downloadSelected': { 
                    if(command.data)
                        this.selectedData = command.data;
                   this.downloadAllFilesFromAPI();
                   break; 
                } 
                case 'resetDownloadParams': {
                    this.resetDownloadParams();
                    break;
                }
                default: { 
                   //statements; 
                   break; 
                } 
             } 
        });
    }

    ngOnInit() {
        if(this.inBrowser){
            this.dataCartStatus = DataCartStatus.openCartStatus();

            if (this.ediid != this.CART_CONSTANTS.GLOBAL_CART_NAME) {
                this.dataCart = DataCart.openCart(this.ediid);
            }else{
                this.dataCart = DataCart.openCart(this.CART_CONSTANTS.GLOBAL_CART_NAME);
            }
        }
        
        this.distApi = this.cfg.get("distService", "/od/ds/");

        this.downloadService.watchDownloadProcessStatus().subscribe(
            value => {
                if(value && this.downloadStarted)
                {
                    this.downloadEndTime = new Date();
                    this.totalDownloadTime = this.downloadEndTime.getTime() / 1000 - this.downloadStartTime.getTime() / 1000;
                    this.overallStatus = 'complete';
                    setTimeout(() => {
                        this.dataCartStatus.updateDownloadPercentage(this.ediid, 100);
                    }, 1000);
                }
            }
        );

        // create root
        const newPart = {
            data: {
                resTitle: "root"
            }, 
            children: this.dataFiles
        };

        this.treeRoot.push(newPart);
    }

    getDownloadStatusColor(downloadStatus: string){
        return this.cartService.getDownloadStatusColor(downloadStatus);
    }

    getIconClass(downloadStatus: string){
        return this.cartService.getIconClass(downloadStatus);
    }

    getStatusForDisplay(downloadStatus: string){
        return this.cartService.getStatusForDisplay(downloadStatus);
    }

    /**
     * Return download time in HH:MM:SS format
     * @param downloadTime - download time in seconds 
     */
    getDownloadTime(downloadTime)
    {
        if(!downloadTime) return "Calculating...";

        let hours = Math.floor(downloadTime / 3600);
        let minutes = Math.floor((downloadTime - hours * 3600)/60);
        let seconds = Math.floor(downloadTime - hours * 3600 - minutes * 60);

        let returnFormat: string = ""; 
        if(seconds > 0) returnFormat = seconds + "sec";
        if(minutes > 0) returnFormat = minutes + "min " + returnFormat;
        if(hours > 0) returnFormat = hours + "hour " + returnFormat;

        return returnFormat.trim();
    }

    /**
     * Cancel download
     * @param zip Current zip to be cancelled
     */
    cancelDownloadZip(zip: ZipData){
        this.downloadService.cancelDownloadZip(zip, this.dataFiles, this.dataCart);
    }

    /*
    * Display zip file error message
    */
    openZipDetails(event, overlaypanel: OverlayPanel, zip: ZipData = null ) {
        this.problemZip = zip;
        this.emailSubject = 'PDR: Error downloading zip file';

        overlaypanel.toggle(event);
    }

    /**
     * Construct email body for error reporting
     */
    getEmailBody() {
        let dateTime = new Date();
        let emaibody = this.emailBody;
        if(!emaibody)
        {
            emaibody = this.emailBodyBase + 'Time: ' + dateTime.toString();
        }

        emaibody += '%0D%0A%0D%0A details:';

        for (let zip of this.zipData) 
        {
            if(zip.downloadStatus == 'error')
            {
                emaibody += '%0D%0A%0D%0A'+ zip.fileName 
                         + ':%0D%0A download URL: ' + zip.downloadUrl
                         + ':%0D%0A error message: ' + zip.downloadErrorMessage
                         + ':%0D%0A details: ' + JSON.stringify(zip.bundle);
            }
        }

        return emaibody;
    }

    /**
     * Make sure the width of popup dialog is less than 500px or 80% of the window width
     */
    getDialogWidth() {
        var w = window.innerWidth > 500 ? 500 : window.innerWidth;
        return w + 'px';
    }

    /**
     * Return row background color
     * @param i - row number
     */
    getBackColor(i: number) {
        if (i % 2 != 0) return 'rgb(231, 231, 231)';
        else return 'white';
    }

    /**
     * Download one particular zip
     */
    downloadOneZip(zip: ZipData) {
        if (zip.downloadInstance != null) {
            zip.downloadInstance.unsubscribe();
        }
        this.downloadService.increaseTotalBundleBySize(zip.bundleSize);
        this.downloadService.download(zip, this.zipData, this.dataFiles, this.dataCart);
    }

    /**
     * Function to download all files from API call.
     **/
    downloadAllFilesFromAPI() {
        this.gaService.gaTrackEvent('download', undefined, 'all files', "Data cart");
        this.clearDownloadStatus();
        this.showCurrentTask = true;
        let postMessage: any[] = [];
        this.downloadData = [];
        this.zipData = [];
        this.allDownloadCancelled = false;
        this.bundlePlanMessage = null;
        // this.downloadStatus = 'downloading';
        this.downloadService.setDownloadProcessStatus(false);
        this.currentTask = "Preparing downloads...";
        this.downloadService.setDownloadingNumber(0);

        this.downloadStartTime = new Date();

        // create root
        const newPart = {
            data: {
                resTitle: "root"
            }, children: []
        };
        newPart.children = this.selectedData;
        this.selectedTreeRoot.push(newPart);

        let files = this.selectedTreeRoot[0];
        // Sending data to _bundle_plan and get back the plan
        this.downloadService.getDownloadData(this.selectedData, this.downloadData);
        var randomnumber = Math.floor(Math.random() * (this.maximum - this.minimum + 1)) + this.minimum;

        var zipFileBaseName = "download" + randomnumber;
        files.data.downloadFileName = zipFileBaseName;
        files.data.downloadStatus = 'downloading';

        postMessage.push({ "bundleName": files.data.downloadFileName, "includeFiles": this.downloadData });
        console.log('Bundle plan post message:', JSON.stringify(postMessage[0]));
        console.log("Calling following end point to get bundle plan:", this.distApi + "_bundle_plan");

        this.bundlePlanRef = this.downloadService.getBundlePlan(this.distApi + "_bundle_plan", JSON.stringify(postMessage[0])).subscribe(
            blob => {
                this.bundlePlanStatus = blob.status.toLowerCase();
                this.bundlePlanMessage = blob.messages;
                this.bundlePlanUnhandledFiles = blob.notIncluded;
                this.messageColor = this.getColor();

                if (this.bundlePlanUnhandledFiles) {
                    this.markUnhandledFiles();
                }

                if (this.bundlePlanStatus == 'complete' || this.bundlePlanStatus == 'warnings') {
                    if(this.bundlePlanStatus == 'warnings')
                    {
                        let dateTime = new Date();

                        this.showUnhandledFiles = false;
                        this.emailSubject = 'PDR: Error getting download plan';
                        this.emailBody = this.emailBodyBase
                            + 'URL:' + this.distApi + '_bundle_plan; ' + '%0D%0A'
                            + 'Time: ' + dateTime.toString() + '%0D%0A%0D%0A'
                            + 'Post message:%0D%0A' + JSON.stringify(postMessage[0]) + ';' + '%0D%0A%0D%0A' + 'Return message:%0D%0A' + JSON.stringify(blob);
                    }

                    this.bundleplan = blob;
                    this.downloadService.setTotalBundleSize(blob.size);

                    let bundlePlan: any[] = blob.bundleNameFilePathUrl;
                    let downloadUrl: any = this.distApi + blob.postEachTo;

                    for (let bundle of bundlePlan) {
                        this.zipData.push({ "fileName": bundle.bundleName, "downloadProgress": 0, "downloadStatus": null, "downloadInstance": null, "bundle": bundle, "downloadUrl": downloadUrl, "downloadErrorMessage": "","bundleSize": bundle.bundleSize, 'downloadTime': null });
                    }

                    this.outputZipData.emit(this.zipData);
            
                    // Associate zipData with files
                    for (let zip of this.zipData) {
                        for (let includeFile of zip.bundle.includeFiles) {
                            let resFilePath = includeFile.filePath.substring(includeFile.filePath.indexOf('/'));
                            for (let dataFile of this.dataFiles) {
                                let treeNode = this.downloadService.searchTreeByfilePath(dataFile, resFilePath);
                                if (treeNode != null) {
                                    treeNode.data.zipFile = zip.fileName;
                                    break;
                                }
                            }
            
                            this.downloadService.setDownloadStatus(zip, this.dataFiles, 'pending', this.dataCart);
                        }
                    }

                    let ngbModalOptions: NgbModalOptions = {
                        backdrop: 'static',
                        keyboard: false,
                        windowClass: "myCustomModalClass",
                        size: 'lg'
                    };

                    this.modalRef = this.modalService.open(DownloadConfirmComponent, ngbModalOptions);
                    this.modalRef.componentInstance.bundle_plan_size = blob.size;
                    this.modalRef.componentInstance.zipData = this.zipData;
                    this.modalRef.componentInstance.totalFiles = blob.filesCount;
                    this.modalRef.componentInstance.returnValue.subscribe((returnValue) => {
                        if ( returnValue ) {
                            this.showCurrentTask = false;
                            this.downloadStarted = true;
                            this.processBundle(this.bundleplan);
                        }else{
                            this.showCurrentTask = false;
                            this.cancelDownloadAll()
                            console.log("User canceled download");
                        }
                    }, (reason) => {
                        this.showCurrentTask = false;
                        this.cancelDownloadAll()
                    });
                }
                else // error
                {
                    let dateTime = new Date();
                    this.emailSubject = 'PDR: Error getting download plan';
                    this.emailBody = this.emailBodyBase
                        + 'URL:' + this.distApi + '_bundle_plan; ' + '%0D%0A'
                        + 'Time: ' + dateTime.toString() + '%0D%0A%0D%0A'
                        + 'Post message:%0D%0A' + JSON.stringify(postMessage[0]) + ';' + '%0D%0A%0D%0A' + 'Return message:%0D%0A' + JSON.stringify(blob);
                    this.showUnhandledFiles = false;
                    this.showCurrentTask = false;
                    this.unsubscribeBundleplan();
                }
            },
            err => {
                let dateTime = new Date()
                console.log("Calling following end point returned error:");
                console.log(this.distApi + "_bundle_plan");
                console.log("Post message:", JSON.stringify(postMessage[0]));
                console.log("Error message:", err);
                this.bundlePlanMessage = err;
                this.bundlePlanStatus = "internal error";
                this.showCurrentTask = false;
                this.messageColor = this.getColor();
                this.emailSubject = 'PDR: Error getting download plan';
                this.emailBody =
                    'The information below describes an error that occurred while downloading data via the data cart.' + '%0D%0A%0D%0A'
                    + '[From the PDR Team:  feel free to add additional information about the failure or your questions here.  Thanks for sending this message!]' + '%0D%0A%0D%0A'
                    + 'URL:' + this.distApi + '%0D%0A'
                    + 'Time: ' + dateTime.toString() + '%0D%0A%0D%0A'
                    + '_bundle_plan; ' + '%0D%0A%0D%0A'
                    + 'Post message:%0D%0A' + JSON.stringify(postMessage[0]) + '%0D%0A%0D%0A'
                    + 'Error message:%0D%0A' + JSON.stringify(err);
                console.log("emailBody:", this.emailBody);
            }
        );
    }

    /**
     * Unsubscribe Bundleplan request
     */
    unsubscribeBundleplan() {
        this.bundlePlanRef.unsubscribe();
        this.bundlePlanRef = null;
    }

    /**
    * Process data returned from bundle_plan
    **/
    processBundle(res: any) {
        this.currentTask = "Processing Each Bundle...";
        this.messageColor = this.getColor();

        this.downloadService.downloadNextZip(this.zipData, this.dataFiles, this.dataCart);

        // Start downloading the first one, this will set the downloaded zip file to 1
        this.subscriptions.push(this.downloadService.watchDownloadingNumber().subscribe(
            value => {
                if (value >= 0) {
                    if (!this.allDownloadCancelled) {
                        this.overallStatus = "downloading";
                        this.downloadService.downloadNextZip(this.zipData, this.dataFiles, this.dataCart);
                    }
                    else
                    {
                        this.overallStatus = "Cancelled";
                        setTimeout(() => {
                            this.dataCartStatus.updateDownloadPercentage(this.ediid, 0);
                        }, 1000);
                    }
                }
            }
        ));
    }

    get overallProgress(){
        let returnValue = 0;
        if(this.downloadService.totalBundleSize > 0 && this.downloadService.totalBundleSize >= this.downloadService.totalDownloaded)
            returnValue = Math.round(100 * this.downloadService.totalDownloaded / this.downloadService.totalBundleSize);
        else if(this.downloadService.totalBundleSize > 0)
            returnValue = 100;
        else    
            returnValue = 0;

        this.dataCartStatus.updateDownloadPercentage(this.ediid, returnValue)
        return returnValue;
    }

    /**
    * Reset download params
    **/
    resetDownloadParams() {
        this.zipData = [];
        this.downloadService.setDownloadingNumber(-1);
        this.allDownloadCancelled = true;
        this.downloadService.resetZipName(this.treeRoot[0]);
        this.bundlePlanMessage = null;
        this.bundlePlanStatus = null;
        this.bundlePlanUnhandledFiles = null;
    }

    /**
     * clears all download status
     **/
    clearDownloadStatus() {
        this.resetDownloadParams();
        this.cartService.resetDatafileDownloadStatus(this.dataFiles, this.dataCart, '');
        this.downloadService.setTotalFileDownloaded(0);
        this.downloadService.resetDownloadData();
    }

    /**
     * Set color for bundle plan return message 
     */
    getColor() {
        if (this.bundlePlanStatus == 'warnings') {
            return "darkorange";
        } else if (this.bundlePlanStatus == 'error' || this.bundlePlanStatus == 'internal error') {
            return "red";
        } else {
            return "black";
        }
    }

    /**
     * 
     */
    markUnhandledFiles() {
        this.dataCart.restore();

        for (let unhandledFile of this.bundlePlanUnhandledFiles) {
            let resFilePath = unhandledFile.filePath.substring(unhandledFile.filePath.indexOf('/'));
            for (let dataFile of this.dataFiles) {
                let node = this.downloadService.searchTreeByfilePath(dataFile, resFilePath);
                if (node != null) {
                    node.data.downloadStatus = 'failed';
                    node.data.filePath = unhandledFile.filePath;
                    node.data.downloadUrl = unhandledFile.downloadUrl;
                    node.data.message = unhandledFile.message;
                    // this.cartService.updateCartItemDownloadStatus(node.data['cartId'], 'failed');
                    let cartItem = this.dataCart.findFile(node.data.resId, node.data.filePath);
                    if(cartItem) cartItem.downloadStatus = 'failed';

                    break;
                }
            }
        }

        this.dataCart.save();
    }

    /**
     * Cancel all downloads confirmation
     */
    cancelDownloadAllConfirmation()
    {
        var message = 'This will cancel all current and pending download process.';

        this.modalRef = this.modalService.open(ConfirmationDialogComponent);
        this.modalRef.componentInstance.title = 'Please confirm';
        this.modalRef.componentInstance.btnOkText = 'Yes';
        this.modalRef.componentInstance.btnCancelText = 'No';
        this.modalRef.componentInstance.message = message;
        this.modalRef.componentInstance.showWarningIcon = true;
        this.modalRef.componentInstance.showCancelButton = true;

        this.modalRef.result.then((result) => {
            if ( result ) {
                this.cancelDownloadAll();
            }else{
                console.log("User changed mind.");
            }
        }, (reason) => {
        });
    }

    /**
     * Cancell all download instances
     **/
    cancelDownloadAll() {
        for (let zip of this.zipData) {
            if (zip.downloadInstance != null) {
                zip.downloadInstance.unsubscribe();
            }
            zip.downloadInstance = null;
            zip.downloadProgress = 0;
            zip.downloadStatus = null;
        }

        for (let sub of this.subscriptions) {
            sub.unsubscribe();
        }

        this.resetDownloadParams();
        this.clearDownloadingStatus();
        this.showCurrentTask = false;
        this.overallStatus = "cancelled";
        this.downloadService.resetDownloadData();
        setTimeout(() => {
            this.dataCartStatus.updateDownloadPercentage(this.ediid, 0)
        }, 1000);
    }

    /**
     * Clear "downloading" and "pending" status of given tree node
     **/
    clearDownloadingStatus() {
        for (let dataFile of this.dataFiles) {
            this.clearTreeByDownloadStatus(dataFile);
        }
    }

    clearTreeByDownloadStatus(element) {
        if (element.data.isLeaf && (element.data.downloadStatus == 'downloading' || element.data.downloadStatus == 'pending')) {
            element.data.downloadStatus = null;
            element.data.zipFile = null;

            this.dataCart.setDownloadStatus(element.data.resId, element.data.filePath, '');
        }

        for (let i = 0; i < element.children.length; i++) {
            this.clearTreeByDownloadStatus(element.children[i]);
        }
    }
}
