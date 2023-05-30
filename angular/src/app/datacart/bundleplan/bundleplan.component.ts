import { Component, OnInit, Input, Output, Inject, PLATFORM_ID, EventEmitter, SimpleChanges } from '@angular/core';
import { ZipData } from '../../shared/download-service/zipData';
import { TreeNode } from 'primeng/api';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { formatBytes } from '../../utils';
import { OverlayPanel } from 'primeng/overlaypanel';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { DownloadData } from '../../shared/download-service/downloadData';
import { CartService } from '../cart.service';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { DownloadConfirmComponent } from '../download-confirm/download-confirm.component';
import { ConfirmationDialogComponent } from '../../shared/confirmation-dialog/confirmation-dialog.component';
import { DataCart, DataCartItem } from '../cart';
import { DisplayPrefs } from '../displayprefs';
import { CartConstants, DownloadStatus } from '../cartconstants';
import { DataCartStatus } from '../cartstatus';
import { isPlatformBrowser } from '@angular/common';

class BundlePlanStatus {
    static readonly COMPLETED : string = "complete";
    static readonly WARNINGS  : string = "warnings";
    static readonly ERROR     : string = "error";
    static readonly INTERNAL_ERROR : string = "internal error";
}

@Component({
  selector: 'app-bundleplan',
  templateUrl: './bundleplan.component.html',
  styleUrls: ['./bundleplan.component.css', '../datacart.component.css']
})
export class BundleplanComponent implements OnInit {
    dataCart: DataCart;
    public CART_CONSTANTS: any;
    dataCartStatus: DataCartStatus;
    inBrowser: boolean = false;

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
    downloadFiles : DataCartItem[] = [];  // the files currently being downloaded
    allDownloadCancelled: boolean = false;
    subscriptions: any = [];
    downloadStarted: boolean = false;

    //Data
    zipData: ZipData[] = [];

    // For pop up
    modalRef: any;

    emailSubject: string;
    emailBody: string;
    emailBodyBase: string = 'The information below describes an error that occurred while downloading data via the data cart. %0D%0A%0D%0A [From the PDR Team:  feel free to add additional information about the failure or your questions here. Thanks for sending this message!] %0D%0A%0D%0A';

    showMessage: boolean = true;

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

    @Input() cartName: string;
    @Output() outputOverallStatus = new EventEmitter<string>();

    constructor(
        private downloadService: DownloadService,
        public gaService: GoogleAnalyticsService,
        public cartService: CartService,
        private modalService: NgbModal,
        @Inject(PLATFORM_ID) private platformId: Object
    ) { 
        this.inBrowser = isPlatformBrowser(platformId);
    }

    ngOnInit() {
        this.cartInit();

        this.downloadService.watchDownloadProcessStatus().subscribe(
            value => {
                if(value && this.downloadStarted && this.inBrowser){
                    this.setProcessComplete();
                }
            }
        );
    }

    ngOnChanges(changes: SimpleChanges): void {
        //Called before any other lifecycle hook. Use it to inject dependencies, but avoid any serious work here.
        //Add '${implements OnChanges}' to the class.
        if (changes.cartName) {
            this.cartInit();
        }
    }

    cartInit() {
        if(this.inBrowser) {
            this.dataCartStatus = DataCartStatus.openCartStatus();

            this.dataCart = this.cartService.getCart(this.cartName);
            // watch this cart?
        }
    }

    /**
     * Set the overall status to complete
     */
    setProcessComplete(){
        this.downloadEndTime = new Date();
        this.totalDownloadTime = this.downloadEndTime.getTime() / 1000 - this.downloadStartTime.getTime() / 1000;
        this.overallStatus = DownloadStatus.COMPLETED
        this.outputOverallStatus.emit(this.overallStatus);

        if (this.dataCart && this.downloadFiles) {
            let title = (this.dataCart.isGlobalCart()) ? "Global Data Cart"
                                                       : this.downloadFiles[0].resTitle? this.downloadFiles[0].resTitle.substring(0,20)+"..." : "No title...";
            this.dataCartStatus.setDownloadCompleted(this.dataCart.getName(), title);
        }

        setTimeout(() => {
            this.updateDownloadPercentage(100);
        }, 1000);
    }

    /**
     * Return font color based on input download status
     * @param downloadStatus 
     */
    getDownloadStatusColor(downloadStatus: string){
        return DisplayPrefs.getDownloadStatusColor(downloadStatus);
    }

    /**
     * Reture icon class based on input download status
     * @param downloadStatus 
     */
    getIconClass(downloadStatus: string){
        return DisplayPrefs.getDownloadStatusIcon(downloadStatus);
    }

    /**
     * Return status string for display (usually the same as input download status)
     * @param downloadStatus 
     */
    getStatusForDisplay(downloadStatus: string){
        return DisplayPrefs.getDownloadStatusLabel(downloadStatus);
    }

    /**
     * Update the percentage in the cartstatus
     */
    updateDownloadPercentage(percentage: number){
        if (this.dataCart && this.downloadFiles) {
            let title = (this.dataCart.isGlobalCart()) ? "Global Data Cart"
                                                       : this.downloadFiles[0].resTitle? this.downloadFiles[0].resTitle.substring(0,20)+"..." : "No title...";

            this.dataCartStatus.updateDownloadPercentage(this.dataCart.getName(), percentage, title);
        }
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
     * Cancel download a particular zip file in the bundle
     * @param zip Current zip to be cancelled
     */
    cancelDownloadZip(zip: ZipData){
        this.downloadService.cancelDownloadZip(zip, this.dataCart);
    }

    /**
     * Display error message of the given zip file 
     * @param event 
     * @param overlaypanel - the pop up control
     * @param zip 
     */
    openErrZipDetails(event, overlaypanel: OverlayPanel, zip: ZipData = null ) {
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
            if (zip.downloadStatus == DownloadStatus.ERROR)
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
        if(this.inBrowser){
            var w = window.innerWidth > 500 ? 500 : window.innerWidth;
            return w + 'px';
        }else{
            return '500px';
        }
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
     * @param zip 
     */
    downloadOneZip(zip: ZipData) {
        if (zip.downloadInstance != null) {
            zip.downloadInstance.unsubscribe();
        }
        this.downloadService.increaseTotalBundleBySize(zip.bundleSize);
        this.downloadService.download(zip, this.zipData, this.dataCart);
    }

    private generateZipFileName(base : string = null) : string {
        const MIN : number = 0;
        const MAX : number = 100000;
        let suffix = Math.floor(Math.random() * (MAX - MIN + 1)) + MIN;
        return base + suffix;
    }

    /**
     * download the selected files from this cart.
     */
    public downloadSelectedFiles() {
        this.showCurrentTask = true;
        this.currentTask = "Preparing downloads...";
        this.clearDownloadingStatus();
        this.zipData = [];
        this.allDownloadCancelled = false;
        this.bundlePlanMessage = null;
        this.downloadStartTime = new Date();

        // Sending data to _bundle_plan and get back the plan
        this.downloadFiles = this.dataCart.getSelectedFiles();
        let bundleBaseName = this.generateZipFileName(this.dataCart.getName());
        
        this.bundlePlanRef = this.downloadService.getBundlePlan(bundleBaseName, this.downloadFiles).subscribe(
            blob => {
                // console.log(JSON.stringify(blob, null, 2));
                this.bundlePlanStatus = blob.status.toLowerCase();
                this.bundlePlanMessage = blob.messages;
                this.bundlePlanUnhandledFiles = blob.notIncluded;
                this.messageColor = this.getColor();

                if (this.bundlePlanUnhandledFiles) {
                    this.markUnhandledFiles();
                }
                if (this.bundlePlanStatus == BundlePlanStatus.COMPLETED ||
                    this.bundlePlanStatus == BundlePlanStatus.WARNINGS    )
                {
                    if(this.bundlePlanStatus == BundlePlanStatus.WARNINGS) {
                        let dateTime = new Date();

                        this.showUnhandledFiles = false;
                        this.emailSubject = 'PDR: Error getting download plan';
                        this.emailBody = this.emailBodyBase
                            + 'URL:' + blob.diagnostics['url'] + '; %0D%0A'
                            + 'Time: ' + blob.diagnostics['time'] + '%0D%0A%0D%0A'
                            + 'Post message:%0D%0A' + blob.diagnostics['body'] + ';' + '%0D%0A%0D%0A' + 'Return message:%0D%0A' + JSON.stringify(blob);
                    }

                    this.bundleplan = blob;
                    this.downloadService.setTotalBundleSize(blob.size);

                    for (let bundle of blob.bundleNameFilePathUrl) {
                        this.zipData.push({ "fileName": bundle.bundleName, "downloadProgress": 0, "downloadStatus": null, "downloadInstance": null, "bundle": bundle, "downloadUrl": blob.postEachTo, "downloadErrorMessage": "","bundleSize": bundle.bundleSize, 'downloadTime': null });
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
                            this.processBundle();
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
                    this.emailSubject = 'PDR: Error getting download plan';
                    this.emailBody = this.emailBodyBase
                        + 'URL:' + blob.diagnostics['url'] + '; %0D%0A'
                        + 'Time: ' + blob.diagnostics['time'] + '%0D%0A%0D%0A'
                        + 'Post message:%0D%0A' + blob.diagnostics['body'] + ';' + '%0D%0A%0D%0A' + 'Return message:%0D%0A' + JSON.stringify(blob);
                    this.showUnhandledFiles = false;
                    this.showCurrentTask = false;
                    this.unsubscribeBundleplan();
                }
            },
            err => {
                // err is an object with diagnostic information in it
                console.log("Calling following end point returned error:");
                console.log(err['url']);
                console.log("Post message:", err['body']);
                console.log("Error message:", err['error']);
                this.bundlePlanMessage = err['error'];
                this.bundlePlanStatus = BundlePlanStatus.INTERNAL_ERROR;
                this.showCurrentTask = false;
                this.messageColor = this.getColor();
                this.emailSubject = 'PDR: Error getting download plan';
                this.emailBody =
                    'The information below describes an error that occurred while downloading data via the data cart.' + '%0D%0A%0D%0A'
                    + '[From the PDR Team:  feel free to add additional information about the failure or your questions here.  Thanks for sending this message!]' + '%0D%0A%0D%0A'
                    + 'URL:' + err['url']
                    + 'Time: ' + err['time'] + '%0D%0A%0D%0A'
                    + '_bundle_plan; ' + '%0D%0A%0D%0A'
                    + 'Post message:%0D%0A' + err['body'] + '%0D%0A%0D%0A'
                    + 'Error message:%0D%0A' + JSON.stringify(err['error']);
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
     * Process data returned from bundle_plan (stored in zipData)
     */
    processBundle() {
        let processingZip: ZipData;
        this.gaService.gaTrackEvent('download', undefined, 'all files', "Data cart");

        this.messageColor = this.getColor();

        // Start downloading the first one, this will set the downloaded zip file to 1 which will
        // trigger the following listener
        this.downloadService.downloadNextZip(this.zipData, this.dataCart);

        this.subscriptions.push(this.downloadService.watchDownloadingNumber().subscribe(
            value => {
                if (value >= 0) {
                    if (!this.allDownloadCancelled) {
                        this.overallStatus = DownloadStatus.DOWNLOADING;
                        this.outputOverallStatus.emit(this.overallStatus);
                        this.downloadService.downloadNextZip(this.zipData, this.dataCart);
                    }
                    else
                    {
                        this.overallStatus = DownloadStatus.CANCELED;
                        this.outputOverallStatus.emit(this.overallStatus);
                        setTimeout(() => {
                            this.updateDownloadPercentage(0);
                        }, 1000);
                    }
                }
            }
        ));
    }

    /**
     * Get the overall progress for progress bar display
     */
    get overallProgress(){
        let returnValue = 0;
        if(this.downloadService.totalBundleSize > 0 && this.downloadService.totalBundleSize >= this.downloadService.totalDownloaded){
            returnValue = Math.round(100 * this.downloadService.totalDownloaded / this.downloadService.totalBundleSize);
        }else if(this.downloadService.totalBundleSize > 0){
            returnValue = 100;
        }else {   
            returnValue = 0;
        }

        this.updateDownloadPercentage(returnValue)
        return returnValue;
    }

    /**
     * Reset download params
     */
    resetDownloadParams() {
        this.zipData = [];
        this.downloadService.setDownloadingNumber(-1);
        this.allDownloadCancelled = true;
        this.bundlePlanMessage = null;
        this.bundlePlanStatus = null;
        this.bundlePlanUnhandledFiles = null;
    }

    /**
     * clears all download status for the current set of files being downloaded
     */
    clearDownloadingStatus() {
        this.resetDownloadParams();

        this.dataCart.restore();
        this._clearCartDownloadStatus();
        this.dataCart.save();
        this.downloadService.resetDownloadData();
    }

    private _clearCartDownloadStatus() : void {
        if (! this.downloadFiles)
            return;
        for (let dfile of this.downloadFiles) 
            this.dataCart.setDownloadStatus(dfile.resId, dfile.filePath, DownloadStatus.NO_STATUS,
                                            false, { zipFile: '', message: '' });
    }

    /**
     * Set color for the message from bundle plan
     */
    getColor() {
        if (this.bundlePlanStatus == BundlePlanStatus.WARNINGS) {
            return "darkorange";
        } else if (this.bundlePlanStatus == BundlePlanStatus.ERROR ||
                   this.bundlePlanStatus == BundlePlanStatus.INTERNAL_ERROR) {
            return "red";
        } else {
            return "black";
        }
    }

    /**
     * Mark the data cart for those unhandled files
     */
    markUnhandledFiles() {
        this.dataCart.restore();

        let p: number = -1;
        let resid: string = null;
        let filepath: string = null;
        for (let unhandledFile of this.bundlePlanUnhandledFiles) {
            p = unhandledFile.filePath.indexOf('/');
            if (p < 0) {
                console.warn("markUnhandledFiles(): Unexpected file ID: " + unhandledFile.filePath);
                continue;
            }
            resid = unhandledFile.filePath.substring(0, p);
            filepath = unhandledFile.filePath.substring(p+1);
            this.dataCart.setDownloadStatus(resid, filepath, DownloadStatus.FAILED, false,
                                            { message: unhandledFile.message });
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
     * Cancell all download and cleanup all zipdata
     */
    cancelDownloadAll() {
        for (let zip of this.zipData) {
            if(zip.downloadStatus == DownloadStatus.DOWNLOADING) {
                this.cancelDownloadZip(zip);
            }else{
                if (zip.downloadInstance != null) {
                    zip.downloadInstance.unsubscribe();
                }
                zip.downloadInstance = null;
                zip.downloadProgress = 0;
                zip.downloadStatus = null;
            }
       }

        for (let sub of this.subscriptions) {
            sub.unsubscribe();
        }

        this.showCurrentTask = false;
        this.overallStatus = DownloadStatus.CANCELED;
        this.outputOverallStatus.emit(this.overallStatus);
        setTimeout(() => {
            this.updateDownloadPercentage(0)
        }, 1000);

        this.zipData = [];
    }

    /**
     * Function to display bytes in appropriate format.
     * @param bytes - input data in bytes
     */
    formatBytes(bytes) {
        return formatBytes(bytes);
    }
}
