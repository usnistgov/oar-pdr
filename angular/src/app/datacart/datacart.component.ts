import { Component, OnInit, OnDestroy, AfterViewInit, ElementRef, ViewChildren, Input } from '@angular/core';
//import {Headers, RequestOptions, Response, ResponseContentType, URLSearchParams} from '@angular/common/http';
import { HttpClientModule, HttpClient, HttpParams, HttpRequest, HttpEventType } from '@angular/common/http';
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

declare var Ultima: any;
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
  display: boolean = true;
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
  // private distApi : string = "";

  private distApi: string = environment.DISTAPI;
  //private distApi:string = "http://localhost:8083/oar-dist-service";

  /**
   * Creates an instance of the SearchPanel
   *
   */
  constructor(private http: HttpClient,
    private cartService: CartService,
    private downloadService: DownloadService,
    private commonVarService: CommonVarService) {
      console.log("Datacart starts...")
      this.getDataCartList("Init");
      this.display = true;
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
    this.ediid = this.commonVarService.getEdiid();
    this.cartService.watchCartEntitesReady().subscribe(
      value => {
        if (value) {
          this.loadDatacart();
        }
      }
    );

    this.downloadService.watchDownloadProcessStatus("datacard").subscribe(
      value => {
        this.allProcessed = value;
        // this.updateDownloadStatus(this.files);
      }
    );

    // this.totalDownloaded = this.downloadService.getTotalDownloaded(this.dataFiles);

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
  * Loaing datacart
  */
  loadDatacart(){
    console.log("Loading datacart...");
    this.selectedData = [];
    this.createDataCartHierarchy();
    this.display = true;

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

    // console.log("this.dataFiles:");
    // console.log(this.dataFiles);

    this.checkNode(this.dataFiles);

    console.log("this.selectedData:");
    console.log(this.selectedData);

    this.dataFileCount();

    if (this.cartEntities.length > 0) {
      // var element = <HTMLInputElement> document.getElementById("downloadStatus");
      // element.disabled = false;
    } else {
      //var element = <HTMLInputElement> document.getElementById("downloadStatus");
      //element.disabled = true;
    }
  }


  showHideZipFiles() {
    this.showZipFilesNmaes = !this.showZipFilesNmaes;
  }

  // expandAll(dataFiles: any, level: any){
  //     let currentLevel = level + 1;
  //     for ( let i=0; i < dataFiles.length;i++) {
  //         dataFiles[i].expanded = true;
  //         if(dataFiles[i].children.length > 0 && currentLevel < 1){
  //             this.expandAll(dataFiles[i].children, currentLevel);
  //         }
  //     }

  //     this.isVisible = false;
  //     setTimeout(() => {
  //         this.isVisible = true;
  //     },0);
  // }

  expandToLevel(dataFiles: any, option: boolean, targetLevel: any) {
    this.expandAll(dataFiles, option, 0, targetLevel)
  }

  expandAll(dataFiles: any, option: boolean, level: any, targetLevel: any) {
    let currentLevel = level + 1;
    // console.log("dataFiles:");
    // console.log(dataFiles);
    // console.log("targetLevel:");
    // console.log(targetLevel);
    for (let i = 0; i < dataFiles.length; i++) {
      dataFiles[i].expanded = option;
      if (targetLevel != null) {
        // console.log("expandAll again0:");
        if (dataFiles[i].children.length > 0 && currentLevel < targetLevel) {
          // console.log("expandAll again:");
          this.expandAll(dataFiles[i].children, option, currentLevel, targetLevel);
        }
      } else {
        // console.log("expandAll again1:");
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
   * If Search is successful populate list of keywords themes and authors
   */

  getDataCartList(state: string = '') {
    this.cartService.getAllCartEntities().then(function (result) {
      this.cartEntities = result;
      if (state == 'Init')
        this.cartService.setCartEntitesReady(true);
      //   console.log("cart entities inside datacartlist" + JSON.stringify(this.cartEntities));
    }.bind(this), function (err) {
      alert("something went wrong while fetching the products");
    });
  }

  /**
      * Function to download all files from API call.
      **/
  downloadAllFilesFromAPI() {
    let postMessage: any[] = [];
    this.downloadData = [];
    this.zipData = [];
    this.displayDownloadFiles = true;
    this.cancelAllDownload = false;
    this.downloadStatus = 'downloading';
    this.downloadService.setDownloadProcessStatus(false, "datacard");

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
    files.data.downloadFileName = zipFileBaseName + ".zip"
    files.data.downloadStatus = 'downloading';

    postMessage.push({ "bundleName": files.data.downloadFileName, "includeFiles": this.downloadData });

    this.downloadService.getBundlePlan(this.distApi + "_bundle_plan", JSON.stringify(postMessage)).subscribe(
      blob => {
        // console.log("blob:");
        // console.log(blob);
        this.processBundle(blob, zipFileBaseName, files);
      },
      err => {

      }
    );
  }

  processBundle(res: any, zipFileBaseName: any, files: any) {
    this.bundlePlanStatus = res.status.toLowerCase();
    this.messageColor = this.getColor();
    this.bundlePlanUnhandledFiles = res.notIncluded;
    this.bundlePlanMessage = res.messages;
    let bundlePlan: any[] = res.bundleNameFilePathUrl;
    let downloadUrl: any = this.distApi + res.postEach;
    let tempData: any[] = [];

    for (let bundle of bundlePlan) {
      this.zipData.push({ "fileName": bundle.bundleName, "downloadProgress": 0, "downloadStatus": null, "downloadInstance": null, "bundle": bundle, "downloadUrl": downloadUrl, "downloadErrorMessage": "" });
    }

    // Associate zipData with files
    for (let zip of this.zipData) {
      for (let includeFile of zip.bundle.includeFiles) {
        let filePath = includeFile.filePath.substring(includeFile.filePath.indexOf('/'));
        let treeNode = this.downloadService.searchTreeByfilePath(this.treeRoot[0], filePath);
        if (treeNode != null) {
          treeNode.data.zipFile = zip.fileName;
        }
      }
    }

    this.downloadService.downloadNextZip(this.zipData, this.treeRoot[0], "datacard");

    // Start downloading the first one, this will set the downloaded zip file to 1
    this.subscriptions.push(this.downloadService.watchDownloadingNumber("datacard").subscribe(
      value => {
        if (!this.cancelAllDownload) {
          this.downloadService.downloadNextZip(this.zipData, this.treeRoot[0], "datacard");
          // files.data.downloadProgress = Math.round(100*this.downloadService.getDownloadedNumber(this.zipData) / this.zipData.length);
          // if(this.downloadService.allDownloadFinished(this.zipData)){
          //     files.data.downloadStatus = 'downloaded';
          //     this.downloadStatus = 'downloaded';
          // }
        }

        // this.updateDownloadStatus(this.files);
      }
    ));
  }

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
  }

  resetDownloadParams() {
    this.downloadService.setDownloadingNumber(0, "datacard");
    this.zipData = [];
    this.downloadStatus = null;
    this.cancelAllDownload = true;
    this.displayDownloadFiles = false;
    this.downloadService.resetZipName(this.treeRoot[0]);
    this.bundlePlanMessage = null;
    this.bundlePlanStatus = null;
    this.bundlePlanUnhandledFiles = null;
  }

  downloadOneFile(rowData: any) {
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
          this.cartService.updateCartItemDownloadStatus(rowData.cartId, 'downloaded');
          this.downloadService.setFileDownloadedFlag(true);
          break;
        case HttpEventType.DownloadProgress:
          rowData.downloadProgress = Math.round(100 * event.loaded / event.total);
          break;
      }
    })
  }
  /**
   *  download zip file
   */
  // downloadZIP() {
  //     let downloadURL: string[];
  //     let fileName: string[];
  //     let params = new HttpParams();
  //     let folderName: string;
  //     this.showSpinner = true;
  //     let downloadData: DownloadData[] = [];
  //     let existItem: any;
  //     this.displayDownloadFiles = true;
  //     var i:number;

  //     for ( i=0; i < this.dataFiles.length;i++) {
  //         if (this.dataFiles[i].expanded == true) {
  //             this.selectedParentIndex = i;
  //         }
  //     }

  //     for (let selData of this.selectedData) {
  //         if (selData.data['resFilePath'] != null && selData.data['resFilePath'] != undefined) {
  //             if (selData.data['resFilePath'].split(".").length > 1) {
  //                 existItem = downloadData.filter(item => item.filePath === this.ediid+selData.data['resFilePath'] 
  //                     && item.downloadURL === selData.data['downloadURL']);

  //                 if (existItem.length == 0) {
  //                     downloadData.push({"filePath":this.ediid+selData.data['resFilePath'], 'downloadURL':selData.data['downloadURL']});
  //                 }
  //             }
  //         }
  //     }

  //     // for (let selData of this.selectedData) {
  //     //   if (selData.data['filePath'] != null) {
  //     //     if (selData.data['filePath'].split(".").length > 1) {
  //     //       //folderName = selData.data['resId'].split("/")[2] + "-" + selData.data['resTitle'].substring(0, 20);
  //     //       params = params.append('folderName', folderName);
  //     //       params = params.append('downloadURL', selData.data['downloadURL']);
  //     //       params = params.append('fileName', selData.data['resId'] + selData.data['fileName']);
  //     //       params = params.append('filePath', selData.data['filePath']);
  //     //       params = params.append('resFilePath', selData.data['resFilePath']);
  //     //       this.cartService.updateCartItemDownloadStatus(selData.data['resId'],true);
  //     //     }
  //     //   }
  //     // }


  //     // if(params.keys.length !== 0){
  //     var randomnumber = Math.floor(Math.random() * (this.maximum - this.minimum + 1)) + this.minimum;

  //     var downloadFileName = "download" + randomnumber + ".zip";
  //     this["showDownloadFileSpinner"+randomnumber] = true;
  //     this.displayFiles.push({key: downloadFileName, value: this["showDownloadFileSpinner"+randomnumber]});

  //     const req = new HttpRequest('GET', 'https://s3.amazonaws.com/nist-midas/1858/RawCameraData.zip', {
  //     reportProgress: true, responseType: 'blob'
  //     });

  //     this.downloadStatus = 'downloading';
  //     this.downloadInstance = this.http.request(req).subscribe(event => {
  //         switch (event.type) {
  //             case HttpEventType.Response:
  //                 this.downloadStatus = 'downloaded';
  //                 this.downloadProgress = 0;
  //                 this.downloadService.saveToFileSystem(event.body, downloadFileName);
  //                 this.showSpinner = false;
  //                 this["showDownloadFileSpinner"+randomnumber] = false;
  //                 this.displayFiles.forEach(function(item) {
  //                     if (item.key === downloadFileName) {
  //                         item.value = this["showDownloadFileSpinner"+randomnumber];
  //                     }
  //                 },1000);

  //                 for (let selData of this.selectedData) {
  //                     if (selData.data['filePath'] != null) {
  //                         //   if (selData.data['filePath'].split(".").length > 1) {
  //                         if (selData.data.children == undefined) {
  //                             this.cartService.updateCartItemDownloadStatus(selData.data['resId'],'downloaded');
  //                         }
  //                     }
  //                 }

  //                 this.updateCartEntries();
  //                 //   this.cartService.getAllCartEntities().then(function (result) {
  //                 //       this.cartEntities = result;
  //                 //       this.createDataCartHierarchy();
  //                 //       if (this.cartEntities.length > 0) {
  //                 //           this.dataFiles[this.selectedParentIndex].expanded = true;
  //                 //       }
  //                 //   }.bind(this), function (err) {
  //                 //       alert("something went wrong while creating the zip file");
  //                 //   });

  //                 this.selectedData.length = 0;
  //                 this.dataFileCount();

  //                 break;
  //             case HttpEventType.DownloadProgress:
  //                 this.downloadProgress = Math.round(100*event.loaded / event.total);
  //                 break;
  //         }
  //     });
  //     //   this.downloadService.postFile(this.distApi + "downloadall", JSON.stringify(downloadData)).subscribe(blob => {
  //     //     this.downloadService.saveToFileSystem(blob, downloadFileName);
  //     //       this.showSpinner = false;
  //     //       this["showDownloadFileSpinner"+randomnumber] = false;
  //     //       this.displayFiles.forEach(function(item) {
  //     //           if (item.key === downloadFileName) {
  //     //               item.value = this["showDownloadFileSpinner"+randomnumber];
  //     //           }
  //     //       },1000);
  //     //   });

  //     //   for (let selData of this.selectedData) {
  //     //     if (selData.data['filePath'] != null) {
  //     //         //   if (selData.data['filePath'].split(".").length > 1) {
  //     //         if (selData.data.children == undefined) {
  //     //               this.cartService.updateCartItemDownloadStatus(selData.data['resId'],'downloaded');
  //     //         }
  //     //       }
  //     //   }

  //     //   this.cartService.getAllCartEntities().then(function (result) {
  //     //       this.cartEntities = result;
  //     //       this.createDataCartHierarchy();
  //     //       if (this.cartEntities.length > 0) {
  //     //           this.dataFiles[this.selectedParentIndex].expanded = true;
  //     //       }
  //     //   }.bind(this), function (err) {
  //     //       alert("something went wrong while creating the zip file");
  //     //   });

  //     //   this.selectedData.length = 0;
  //     //   this.dataFileCount();
  //     // }
  // }

  // cancelDownload(key){
  //     this.downloadInstance.unsubscribe();
  //     this.downloadInstance = null;
  //     this.downloadProgress = 0;
  //     this.downloadStatus = null;
  //     this.showSpinner = false;
  //     this.displayFiles = this.displayFiles.filter(obj => obj.key != key);
  // }

  cancelDownload(rowData: any) {
    rowData.downloadInstance.unsubscribe();
    rowData.downloadInstance = null;
    rowData.downloadProgress = 0;
    rowData.downloadStatus = null;
  }

  /**
   * count the selected files
   */

  dataFileCount() {
    this.selectedFileCount = 0;
    for (let selData of this.selectedData) {
      if (selData.data['filePath'] != null) {
        if (selData.data['filePath'].split(".").length > 1) {
          this.selectedFileCount++;
        }
      }
    }

    if (this.selectedFileCount > 0) {
      // var element = <HTMLInputElement> document.getElementById("download");
      // element.disabled = false;
      // element = <HTMLInputElement> document.getElementById("removeData");
      // element.disabled = false;
    } else {
      //var element = <HTMLInputElement> document.getElementById("download");
      //element.disabled = true;
      //element = <HTMLInputElement> document.getElementById("removeData");
      //element.disabled = true;
    }

  }

  /**
   * Update cart entries
   */
  //   updateCartEntries(row:any,downloadStatus:any) {
  updateCartEntries() {
    // console.log("id" + JSON.stringify(row.data));
    // this.cartService.updateCartItemDownloadStatus(row.data['resId'],ownloadStatus);
    this.cartService.getAllCartEntities().then(function (result) {
      this.cartEntities = result;
      this.createDataCartHierarchy();
    }.bind(this), function (err) {
      alert("something went wrong while fetching the products");
    });

  }

  /**
   * display spinner
   */
  showLoadingSpinner() {
    this.showSpinner = true;
  }

  /**
   * hide spinner
   */
  hideLoadingSpinner() {
    this.showSpinner = false;
  }

  /**
   * Removes all cart Instances that are bound to the given id.
   **/
  removeByDataId() {

    let dataId: any;
    // convert the map to an array
    // var i:number;
    // for ( i=0; i < this.dataFiles.length;i++) {
    //     if (this.dataFiles[i].expanded == true) {
    //         this.selectedParentIndex = i;
    //     }
    // }
    for (let selData of this.selectedData) {
      dataId = selData.data['resId'];
      // Filter out all cartEntities with given productId,  finally the new stuff from es6 can be used.
      this.cartEntities = this.cartEntities.filter(entry => entry.data.resId != dataId);
      //save to localStorage
      this.cartService.saveListOfCartEntities(this.cartEntities);
    }
    this.getDataCartList();
    this.createDataCartHierarchy();

    // if (this.cartEntities.length > 0) {
    //     this.dataFiles[this.selectedParentIndex].expanded = true;
    // }

    this.cartService.setCartLength(this.cartEntities.length);
    this.selectedData.length = 0;
    this.dataFileCount();
    this.expandToLevel(this.dataFiles, true, 1);
  }

  /**
   * Removes all cart Instances that are bound to the download status.
   **/
  removeByDownloadStatus() {
    let dataId: any;
    // convert the map to an array
    this.cartService.removeByDownloadStatus();
    this.updateCartEntries();
    this.cartService.setCartLength(this.cartEntities.length);
    setTimeout(() => {
      this.expandToLevel(this.dataFiles, true, null);
    }, 0);
    this.isVisible = false;
    setTimeout(() => {
      this.isVisible = true;
    }, 0);
    //   this.cartService.getAllCartEntities().then(function (result) {
    //       this.cartEntities = result;
    //       this.createDataCartHierarchy();
    //       if (this.cartEntities.length > 0) {
    //           this.dataFiles[this.selectedParentIndex].expanded = true;
    //       }
    //       this.cartService.setCartLength(this.cartEntities.length);
    //     }.bind(this), function (err) {
    //         alert("something went wrong while removing item");
    //     });
  }

  resetDatafileDownloadStatus(dataFiles: any, downloadStatus: any) {
    for (let i = 0; i < dataFiles.length; i++) {
      if (dataFiles[i].children.length > 0) {
        // console.log("expandAll again:");
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
    //console.log("datafiles" + this.dataFiles.length);

  }

  /**
   * Create Data hierarchy for the tree
   */
  createDataCartHierarchy() {
    console.log("creating DataCartHierarchy this.cartEntities");
    console.log(this.cartEntities);
    let arrayList = this.cartEntities.reduce(function (result, current) {
      result[current.data.resTitle] = result[current.data.resTitle] || [];
      result[current.data.resTitle].push(current);
      return result;
    }, {});

    var noFileDownloadedFlag = true;
    this.dataFiles = [];
    this.totalDownloaded = 0;
    let parentObj: TreeNode = {};

    // console.log("this.cartEntities:");
    // console.log(this.cartEntities);
    // console.log("arrayList:");
    // console.log(arrayList);

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
              // console.log("##$%$%$ path path:" +fpath[path]);
              /// Added this code to avoid the issue of extra file layers in the datacart
              if (fpath[path] !== "") {
                child2 = this.createDataCartChildrenTree(
                  "/" + fpath[path],
                  fields.data.cartId,
                  resId, ediid,
                  fpath[path],
                  fields.data.downloadURL,
                  fields.data.filePath,
                  fields.data.downloadStatus,
                  fields.data.mediatype,
                  fields.data.description,
                  fields.data.filetype,
                  fields.data.isSelected
                );
                parent.children.push(child2);

                parent = child2;
              }
              if (key == 'Measurement of the Behavior of Steel Beams under Localized Fire Exposure' && parent.parent != null)
                this.selectedData.push(parent);
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
  createDataCartChildrenTree(path: string, cartId: string, resId: string, ediid: string, resTitle: string, downloadURL: string, resFilePath: string, downloadStatus: string, mediatype: string, description: string, filetype: string, isSelected: boolean) {
    let child1: TreeNode = {};
    child1 = {
      data: {
        'filePath': path,
        'cartId': cartId,
        'resId': resId,
        'ediid': ediid,
        'resTitle': resTitle,
        'downloadURL': downloadURL,
        'resFilePath': resFilePath,
        'downloadStatus': downloadStatus,
        'mediatype': mediatype,
        'description': description,
        'filetype': filetype,
        'isSelected': isSelected
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

  isNodeSelected: boolean = false;
  openDetails(event, fileNode: TreeNode, overlaypanel: OverlayPanel) {
    this.isNodeSelected = true;
    this.fileNode = fileNode;
    overlaypanel.hide();
    setTimeout(() => {
      overlaypanel.show(event);
    }, 100);
  }

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

  onNodeSelection(event: any, rowData: any, rowIndex: any) {
    console.log("rowData");
    console.log(rowData);
    console.log("rowIndex");
    console.log(rowIndex);

    if (rowData.children) {
      // for (let child of rowData.children)
      // this.setSelected(child);
    }
  }

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
}