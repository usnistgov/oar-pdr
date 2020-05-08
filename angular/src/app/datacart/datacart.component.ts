import { Component, OnInit, OnDestroy, AfterViewInit, ElementRef, ViewChildren, Input, NgZone, HostListener } from '@angular/core';
//import {Headers, RequestOptions, Response, ResponseContentType, URLSearchParams} from '@angular/common/http';
import { HttpClientModule, HttpClient, HttpParams, HttpRequest, HttpEventType } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { Http, HttpModule } from '@angular/http';
import 'rxjs/add/operator/map';
import { Subscription } from 'rxjs/Subscription';
import { Message } from 'primeng/components/common/api';
import {
    TreeTableModule, TreeNode, MenuItem, OverlayPanelModule,
    FieldsetModule, PanelModule, ContextMenuModule,
    MenuModule
} from 'primeng/primeng';
import { CartService } from './cart.service';
import { CartEntity } from './cart.entity';
import { Observable } from 'rxjs/Observable';
import { ProgressSpinnerModule, DialogModule } from 'primeng/primeng';
// import * as _ from 'lodash';
// import * as __ from 'underscore';
import { DownloadData } from '../shared/download-service/downloadData';

import { DownloadService } from '../shared/download-service/download-service.service';
import { ZipData } from '../shared/download-service/zipData';
import { OverlayPanel } from 'primeng/overlaypanel';
import { AppConfig } from '../config/config';
import { BootstrapOptions } from '@angular/core/src/application_ref';
import { AsyncBooleanResultCallback } from 'async';
import { FileSaverService } from 'ngx-filesaver';
import { CommonFunctionService } from '../shared/common-function/common-function.service';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';

declare var saveAs: any;
declare var $: any;

@Component({
    moduleId: module.id,
    selector: 'data-cart',
    templateUrl: 'datacart.component.html',
    styleUrls: ['datacart.component.css'],
})

export class DatacartComponent implements OnInit, OnDestroy {
    layoutCompact: boolean = true;
    layoutMode: string = 'horizontal';
    profileMode: string = 'inline';
    msgs: Message[] = [];
    exception: string;
    errorMsg: string;
    status: string;
    errorMessage: string;
    errorMessageArray: string[];
    //searchResults: any[] = [];
    searchValue: string;
    recordDisplay: any[] = [];
    keyword: string;
    downloadZIPURL: string;
    summaryCandidate: any[];
    showSpinner: boolean = false;
    findId: string;
    leftmenu: MenuItem[];
    rightmenu: MenuItem[];
    similarResources: boolean = false;
    similarResourcesResults: any[] = [];
    qcriteria: string = '';
    selectedFile: TreeNode;
    isDOI = false;
    isEmail = false;
    citeString: string = '';
    type: string = '';
    process: any[];
    requestedId: string = '';
    isCopied: boolean = false;
    distdownload: string = '';
    serviceApi: string = '';
    metadata: boolean = false;
    cartEntities: CartEntity[];
    cols: any[];
    selectedData: TreeNode[] = [];
    dataFiles: TreeNode[] = [];
    childNode: TreeNode = {};
    minimum: number = 1;
    maximum: number = 100000;
    displayFiles: any = [];
    index: any = {};
    selectedNode: TreeNode[] = [];
    selectedFileCount: number = 0;
    selectedParentIndex: number = 0;
    downloadInstance: any;
    downloadStatus: any;
    downloadProgress: any;
    displayDownloadFiles: boolean = false;
    downloadData: DownloadData[];
    zipData: ZipData[] = [];
    cancelAllDownload: boolean = false;
    treeRoot = [];
    selectedTreeRoot = [];
    subscriptions: any = [];
    showZipFiles: boolean = true;
    showZipFilesNmaes: boolean = true;
    allProcessed: boolean = false;
    downloadStatusExpanded: boolean = true;
    bundlePlanStatus: any;
    bundlePlanMessage: any[];
    unhandledFiles: any[];
    bundlePlanUnhandledFiles: any[] = null;
    showUnhandledFiles: boolean = true;
    isVisible: boolean = true;
    isExpanded: boolean = true;
    showUnhandledFilesTable: boolean = true;
    fileNode: TreeNode;
    showMessageBlock: boolean = false;
    messageColor: any;
    noFileDownloaded: boolean; // will be true if any item in data cart is downloaded
    totalDownloaded: number = 0;
    selectedNodes: TreeNode[] = [];
    distApi: string;
    currentTask: string = '';
    showCurrentTask: boolean = false;
    showMessage: boolean = true;
    broadcastMessage: string = '';
    showDownloadProgress: boolean = false;
    isProcessing: boolean = false;
    isNodeSelected: boolean = false;
    getBundlePlanRef: any;
    mode: any;
    routerparams: any;
    mobWidth: number;
    mobHeight: number;
    titleWidth: string;
    typeWidth: string;
    sizeWidth: string;
    actionWidth: string;
    statusWidth: string;
    fontSize: string;
    downloadflag: boolean = true;
    emailSubject: string;
    emailBody: string;
    imageURL: string;
    screenWidth: number;
    screenSizeBreakPoint: number;
    emailBodyBase: string = 'The information below describes an error that occurred while downloading data via the data cart. %0D%0A%0D%0A [From the PDR Team:  feel free to add additional information about the failure or your questions here.  Thanks for sending this message!] %0D%0A%0D%0A';

    /**
     * Creates an instance of the SearchPanel
     *
     */
    constructor(private http: HttpClient,
        private cartService: CartService,
        private downloadService: DownloadService,
        private cfg: AppConfig,
        private _FileSaverService: FileSaverService,
        private commonFunctionService: CommonFunctionService,
        private route: ActivatedRoute,
        private gaService: GoogleAnalyticsService,
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
        this.isProcessing = true;
        this.distApi = this.cfg.get("distService", "/od/ds/");
        this.routerparams = this.route.params.subscribe(params => {
            this.mode = params['mode'];
        })

        if (this.mode == 'popup') {
            this.cartService.setCurrentCart('landing_popup');

            this.loadDatacart().then(function (result) {
                this.clearDownloadingStatus();
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
                this.allProcessed = value;
                // this.updateDownloadStatus(this.files);
            }
        );

        this.downloadService.watchAnyFileDownloaded().subscribe(
            value => {
                this.noFileDownloaded = !value;
                if (value) {
                    this.totalDownloaded = this.downloadService.getTotalDownloaded(this.dataFiles);
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
    titleStyleHeader() {
        return { 'background-color': '#1E6BA1', 'width': this.titleWidth, 'color': 'white', 'font-size': this.fontSize };
    }

    typeStyleHeader() {
        return { 'background-color': '#1E6BA1', 'width': this.typeWidth, 'color': 'white', 'font-size': this.fontSize };
    }

    sizeStyleHeader() {
        return { 'background-color': '#1E6BA1', 'width': this.sizeWidth, 'color': 'white', 'font-size': this.fontSize };
    }

    actionStyleHeader() {
        return { 'background-color': '#1E6BA1', 'width': this.actionWidth, 'color': 'white', 'font-size': this.fontSize };
    }

    statusStyleHeader() {
        return { 'background-color': '#1E6BA1', 'width': this.statusWidth, 'color': 'white', 'font-size': this.fontSize, 'white-space': 'nowrap' };
    }

    titleStyle() {
        return { 'width': this.titleWidth, 'font-size': this.fontSize };
    }

    typeStyle() {
        return { 'width': this.typeWidth, 'font-size': this.fontSize };
    }

    sizeStyle() {
        return { 'width': this.sizeWidth, 'font-size': this.fontSize };
    }
    statusStyle() {
        return { 'width': this.statusWidth, 'font-size': this.fontSize };
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
        this.isProcessing = true;
        this.showCurrentTask = true;
        let postMessage: any[] = [];
        this.downloadData = [];
        this.zipData = [];
        this.displayDownloadFiles = true;
        this.cancelAllDownload = false;
        this.bundlePlanMessage = null;
        this.downloadStatus = 'downloading';
        this.downloadService.setDownloadProcessStatus(false, "datacart");
        this.currentTask = "Zipping files...";
        this.downloadService.setDownloadingNumber(0, "datacart");
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
        // console.log('Bundle plan post message:');
        // console.log(JSON.stringify(postMessage[0]));
        console.log("Calling following end point to get bundle plan:");
        console.log(this.distApi + "_bundle_plan");

        this.getBundlePlanRef = this.downloadService.getBundlePlan(this.distApi + "_bundle_plan", JSON.stringify(postMessage[0])).subscribe(
            blob => {
                this.showCurrentTask = false;
                this.isProcessing = false;
                this.bundlePlanStatus = blob.status.toLowerCase();
                this.bundlePlanMessage = blob.messages;
                this.bundlePlanUnhandledFiles = blob.notIncluded;
                if (this.bundlePlanMessage != null && this.bundlePlanMessage != undefined && this.bundlePlanStatus != 'complete') {
                    this.broadcastMessage = 'Server responsed with ' + this.bundlePlanStatus + '.';
                }
                this.messageColor = this.getColor();
                //   console.log("Bundle plan return:", JSON.stringify(blob));

                if (this.bundlePlanUnhandledFiles) {
                    this.markUnhandledFiles();
                }

                if (this.bundlePlanStatus == 'complete') {
                    this.processBundle(blob);
                }
                else if (this.bundlePlanStatus == 'warnings') {
                    let dateTime = new Date();

                    this.showMessageBlock = true;
                    this.showUnhandledFiles = false;
                    this.emailSubject = 'PDR: Error getting download plan';
                    this.emailBody = this.emailBodyBase
                        + 'URL:' + this.distApi + '_bundle_plan; ' + '%0D%0A'
                        + 'Time: ' + dateTime.toString() + '%0D%0A%0D%0A'
                        + 'Post message:%0D%0A' + JSON.stringify(postMessage[0]) + ';' + '%0D%0A%0D%0A' + 'Return message:%0D%0A' + JSON.stringify(blob);
                    this.processBundle(blob);
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
                    this.showMessageBlock = true;
                    this.showUnhandledFiles = false;
                    this.unsubscribeBundleplan();
                }
            },
            err => {
                let dateTime = new Date()
                console.log("Calling following end point returned error:");
                console.log(this.distApi + "_bundle_plan");
                console.log("Post message:");
                console.log(JSON.stringify(postMessage[0]));
                console.log("Error message:");
                console.log(err);
                this.bundlePlanMessage = err;
                this.bundlePlanStatus = "internal error";
                this.isProcessing = false;
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
                this.showMessageBlock = false;
            }
        );
    }

    unsubscribeBundleplan() {
        this.getBundlePlanRef.unsubscribe();
        this.getBundlePlanRef = null;
    }

    /**
    * Process data returned from bundle_plan
    **/
    processBundle(res: any) {
        this.currentTask = "Processing Each Bundle...";
        this.messageColor = this.getColor();

        let bundlePlan: any[] = res.bundleNameFilePathUrl;
        let downloadUrl: any = this.distApi + res.postEachTo;
        console.log("Bundle url:");
        console.log(downloadUrl);

        let tempData: any[] = [];

        for (let bundle of bundlePlan) {
            this.zipData.push({ "fileName": bundle.bundleName, "downloadProgress": 0, "downloadStatus": null, "downloadInstance": null, "bundle": bundle, "downloadUrl": downloadUrl, "downloadErrorMessage": "" });
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

        this.downloadService.downloadNextZip(this.zipData, this.dataFiles, "datacart");

        // Start downloading the first one, this will set the downloaded zip file to 1
        this.subscriptions.push(this.downloadService.watchDownloadingNumber("datacart").subscribe(
            value => {
                if (value >= 0) {
                    if (!this.cancelAllDownload) {
                        this.downloadService.downloadNextZip(this.zipData, this.dataFiles, "datacart");
                    }
                }
            }
        ));
    }

    /**
    * Download one particular zip
    **/
    downloadOneZip(zip: ZipData) {
        if (zip.downloadInstance != null) {
            zip.downloadInstance.unsubscribe();
        }
        this.downloadService.download(zip, this.zipData, this.dataFiles, "datacart");
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
        this.isProcessing = false;
        this.showCurrentTask = false;
        this.showMessageBlock = false;
    }

    /**
    * Reset download params
    **/
    resetDownloadParams() {
        this.zipData = [];
        this.downloadService.setDownloadingNumber(-1, "datacart");
        this.downloadStatus = null;
        this.cancelAllDownload = true;
        this.displayDownloadFiles = false;
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
            this.showDownloadProgress = true;
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
        this.totalDownloaded = 0;
        this.showMessageBlock = false;
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

    cancelDownloadZip(zip: any) {
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
    openDetails(event, fileNode: TreeNode, overlaypanel: OverlayPanel) {
        this.isNodeSelected = true;
        this.fileNode = fileNode;
        overlaypanel.hide();
        setTimeout(() => {
            overlaypanel.show(event);
        }, 100);
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
    getDownloadStatusColor(rowData: any) {
        let returnColor = '#1E6BA1';

        switch (rowData.downloadStatus) {
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
            emaibody = this.emailBodyBase + 'Time: ' + dateTime.toString() + '%0D%0A%0D%0A';
        }

        for (let zip of this.zipData) 
        {
            if(zip.downloadStatus == 'error')
            {
                emaibody += '%0D%0A%0D%0A'+ 'Zip error details:%0D%0A' + JSON.stringify(zip.bundle);
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
    getIconClass(rowData: any){
        let iconClass = "";
        switch(rowData.downloadStatus){
            case 'complete':
                iconClass = 'faa faa-check';
                break;
            case 'downloaded':
                iconClass = 'faa faa-check';
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
    getStatusForDisplay(rowData: any){
        let status = "";
        switch(rowData.downloadStatus){
            case 'complete':
                status = 'Completed';
                break;
            case 'downloaded':
                status = 'Downloaded';
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
}

