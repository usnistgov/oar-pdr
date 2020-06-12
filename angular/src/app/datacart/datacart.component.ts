import { Component, OnInit, OnDestroy, NgZone, HostListener } from '@angular/core';
import { HttpClient, HttpRequest, HttpEventType } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import 'rxjs/add/operator/map';
import { TreeNode } from 'primeng/primeng';
import { CartService } from './cart.service';
import { CartEntity } from './cart.entity';
import { DownloadData } from '../shared/download-service/downloadData';

import { DownloadService } from '../shared/download-service/download-service.service';
import { ZipData } from '../shared/download-service/zipData';
import { OverlayPanel } from 'primeng/overlaypanel';
import { AppConfig } from '../config/config';
import { FileSaverService } from 'ngx-filesaver';
import { CommonFunctionService } from '../shared/common-function/common-function.service';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { DownloadConfirmComponent } from './download-confirm/download-confirm.component';
import {formatDate } from '@angular/common';
import { ConfirmationDialogComponent } from '../shared/confirmation-dialog/confirmation-dialog.component';

declare var saveAs: any;
declare var $: any;

@Component({
    moduleId: module.id,
    selector: 'data-cart',
    templateUrl: 'datacart.component.html',
    styleUrls: ['datacart.component.css'],
})

export class DatacartComponent implements OnInit, OnDestroy {
    //Data cart
    cartEntities: CartEntity[];

    //Bundle
    bundlePlanStatus: any;
    bundlePlanMessage: any[];
    unhandledFiles: any[];
    bundlePlanUnhandledFiles: any[] = null;
    bundleSizeAlert: number;
    bundleplan: any;
    bundlePlanRef: any;

    //For display
    downloadStatusExpanded: boolean = true;
    showUnhandledFiles: boolean = true;
    isVisible: boolean = true;
    isExpanded: boolean = true;
    showUnhandledFilesTable: boolean = true;
    showZipFiles: boolean = true;
    showZipFilesNmaes: boolean = true;
    showCurrentTask: boolean = false;
    showMessage: boolean = true;
    messageColor: any;
    currentTask: string = '';
    mobWidth: number;
    mobHeight: number;
    titleWidth: string;
    typeWidth: string;
    sizeWidth: string;
    actionWidth: string;
    statusWidth: string;
    fontSize: string;
    screenWidth: number;
    screenSizeBreakPoint: number;
    imageURL: string;

    //Connection
    distApi: string;
    routerparams: any;
    serviceApi: string = '';

    //Data
    fileNode: TreeNode;
    selectedNodes: TreeNode[] = [];
    isNodeSelected: boolean = false;
    mode: any;
    treeRoot = [];
    selectedTreeRoot = [];
    index: any = {};
    selectedNode: TreeNode[] = [];
    selectedFileCount: number = 0;
    selectedParentIndex: number = 0;
    minimum: number = 1;
    maximum: number = 100000;
    selectedData: TreeNode[] = [];
    dataFiles: TreeNode[] = [];

    //Download
    totalDownloaded: number = 0;
    noFileDownloaded: boolean; // will be true if any item in data cart is downloaded
    downloadData: DownloadData[];
    zipData: ZipData[] = [];
    allDownloadCancelled: boolean = false;
    subscriptions: any = [];
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

    // Email
    emailSubject: string;
    emailBody: string;
    emailBodyBase: string = 'The information below describes an error that occurred while downloading data via the data cart. %0D%0A%0D%0A [From the PDR Team:  feel free to add additional information about the failure or your questions here. Thanks for sending this message!] %0D%0A%0D%0A';

    // Overall progress
    totalDownloadedSize: number = 0;
    downloadSpeed = 0.00;
    overallStatus: string = null;
    downloadStartTime: any;
    downloadEndTime: any;
    totalDownloadTime: number;

    // For pop up
    modalRef: any;


    /**
     * Creates an instance of the SearchPanel
     *
     */
    constructor(private http: HttpClient,
        private cartService: CartService,
        private downloadService: DownloadService,
        private cfg: AppConfig,
        private _FileSaverService: FileSaverService,
        public commonFunctionService: CommonFunctionService,
        private route: ActivatedRoute,
        public gaService: GoogleAnalyticsService,
        private modalService: NgbModal,
        ngZone: NgZone) 
    {
        this.mobHeight = (window.innerHeight);
        this.mobWidth = (window.innerWidth);
        this.setWidth(this.mobWidth);
        this.screenSizeBreakPoint = +this.cfg.get("screenSizeBreakPoint", "1060");
        console.log('this.screenSizeBreakPoint', this.screenSizeBreakPoint)
        window.onresize = (e) => {
            ngZone.run(() => {
                this.mobWidth = window.innerWidth;
                this.mobHeight = window.innerHeight;
                this.setWidth(this.mobWidth);
            });
        };

        this.cartService.watchForceDatacartReload().subscribe(
            value => {
                if (value) {
                    this.getDataCartList("Init");
                }
            }
        );
    }

    /**
     * Get the params OnInit
     */
    ngOnInit() {
        this.imageURL = 'assets/images/sdp-background.jpg';

        console.log("Datacart init...");
        this.distApi = this.cfg.get("distService", "/od/ds/");
        this.bundleSizeAlert = +this.cfg.get("bundleSizeAlert", "1000000000");
        this.routerparams = this.route.params.subscribe(params => {
            this.mode = params['mode'];
        })

        if (this.mode == 'popup') {
            this.cartService.setCurrentCart('landing_popup');

            this.loadDatacart().then(function (result) {
                this.downloadAllFilesFromAPI();
            }.bind(this), function (err) {
                console.log("Error while loading datacart:");
                console.log(err);
                // alert("something went wrong while loading datacart.");
            });

        } else {
            this.cartService.setCurrentCart('cart');
            this.loadDatacart().then(function (result) {
                this.clearDownloadingStatus();
            }.bind(this), function (err) {
                console.log("Error while loading datacart:");
                console.log(err);
                // alert("something went wrong while loading datacart.");
            });

        }

        this.downloadService.watchDownloadProcessStatus("datacart").subscribe(
            value => {
                if(value)
                {
                    this.totalDownloadedSize = 0;
                    // this.downloadService.setTotalBundleSize(0);
                    this.downloadEndTime = new Date();
                    this.totalDownloadTime = this.downloadEndTime.getTime() / 1000 - this.downloadStartTime.getTime() / 1000;
                    console.log('this.downloadEndTime', this.downloadEndTime);
                    this.overallStatus = 'complete';
                }
            }
        );

        this.downloadService.watchAnyFileDownloaded().subscribe(
            value => {
                this.noFileDownloaded = !value;
                if (value) {
                    this.totalDownloaded = this.downloadService.getTotalDownloadedFiles(this.dataFiles);
                }
            }
        );
    }

    /**
     *  Following functions detect screen size
     */
    @HostListener("window:resize", [])
    public onResize() {
        this.detectScreenSize();
    }

    public ngAfterViewInit() {
        this.detectScreenSize();
    }

    private detectScreenSize() {
        this.screenWidth = window.innerWidth;
    }

    /*
    * Following functions set tree table style
    */
    headerStyle(width) {
        return { 'background-color': '#1E6BA1', 'width': width, 'color': 'white', 'font-size': this.fontSize };
    }

    bodyStyle(width) {
        return { 'width': width, 'font-size': this.fontSize };
    }

    setWidth(mobWidth: number) {
        if (mobWidth > 1340) {
            this.titleWidth = '60%';
            this.typeWidth = 'auto';
            this.sizeWidth = 'auto';
            this.actionWidth = '30px';
            this.statusWidth = 'auto';
            this.fontSize = '16px';
        } else if (mobWidth > 780 && this.mobWidth <= 1340) {
            this.titleWidth = '60%';
            this.typeWidth = '150px';
            this.sizeWidth = '100px';
            this.actionWidth = '30px';
            this.statusWidth = '150px';
            this.fontSize = '14px';
        }
        else {
            this.titleWidth = '40%';
            this.typeWidth = '20%';
            this.sizeWidth = '20%';
            this.actionWidth = '10%';
            this.statusWidth = '20%';
            this.fontSize = '12px';
        }
    }

    /*
    * Loaing datacart
    */
    loadDatacart() {
        this.currentTask = "Loading Datacart...";
        this.selectedData = [];
        this.getDataCartList("Init").then(function (result) {
            this.createDataCartHierarchy();

            // create root
            const newPart = {
                data: {
                    resTitle: "root"
                }, children: []
            };
            newPart.children = this.dataFiles;
            this.treeRoot.push(newPart);

            this.fileNode = { "data": { "resTitle": "", "size": "", "mediatype": "", "description": "", "filetype": "" } };
            this.buildSelectNodes(this.dataFiles)
            this.checkNode(this.dataFiles, this.selectedNodes);
            this.dataFileCount();
            this.expandToLevel(this.dataFiles, true, 3);
        }.bind(this), function (err) {
            console.log("Error while loading datacart:");
            console.log(err);
            // alert("something went wrong while fetching the datacart");
        });
        return Promise.resolve(this.dataFiles);
    }

    /**
     * Build selected nodes to be used to pre-select file tree. It walks through the given treenodes 
     * and collects the nodes whose isSelected field is set and put them in selectedNodes.
     * @param nodes The treenodes to be walked through
     */
    buildSelectNodes(nodes: TreeNode[]) {
        for (let i = 0; i < nodes.length; i++) {
            if (nodes[i].children.length > 0) {
                this.buildSelectNodes(nodes[i].children);
            } else {
                if (nodes[i].data.isSelected) {
                    this.addNode(nodes[i]);
                }
            }
        }
    }

    /**
     * Add the given treenode and it's children nodes to selectedNodes which will be used to 
     * pre-select the file tree.
     * @param node The treenode to be added to selectedNodes
     */
    addNode(node: TreeNode) {
        if (node.children.length == 0) {
            if (!this.selectedNodes.includes(node)) {
                this.selectedNodes.push(node);
            }
            return;
        }
        for (let i = 0; i < node.children.length; i++) {
            this.addNode(node.children[i]);
        }
    }

    /**
    * Pre-select tree nodes based on a given selection
    * 
    * @param nodes  The treenodes to be pre-checked based on the 2nd param selectedNodes
    * 
    * @param selectedNodes  Selected treenodes
    */
    checkNode(nodes: TreeNode[], selectedNodes: TreeNode[]) {
        for (let i = 0; i < nodes.length; i++) {
            if (nodes[i].children.length > 0) {
                for (let j = 0; j < nodes[i].children.length; j++) {
                    if (nodes[i].children[j].children.length == 0) {
                        if (selectedNodes.includes(nodes[i].children[j])) {
                            if (!this.selectedData.includes(nodes[i].children[j])) {
                                this.selectedData.push(nodes[i].children[j]);
                            }
                        }
                    }
                }
            } else {
                if (nodes[i].data.isSelected) {
                    if (!this.selectedData.includes(nodes[i]))
                        this.selectedData.push(nodes[i]);
                }
            }
            if (nodes[i].children.length > 0) {
                this.checkNode(nodes[i].children, selectedNodes);
                let count = nodes[i].children.length;
                let c = 0;
                for (let j = 0; j < nodes[i].children.length; j++) {
                    if (this.selectedData.includes(nodes[i].children[j])) {
                        c++;
                    }
                    if (nodes[i].children[j].partialSelected) nodes[i].partialSelected = true;
                }
                if (c == 0) { }
                else if (c == count) {
                    nodes[i].partialSelected = false;
                    if (!this.selectedData.includes(nodes[i])) {
                        this.selectedData.push(nodes[i]);
                    }
                }
                else {
                    nodes[i].partialSelected = true;
                }
            }
        }
    }

    /*
    * Taggle zip file display
    */
    showHideZipFiles() {
        this.showZipFilesNmaes = !this.showZipFilesNmaes;
    }

    /*
    * Expand the tree to a level
    */
    expandToLevel(dataFiles: any, option: boolean, targetLevel: any) {
        this.expandAll(dataFiles, option, 0, targetLevel)
    }

    /*
    * Expand the tree to a level - detail
    */
    expandAll(dataFiles: any, option: boolean, level: any, targetLevel: any) {
        let currentLevel = level + 1;

        for (let i = 0; i < dataFiles.length; i++) {
            dataFiles[i].expanded = option;
            if (targetLevel != null) {
                if (dataFiles[i].children.length > 0 && currentLevel < targetLevel) {
                    this.expandAll(dataFiles[i].children, option, currentLevel, targetLevel);
                }
            } else {
                if (dataFiles[i].children.length > 0) {
                    this.expandAll(dataFiles[i].children, option, currentLevel, targetLevel);
                }
            }
        }
        this.isExpanded = option;
        this.isVisible = false;
        setTimeout(() => {
            this.isVisible = true;
        }, 0);
    }

    ngOnDestroy() {
    }

    clearAll() {
        var i: number;
        for (i = 0; i < this.dataFiles.length; i++) {
            if (this.dataFiles[i].expanded == true) {
                this.selectedParentIndex = i;
            }
        }
        this.cartService.clearTheCart();
        this.updateCartEntries();
        if (this.cartEntities.length > 0) {
            this.dataFiles[this.selectedParentIndex].expanded = true;
        }

        setTimeout(() => {
            this.expandToLevel(this.dataFiles, true, null);
        }, 0);
        this.isVisible = false;
        setTimeout(() => {
            this.isVisible = true;
        }, 0);
    }

    /**
     * Function to get the datacart list.
     */
    getDataCartList(state: string = '') {
        this.cartService.getAllCartEntities().then(function (result) {
            this.cartEntities = result;
        }.bind(this), function (err) {
            console.log("Error while getting datacart list:");
            console.log(err);
            // alert("something went wrong while fetching the datacart");
        });
        return Promise.resolve(this.cartEntities);
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
        // this.displayDownloadFiles = true;
        this.allDownloadCancelled = false;
        this.bundlePlanMessage = null;
        // this.downloadStatus = 'downloading';
        this.downloadService.setDownloadProcessStatus(false, "datacart");
        this.currentTask = "Preparing downloads...";
        this.downloadService.setDownloadingNumber(0, "datacart");

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
        // console.log('Bundle plan post message:', JSON.stringify(postMessage[0]));
        console.log("Calling following end point to get bundle plan:", this.distApi + "_bundle_plan");

        this.bundlePlanRef = this.downloadService.getBundlePlan(this.distApi + "_bundle_plan", JSON.stringify(postMessage[0])).subscribe(
            blob => {
                console.log('Bundle plan return:', blob);
                this.bundlePlanStatus = blob.status.toLowerCase();
                this.bundlePlanMessage = blob.messages;
                this.bundlePlanUnhandledFiles = blob.notIncluded;
                // if (this.bundlePlanMessage != null && this.bundlePlanMessage != undefined && this.bundlePlanStatus != 'complete') {
                //     this.broadcastMessage = 'Server responsed with ' + this.bundlePlanStatus + '.';
                // }
                this.messageColor = this.getColor();
                //   console.log("Bundle plan return:", JSON.stringify(blob));

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
            
                            this.downloadService.setDownloadStatus(zip, this.dataFiles, 'pending');
                        }
                    }

                    let ngbModalOptions: NgbModalOptions = {
                        backdrop: 'static',
                        keyboard: false,
                        windowClass: "myCustomModalClass",
                        size: 'lg'
                    };

                    // If bundle size exceeds the alert limit, pop up confirm window
                    // if(blob.size > this.bundleSizeAlert)
                    // {
                        this.modalRef = this.modalService.open(DownloadConfirmComponent, ngbModalOptions);
                        this.modalRef.componentInstance.bundle_plan_size = blob.size;
                        this.modalRef.componentInstance.zipData = this.zipData;
                        this.modalRef.componentInstance.totalFiles = blob.filesCount;
                        this.modalRef.componentInstance.returnValue.subscribe((returnValue) => {
                            console.log(returnValue);
                            if ( returnValue ) {
                                this.showCurrentTask = false;
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

                    // }else  // If bundle size does not exceed the alert limit, continue download
                    // {
                    //     this.showCurrentTask = false;
                    //     this.processBundle(this.bundleplan);
                    // }
                }
                else // error
                {
                    let dateTime = new Date();
                    // console.log("Bundle plan returned error. Post message:", JSON.stringify(postMessage[0]));
                    // console.log("Bundle plan return:", blob);
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

        this.downloadService.downloadNextZip(this.zipData, this.dataFiles, "datacart");

        // Start downloading the first one, this will set the downloaded zip file to 1
        this.subscriptions.push(this.downloadService.watchDownloadingNumber("datacart").subscribe(
            value => {
                if (value >= 0) {
                    if (!this.allDownloadCancelled) {
                        this.overallStatus = "downloading";
                        this.downloadService.downloadNextZip(this.zipData, this.dataFiles, "datacart");
                    }
                    else
                    {
                        this.overallStatus = "Cancelled";
                    }
                }
            }
        ));
    }

    get overallProgress(){
        if(this.downloadService.totalBundleSize > 0 && this.downloadService.totalBundleSize >= this.downloadService.totalDownloaded)
            return Math.round(100 * this.downloadService.totalDownloaded / this.downloadService.totalBundleSize);
        else if(this.downloadService.totalBundleSize > 0)
            return 100;
        else    
            return 0;
    }

    /**
    * Download one particular zip
    **/
    downloadOneZip(zip: ZipData) {
        if (zip.downloadInstance != null) {
            zip.downloadInstance.unsubscribe();
        }
        this.downloadService.increaseTotalBundleBySize(zip.bundleSize);
        this.downloadService.download(zip, this.zipData, this.dataFiles, "datacart");
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
            console.log("Confirmation:", result);
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
    }

    /**
    * Reset download params
    **/
    resetDownloadParams() {
        this.zipData = [];
        this.downloadService.setDownloadingNumber(-1, "datacart");
        // this.downloadStatus = null;
        this.allDownloadCancelled = true;
        // this.displayDownloadFiles = false;
        this.downloadService.resetZipName(this.treeRoot[0]);
        this.bundlePlanMessage = null;
        this.bundlePlanStatus = null;
        this.bundlePlanUnhandledFiles = null;
    }

    /**
    * Download one particular file
    **/
    downloadOneFile(rowData: any) {
        if (rowData.downloadUrl != null && rowData.downloadUrl != undefined) {
            let filename = decodeURI(rowData.downloadUrl).replace(/^.*[\\\/]/, '');
            rowData.downloadStatus = 'downloading';
            rowData.downloadProgress = 0;
            let url = rowData.downloadUrl.replace('http:', 'https:');
            // if (rowData.downloadUrl.length > 5 && rowData.downloadUrl.substring(0, 5).toLowerCase() == 'https') {
            const req = new HttpRequest('GET', url, {
                reportProgress: true, responseType: 'blob'
            });

            rowData.downloadInstance = this.http.request(req).subscribe(event => {
                switch (event.type) {
                    case HttpEventType.Response:
                        this._FileSaverService.save(<any>event.body, filename);
                        rowData.downloadStatus = 'downloaded';
                        this.cartService.updateCartItemDownloadStatus(rowData.cartId, 'downloaded');
                        this.downloadService.setFileDownloadedFlag(true);
                        let cartEntity = this.cartEntities.filter(entry => entry.data.cartId == rowData.cartId)[0];
                        let index = this.cartEntities.indexOf(cartEntity);
                        this.cartEntities[index].data.downloadStatus = 'downloaded';
                        break;
                    case HttpEventType.DownloadProgress:
                        rowData.downloadProgress = 0;
                        if (event.total > 0) {
                            rowData.downloadProgress = Math.round(100 * event.loaded / event.total);
                        }
                        break;
                }
            },
                err => {
                    console.log(err);
                    console.log('Download url:');
                    console.log(url);
                    rowData.downloadStatus = 'error';
                    rowData.message = err;
                })
        }
    }

    /**
    * Cancel one particular download instance
    **/
    cancelDownload(rowData: any) {
        rowData.downloadInstance.unsubscribe();
        rowData.downloadInstance = null;
        rowData.downloadProgress = 0;
        rowData.downloadStatus = null;
    }

    /**
     * Count the selected files
     */
    dataFileCount() {
        this.selectedFileCount = 0;
        for (let selData of this.selectedData) {
            if (selData.data['resFilePath'] != null) {
                if (selData.data.isLeaf) {
                    this.selectedFileCount++;
                }
            }
        }
    }

    /**
     * Update cart entries
     */
    updateCartEntries() {
        this.cartService.getAllCartEntities().then(function (result) {
            this.cartEntities = result;
            this.createDataCartHierarchy();
        }.bind(this), function (err) {
            console.log("Error while updating cart entries:");
            console.log(err);
            // alert("something went wrong while fetching the products");
        });
    }

    /**
     * Removes all cart Instances that are bound to the given id.
     **/
    removeByDataId() {

        let dataId: any;
        for (let selData of this.selectedData) {
            dataId = selData.data['resId'];
            // Filter out all cartEntities with given productId,  finally the new stuff from es6 can be used.
            this.cartEntities = this.cartEntities.filter(entry => entry.data.resId != dataId);
            //save to localStorage
            this.cartService.saveListOfCartEntities(this.cartEntities);
        }
        this.getDataCartList();
        this.createDataCartHierarchy();
        if (this.mode != 'popup') {
            this.cartService.setCartLength(this.cartEntities.length);
        }
        this.selectedData = [];
        this.dataFileCount();
        this.expandToLevel(this.dataFiles, true, 1);
    }

    /**
     * Removes all cart Instances that are bound to the download status.
     **/
    removeByDownloadStatus() {
        this.selectedData = [];
        this.cartService.removeByDownloadStatus();
        this.updateCartEntries();
        this.dataFileCount();
        setTimeout(() => {
            this.expandToLevel(this.dataFiles, true, 1);
        }, 0);
        this.isVisible = false;
        setTimeout(() => {
            this.isVisible = true;
        }, 0);
    }

    /**
     * Reset datafile download status
     **/
    resetDatafileDownloadStatus(dataFiles: any, downloadStatus: any) {
        for (let i = 0; i < dataFiles.length; i++) {
            if (dataFiles[i].children.length > 0) {
                this.resetDatafileDownloadStatus(dataFiles[i].children, downloadStatus);
            } else {
                dataFiles[i].data.downloadStatus = downloadStatus;
            }
        }
    }

    /**
     * clears all download status
     **/
    clearDownloadStatus() {
        this.resetDownloadParams();
        this.cartService.updateCartDownloadStatus(null);
        this.resetDatafileDownloadStatus(this.dataFiles, null);
        this.downloadService.setFileDownloadedFlag(false);
        this.downloadService.resetDownloadData();
        this.totalDownloaded = 0;
    }

    /**
     * Removes all cart Instances that are bound to the given id.
     **/
    removeItem(row: any) {

        let dataId: any;
        // convert the map to an array
        let delRow = this.cartEntities.indexOf(row);
        this.cartEntities.splice(delRow, 1);
        this.cartService.saveListOfCartEntities(this.cartEntities);
        this.getDataCartList();
        this.createDataCartHierarchy();
    }

    /**
     * Create Data hierarchy for the tree
     */
    createDataCartHierarchy() {
        let arrayList = this.cartEntities.reduce(function (result, current) {
            result[current.data.resTitle] = result[current.data.resTitle] || [];
            result[current.data.resTitle].push(current);
            return result;
        }, {});

        var noFileDownloadedFlag = true;
        this.dataFiles = [];
        this.totalDownloaded = 0;
        let parentObj: TreeNode = {};

        var iii: number = 0;
        for (var key in arrayList) {
            // let resId = key;
            if (arrayList.hasOwnProperty(key)) {
                parentObj = {
                    data: {
                        'resTitle': key,
                    }
                };

                parentObj.children = [];
                for (let fields of arrayList[key]) {
                    let resId = fields.data.resId;
                    let ediid = fields.data.ediid;
                    let fpath = fields.data.filePath.split("/");
                    if (fpath.length > 0) {
                        let child2: TreeNode = {};
                        child2.children = [];
                        let parent = parentObj;
                        let folderExists: boolean = false;
                        let folder = null;
                        for (let path in fpath) {
                            if (fields.data.downloadStatus == "downloaded") {
                                this.totalDownloaded += 1;
                                noFileDownloadedFlag = false;
                            }
                            /// Added this code to avoid the issue of extra file layers in the datacart
                            if (fpath[path] !== "") {
                                child2 = this.createDataCartChildrenTree(iii,
                                    "/" + fpath[path],
                                    fields.data.cartId,
                                    resId, ediid,
                                    fpath[path],
                                    fields.data.downloadUrl,
                                    fields.data.filePath,
                                    fields.data.downloadStatus,
                                    fields.data.mediatype,
                                    fields.data.description,
                                    fields.data.filetype,
                                    fields.data.isSelected,
                                    fields.data.fileSize,
                                    fields.data.message
                                );

                                parent.children.push(child2);
                                parent = child2;
                                iii = iii + 1;
                            }
                        }
                    }
                }
                this.walkData(parentObj, parentObj, 0);
                this.dataFiles.push(parentObj);

                this.index = {};
            }
        }
        this.downloadService.setFileDownloadedFlag(!noFileDownloadedFlag);
    }

    /**
     * Create the hierarchy for the tree
     */
    walkData(inputArray, parent, level) {
        level = level || '';
        if (inputArray.children) {
            let copy = inputArray.children.filter((item) => { return true });
            copy.forEach((item) => {
                var path = inputArray.data && inputArray.data.filePath ?
                    inputArray.data.filePath : 'root';
                this.walkData(item, inputArray, level + '/' + path);
            });
        }

        if ((inputArray.data.filetype == 'nrdp:DataFile' || inputArray.data.filetype == 'nrdp:ChecksumFile') && inputArray.children.length == 0) {
            inputArray.data.isLeaf = true;
        } else {
            inputArray.data.cartId = null;
            inputArray.data.isLeaf = false;
        }

        if (inputArray.data && inputArray.data.filePath) {
            var key = level + inputArray.data.filePath;
            if (!(key in this.index)) {
                this.index[key] = inputArray;
            } else {
                inputArray.children.forEach((item) => {
                    this.index[key].children.push(item);
                })
                var indx = 0;
                var found = false;
                parent.children.forEach((item) => {
                    if (!found &&
                        item.data.filePath === inputArray.data.filePath &&
                        item.data.resId === inputArray.data.resId
                    ) {
                        found = true;
                    }
                    else if (!found) {
                        indx++;
                    }
                });
                parent.children.splice(indx, 1);
            }
        }
    }

    /**
     * Create data hierarchy for children
     */
    createDataCartChildrenTree(iii: number, path: string, cartId: string, resId: string, ediid: string, resTitle: string, downloadUrl: string, resFilePath: string, downloadStatus: string, mediatype: string, description: string, filetype: string, isSelected: boolean, fileSize: any, message: string) {
        let child1: TreeNode = {};
        child1 = {
            data: {
                'filePath': path,
                'cartId': cartId,
                'resId': resId,
                'ediid': ediid,
                'resTitle': resTitle,
                'downloadUrl': downloadUrl,
                'resFilePath': resFilePath,
                'downloadStatus': downloadStatus,
                'mediatype': mediatype,
                'description': description,
                'filetype': filetype,
                'isSelected': isSelected,
                'fileSize': fileSize,
                'message': message
            }

        };
        child1.children = [];
        return child1;
    }

    /**
     *  Cancel the download process of the given zip file
     * @param zip - the zip file to be cancelled
     */
    cancelDownloadZip(zip: any) {
        //Need to re-calculate the total file size and total downloaded size
        this.downloadService.decreaseTotalBundleBySize(zip.bundleSize);
        let downloaded = this.downloadService.totalDownloaded - zip.bundleSize*zip.downloadProgress/100;
        this.downloadService.setTotalDownloaded(downloaded);

        zip.downloadInstance.unsubscribe();
        zip.downloadInstance = null;
        zip.downloadProgress = 0;
        zip.downloadStatus = "cancelled";
        this.downloadService.setDownloadStatus(zip, this.dataFiles, "cancelled");
        this.downloadService.decreaseNumberOfDownloading("datacart");
    }

    /*
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

    /*
    * Popup file details
    */
    openDetails(event, overlaypanel: OverlayPanel, fileNode: TreeNode = null ) {
        this.isNodeSelected = true;
        this.fileNode = fileNode;

        overlaypanel.toggle(event);
    }

    /*
    * Display zip file error message
    */
    openZipDetails(event, overlaypanel: OverlayPanel, zip: ZipData = null ) {
        this.problemZip = zip;
        this.emailSubject = 'PDR: Error downloading zip file';

        overlaypanel.toggle(event);
    }
    /*
        Return button color based on Downloaded status
    */
    getButtonColor() {
        if (this.noFileDownloaded) {
            return "#1E6BA1";
        } else {
            return "#307F38";
        }
    }

    /*
        Return text color for Remove Downloaded badge
    */
    getDownloadedColor() {
        if (this.noFileDownloaded) {
            return "rgb(82, 82, 82)";
        } else {
            return "white";
        }
    }

    /*
        Return background color for Remove Downloaded badge
    */
    getDownloadedBkColor() {
        if (this.noFileDownloaded) {
            return "white";
        } else {
            return "green";
        }
    }

    /**
    * Return "download" button color based on download status
    **/
    getDownloadStatusColor(downloadStatus: string) {
        let returnColor = '#1E6BA1';

        switch (downloadStatus) {
            case 'downloaded':
                {
                    returnColor = 'green';
                    break;
                }
            case 'downloading':
                {
                    returnColor = '#00ace6';
                    break;
                }
            case 'warning':
                {
                    returnColor = 'darkorange';
                    break;
                }
            case 'cancelled':
                {
                    returnColor = 'darkorange';
                    break;
                }
            case 'failed':
                {
                    returnColor = 'darkorange';
                    break;
                }
            case 'error':
                {
                    returnColor = 'red';
                    break;
                }
            default:
                {
                    //statements; 
                    break;
                }
        }

        return returnColor;
    }

    /**
    * Function to set status when a file was downloaded
    **/
    setFileDownloaded(rowData: any) {
        // Google Analytics code to track download event
        this.gaService.gaTrackEvent('download', undefined, rowData.ediid, rowData.downloadUrl);

        rowData.downloadStatus = 'downloaded';
        this.cartService.updateCartItemDownloadStatus(rowData.cartId, 'downloaded');
        this.downloadService.setFileDownloadedFlag(true);
    }

    /**
    * Function to display bytes in appropriate format.
    **/
    formatBytes(bytes, numAfterDecimal) {
        return this.commonFunctionService.formatBytes(bytes, numAfterDecimal);
    }

    /**
    * Function to set style for different download status
    **/
    getDownloadStatusStyle(rowData: any) {
        let style: string = 'black';

        if (rowData.downloadStatus == 'error') {
            style = "red";
        }
        return style;
    }

    /*
    * Make sure the width of popup dialog is less than 500px or 80% of the window width
    */
    getDialogWidth() {
        var w = window.innerWidth > 500 ? 500 : window.innerWidth;
        // console.log(w);
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
        }

        for (let i = 0; i < element.children.length; i++) {
            this.clearTreeByDownloadStatus(element.children[i]);
        }
    }

    /**
     * 
     */
    markUnhandledFiles() {
        for (let unhandledFile of this.bundlePlanUnhandledFiles) {
            let resFilePath = unhandledFile.filePath.substring(unhandledFile.filePath.indexOf('/'));
            for (let dataFile of this.dataFiles) {
                let node = this.downloadService.searchTreeByfilePath(dataFile, resFilePath);
                if (node != null) {
                    node.data.downloadStatus = 'failed';
                    node.data.filePath = unhandledFile.filePath;
                    node.data.downloadUrl = unhandledFile.downloadUrl;
                    node.data.message = unhandledFile.message;
                    this.cartService.updateCartItemDownloadStatus(node.data['cartId'], 'failed');
                    break;
                }
            }
        }
    }

    /**
     * Return icon class based on download status
     */
    getIconClass(downloadStatus: string){
        let iconClass = "";
        switch(downloadStatus){
            case 'complete':
                iconClass = 'faa faa-check';
                break;
            case 'downloaded':
                iconClass = 'faa faa-check';
                break;
            case 'pending':
                iconClass = 'faa faa-clock-o';
                break;
            case 'cancelled':
                iconClass = 'faa faa-remove';
                break;
            case 'failed':
                iconClass = 'faa faa-warning';
                break;
            case 'error':
                iconClass = 'faa faa-warning';
                break;  
            default:
                break;              
        }

        return iconClass; 
    }


    /**
     * The status we want to display may not be exactly the same as the status in the database. This function 
     * serves as a mapper.
     * @param rowData - row data of dataFiles
     */
    getStatusForDisplay(downloadStatus: string){
        let status = "";
        switch(downloadStatus){
            case 'complete':
                status = 'Completed';
                break;
            case 'downloaded':
                status = 'Downloaded';
                break;
            case 'downloading':
                status = 'Downloading';
                break;
            case 'pending':
                status = 'Pending';
                break;
            case 'cancelled':
                status = 'Cancelled';
                break;
            case 'failed':
                status = 'Failed';
                break;
            case 'error':
                status = 'Error';
                break;  
            default:
                break;    
        }

        return status;
    }    

    /**
     * Return download time in HH:MM:SS format
     * @param downloadTime - download time in seconds 
     */
    getDownloadTime(downloadTime)
    {
        // console.log('downloadTime', downloadTime);
        if(!downloadTime) return "Calculating...";

        let hours = Math.floor(downloadTime / 3600);
        let minutes = Math.floor((downloadTime - hours * 3600)/60);
        let seconds = Math.floor(downloadTime - hours * 3600 - minutes * 60);

        let returnFormat = seconds + "sec";
        if(minutes > 0) returnFormat = minutes + "min " + returnFormat;
        if(hours > 0) returnFormat = hours + "hour " + returnFormat;

        return returnFormat;
    }
}

