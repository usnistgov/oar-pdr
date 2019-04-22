import { Component, OnInit, OnDestroy, AfterViewInit, ElementRef, ViewChildren, Input, NgZone } from '@angular/core';
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
import * as _ from 'lodash';
import * as __ from 'underscore';
import { environment } from '../../environments/environment';
import { DownloadData } from '../shared/download-service/downloadData';

import { CommonVarService } from '../shared/common-var'
import { DownloadService } from '../shared/download-service/download-service.service';
import { ZipData } from '../shared/download-service/zipData';
import { OverlayPanel } from 'primeng/overlaypanel';
import { AppConfig, Config } from '../shared/config-service/config.service';
import { BootstrapOptions } from '@angular/core/src/application_ref';
import { AsyncBooleanResultCallback } from 'async';
import { FileSaverService } from 'ngx-filesaver';
import { CommonFunctionService } from '../shared/common-function/common-function.service';

declare var Ultima: any;
declare var saveAs: any;
declare var $: any;

@Component({
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
  ediid: any;
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
  dataArray: string[] = [];
  confValues: Config;
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
  statusWidth: string;
  fontSize: string;
  emailSubject: string;
  emailBody: string;

  /**
   * Creates an instance of the SearchPanel
   *
   */
  constructor(private http: HttpClient,
    private cartService: CartService,
    private downloadService: DownloadService,
    private appConfig: AppConfig,
    private _FileSaverService: FileSaverService,
    private commonVarService: CommonVarService,
    private commonFunctionService: CommonFunctionService,
    private route: ActivatedRoute,
    ngZone: NgZone) {
    this.mobHeight = (window.innerHeight);
    this.mobWidth = (window.innerWidth);
    this.setWidth(this.mobWidth);

    window.onresize = (e) => {
      ngZone.run(() => {
        this.mobWidth = window.innerWidth;
        this.mobHeight = window.innerHeight;
        this.setWidth(this.mobWidth);
      });
    };

    this.confValues = this.appConfig.getConfig();
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
    this.commonVarService.setContentReady(false);
    this.isProcessing = true;
    this.ediid = this.commonVarService.getEdiid();
    this.distApi = this.confValues.DISTAPI;
    this.routerparams = this.route.params.subscribe(params => {
      this.mode = params['mode'];
    })

    if (this.mode == 'popup') {
      this.cartService.setCurrentCart('landing_popup');
      this.commonVarService.setLocalProcessing(true);

      this.loadDatacart().then(function (result) {
        this.commonVarService.setContentReady(true);
        this.downloadAllFilesFromAPI();
      }.bind(this), function (err) {
        console.log("Error while loading datacart:");
        console.log(err);
        // alert("something went wrong while loading datacart.");
      });

    } else {
      this.cartService.setCurrentCart('cart');
      this.loadDatacart().then(function (result) {
        this.commonVarService.setContentReady(true);
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
      this.statusWidth = 'auto';
      this.fontSize = '16px';
    } else if (mobWidth > 780 && this.mobWidth <= 1340) {
      this.titleWidth = '60%';
      this.typeWidth = '150px';
      this.sizeWidth = '100px';
      this.statusWidth = '150px';
      this.fontSize = '14px';
    }
    else {
      this.titleWidth = '40%';
      this.typeWidth = '20%';
      this.sizeWidth = '20%';
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
      this.expandToLevel(this.dataFiles, true, 1);
      this.checkNode(this.dataFiles);
      this.dataFileCount();
    }.bind(this), function (err) {
      console.log("Error while loading datacart:");
      console.log(err);
      // alert("something went wrong while fetching the datacart");
    });
    return Promise.resolve(this.dataFiles);
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
    var randomnumber = Math.floor(Math.random() * (this.commonVarService.getRandomMaximum() - this.commonVarService.getRandomMinimum() + 1)) + this.commonVarService.getRandomMinimum();

    var zipFileBaseName = "download" + randomnumber;
    files.data.downloadFileName = zipFileBaseName;
    files.data.downloadStatus = 'downloading';

    postMessage.push({ "bundleName": files.data.downloadFileName, "includeFiles": this.downloadData });
    // console.log('Bundle plan post message:');
    // console.log(JSON.stringify(postMessage[0]));

    this.getBundlePlanRef = this.downloadService.getBundlePlan(this.distApi + "_bundle_plan", JSON.stringify(postMessage[0])).subscribe(
      blob => {
        this.showCurrentTask = false;
        this.isProcessing = false;
        this.processBundle(blob, zipFileBaseName, files);
      },
      err => {
        console.log("Calling following end point returned error:");
        console.log(this.distApi + "_bundle_plan");
        console.log("Post message:");
        console.log(JSON.stringify(postMessage[0]));
        console.log("Error message:");
        console.log(err);
        this.bundlePlanMessage = err;
        this.bundlePlanStatus = "error";
        this.isProcessing = false;
        this.showCurrentTask = false;
        this.messageColor = this.getColor();
        this.emailSubject = 'PDR: Error getting bundle plan';
        this.emailBody = 'URL:' + this.distApi + '_bundle_plan; Post message:' + JSON.stringify(postMessage[0]);
        this.unsubscribeBundleplan();
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
  processBundle(res: any, zipFileBaseName: any, files: any) {
    this.currentTask = "Processing Each Bundle...";

    this.bundlePlanStatus = res.status.toLowerCase();
    this.messageColor = this.getColor();
    this.bundlePlanUnhandledFiles = res.notIncluded;
    this.bundlePlanMessage = res.messages;
    if (this.bundlePlanMessage != null) {
      this.broadcastMessage = 'Http responsed with warning.';
    }

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
                child2 = this.createDataCartChildrenTree(
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
  createDataCartChildrenTree(path: string, cartId: string, resId: string, ediid: string, resTitle: string, downloadUrl: string, resFilePath: string, downloadStatus: string, mediatype: string, description: string, filetype: string, isSelected: boolean, fileSize: any, message: string) {
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
    this.downloadService.decreaseNumberOfDownloading("datacart");
  }

  /*
  * Set color for bundle plan return message 
  */
  getColor() {
    if (this.bundlePlanStatus == 'warnings') {
      return "darkorange";
    } else if (this.bundlePlanStatus == 'error') {
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
      return "grey";
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

  /*
  * Pre-select tree nodes
  */
  checkNode(nodes: TreeNode[]) {
    for (let i = 0; i < nodes.length; i++) {
      if (nodes[i].children.length > 0) {
        for (let j = 0; j < nodes[i].children.length; j++) {
          if (nodes[i].children[j].children.length == 0) {
            if (nodes[i].children[j].data.isSelected) {
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
      if (nodes[i].children.length == 0) {
        return;
      }

      this.checkNode(nodes[i].children);
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

  /**
  * Return "download" button color based on download status
  **/
  getDownloadBtnColor(rowData: any) {
    if (rowData.downloadStatus == 'downloaded')
      return 'green';

    return '#1E6BA1';
  }

  /**
  * Function to set status when a file was downloaded
  **/
  setFileDownloaded(rowData: any) {
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
    console.log(w);
    return w + 'px';
  }
}

