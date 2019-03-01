import { Component, Input, ChangeDetectorRef } from '@angular/core';
import { TreeNode } from 'primeng/api';
import { CartService } from '../../datacart/cart.service';
import { Data } from '../../datacart/data';
import { OverlayPanel } from 'primeng/overlaypanel';
import { stringify, error } from '@angular/compiler/src/util';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { SelectItem, DropdownModule, ConfirmationService, Message } from 'primeng/primeng';
import { DownloadData } from '../../shared/download-service/downloadData';
import { ZipData } from '../../shared/download-service/zipData';
import { CommonVarService } from '../../shared/common-var';
import { environment } from '../../../environments/environment';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse, HttpEvent } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { AppConfig, Config } from '../../shared/config-service/config.service';
import { THIS_EXPR } from '@angular/compiler/src/output/output_ast';
import { FileSaverService } from 'ngx-filesaver';
import { v } from '@angular/core/src/render3';
import { Router } from '@angular/router';

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

  addAllFileSpinner: boolean = false;
  fileDetails: string = '';
  isFileDetails: boolean = false;
  isReference: boolean = false;
  selectedFile: TreeNode;
  isAccessPage: boolean = false;
  accessPages: Map<string, string> = new Map();
  accessUrls: string[] = [];
  accessTitles: string[] = [];
  isReferencedBy: boolean = false;
  isDocumentedBy: boolean = false;
  selectedNodes: TreeNode[];
  addFileStatus: boolean = false;
  selectedNode: TreeNode;
  cols: any[];
  fileNode: TreeNode;
  displayDownloadFiles: boolean = false;
  cartMap: any[];
  allSelected: boolean = false;
  allDownloaded: boolean = false;
  ediid: any;
  downloadStatus: any = null;
  totalFiles: any;
  downloadData: DownloadData[];
  zipData: ZipData[] = [];
  isExpanded: boolean = false;
  visible: boolean = true;
  cancelAllDownload: boolean = false;
  cartLength: number;
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
  distApi: string;
  confValues: Config;
  isLocalProcessing: boolean;
  showDownloadProgress: boolean = false;

  /* Function to Return Keys object properties */
  keys(): Array<string> {
    return Object.keys(this.fileDetails);
  }

  constructor(private cartService: CartService,
    private cdr: ChangeDetectorRef,
    private downloadService: DownloadService,
    private commonVarService: CommonVarService,
    private http: HttpClient,
    private appConfig: AppConfig,
    private _FileSaverService: FileSaverService,
    private confirmationService: ConfirmationService,
    public router: Router) {
    this.cartService.watchAddAllFilesCart().subscribe(value => {
      this.addAllFileSpinner = value;
    });
    this.cartService.watchStorage().subscribe(value => {
      this.cartLength = value;
    });
    this.commonVarService.watchForceLandingPageInit().subscribe(value => {
      if (value) {
        this.cartMap = this.cartService.getCart();
        this.allSelected = this.updateAllSelectStatus(this.files);
        this.cartLength = this.cartService.getCartSize();
      }
    });
    this.confValues = this.appConfig.getConfig();
  }

  ngOnInit() {
    this.distApi = this.confValues.DISTAPI;

    if (this.files.length != 0)
      this.files = <TreeNode[]>this.files[0].data;
    this.cols = [
      { field: 'name', header: 'Name', width: '60%' },
      { field: 'mediatype', header: 'MediaType', width: '150px' },
      { field: 'size', header: 'Size', width: '80px' },
      { field: 'download', header: 'Download', width: '80px' }];

    this.fileNode = { "data": { "name": "", "size": "", "mediatype": "", "description": "", "filetype": "" } };

    this.cartMap = this.cartService.getCart();
    this.ediid = this.commonVarService.getEdiid();

    const newPart = {
      data: {
        cartId: "/",
        ediid: this.ediid,
        name: "files",
        mediatype: "",
        size: null,
        downloadUrl: null,
        description: null,
        filetype: null,
        resId: "files",
        filePath: "/",
        downloadProgress: 0,
        downloadInstance: null,
        isIncart: false,
        zipFile: null
      }, children: []
    };
    newPart.children = this.files;
    this.treeRoot.push(newPart);
    this.updateStatusFromCart();
    this.allSelected = this.updateAllSelectStatus(this.files);
    this.downloadStatus = this.updateDownloadStatus(this.files) ? "downloaded" : null;
    this.totalFiles = 0;
    this.getTotalFiles(this.files);

    this.downloadService.watchDownloadProcessStatus("landingPage").subscribe(
      value => {
        this.allProcessed = value;
        if (this.allProcessed) {
          this.downloadStatus = "downloaded";
        }
        this.downloadStatus = this.updateDownloadStatus(this.files) ? "downloaded" : null;
      }
    );
    this.downloadService.watchAnyFileDownloaded().subscribe(
      value => {
        this.noFileDownloaded = !value;
      }
    );
  }

  /**
   * Function to expand tree display to certain level
   */
  expandToLevel(dataFiles: any, option: boolean, targetLevel: any) {
    this.expandAll(dataFiles, option, 0, targetLevel)
  }

  /**
   * Function to expand tree display to certain level - used by expandToLevel()
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
    this.visible = false;
    setTimeout(() => {
      this.visible = true;
    }, 0);
  }

  /**
   * Function to reset the download status and incart status.
   */
  resetStstus(files: any) {
    for (let comp of files) {
      if (comp.children.length > 0) {
        this.resetStstus(comp.children);
      } else {
        comp.data.isIncart = false;
        comp.data.downloadStatus = null;
      }
    }
    return Promise.resolve(files);
  }

  /**
   * Function to sync the download status from data cart.
   */
  updateStatusFromCart() {
    this.resetStstus(this.files);

    for (let key in this.cartMap) {
      let value = this.cartMap[key];
      if (value.data.downloadStatus != undefined) {
        this.setFilesDownloadStatus(this.files, value.data.cartId, value.data.downloadStatus);
      }
      if (value.data.cartId != undefined) {
        let treeNode = this.searchTree(this.treeRoot[0], value.data.cartId);
        if (treeNode != null) {
          treeNode.data.isIncart = true;
        }
      }
    }
    return Promise.resolve(this.files);
  }

  /**
   * Function to get total number of files.
   */
  getTotalFiles(files) {
    for (let comp of files) {
      if (comp.children.length > 0) {
        this.getTotalFiles(comp.children);
      } else {
        this.totalFiles = this.totalFiles + 1;
      }
    }
  }

  /**
   * Function to set files download status.
   */
  setFilesDownloadStatus(files, cartId, downloadStatus) {
    for (let comp of files) {
      if (comp.children.length > 0) {
        this.setFilesDownloadStatus(comp.children, cartId, downloadStatus);
      } else {
        if (comp.data.cartId == cartId) {
          comp.data.downloadStatus = downloadStatus;
        }
      }
    }
  }

  /**
   * Function to Check whether given record has references in it.
   */
  checkReferences() {
    if (Array.isArray(this.record['references'])) {
      for (let ref of this.record['references']) {
        if (ref.refType === 'IsDocumentedBy') this.isDocumentedBy = true;
        if (ref.refType === 'IsReferencedBy') this.isReferencedBy = true;
      }
      if (this.isDocumentedBy || this.isReferencedBy)
        return true;
    }
  }

  /**
   * Function to Check whether record has keyword
   */
  checkKeywords() {
    if (Array.isArray(this.record['keyword'])) {
      if (this.record['keyword'].length > 0)
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
  checkTopics() {
    if (Array.isArray(this.record['topic'])) {
      if (this.record['topic'].length > 0)
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
  checkAccesspages() {
    if (Array.isArray(this.record['inventory'])) {
      if (this.record['inventory'][0].forCollection == "") {
        for (let inv of this.record['inventory'][0].byType) {
          if (inv.forType == "nrdp:AccessPage")
            this.isAccessPage = true;
        }
      }
    }
    if (this.isAccessPage) {
      this.accessPages = new Map();
      for (let comp of this.record['components']) {
        if (comp['@type'].includes("nrdp:AccessPage")) {
          if (comp["title"] !== "" && comp["title"] !== undefined)
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
    if (0 == bytes) return "0 Bytes";
    if (1 == bytes) return "1 Byte";
    var base = 1000,
      e = ["Bytes", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"],
      d = numAfterDecimal || 1,
      f = Math.floor(Math.log(bytes) / Math.log(base));

    var v = bytes / Math.pow(base, f);
    if (f == 0) // less than 1 kiloByte
      d = 0;
    else if (numAfterDecimal == null && v < 10.0)
      d = 2;
    return v.toFixed(d) + " " + e[f];
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

  ngOnChanges() {
    this.checkAccesspages();
  }

  /**
  * Function to add whole subfolder files to data cart then update status
  **/
  addSubFilesToCartAndUpdate(rowData: any, isSelected: boolean) {
    this.addSubFilesToCart(rowData, isSelected).then(function (result: any) {
      this.allSelected = this.updateAllSelectStatus(this.files);
    }.bind(this), function (err) {
      alert("something went wrong while adding file to data cart.");
    });
  }

  /**
  * Function to add whole subfolder files to data cart
  **/
  addSubFilesToCart(rowData: any, isSelected: boolean) {
    if (!rowData.isLeaf) {
      let subFiles: any = null;
      for (let comp of this.files) {
        subFiles = this.searchTree(comp, rowData.cartId);
        if (subFiles != null) {
          break;
        }
      }
      if (subFiles != null) {
        this.addFilesToCart(subFiles.children, isSelected, '');
        rowData.isIncart = true;
      }
    } else {
      this.addtoCart(rowData, isSelected, '');
    }

    return Promise.resolve(rowData);
  }

  /**
  * Function to search the file tree for a given cartid.
  **/
  searchTree(element, cartId) {
    if (element.data.cartId == cartId) {
      return element;
    } else if (element.children.length > 0) {
      var i;
      var result = null;
      for (i = 0; result == null && i < element.children.length; i++) {
        result = this.searchTree(element.children[i], cartId);
      }
      return result;
    }
    return null;
  }

  /**
  * Function to add/remove all files to/from data cart.
  **/
  cartProcess(files: any) {
    this.isLocalProcessing = true;

    setTimeout(() => {
      if (this.allSelected) {
        this.removeFilesFromCart(files).then(function (result1: any) {
          this.isLocalProcessing = false;
        }.bind(this), function (err) {
          alert("something went wrong while removing file from data cart.");
        });
      }
      else {
        this.addAllFilesToCart(files, false, '').then(function (result1: any) {
          this.isLocalProcessing = false;
        }.bind(this), function (err) {
          alert("something went wrong while adding file to data cart.");
        });
      }
    }, 0);

    setTimeout(() => {
      this.isLocalProcessing = false;
    }, 10000);
  }

  /**
  * Function to add all files to data cart.
  **/
  addAllFilesToCart(files: any, isSelected: boolean, mode: string) {
    this.cartService.deselectAll().then(function (result1: any) {
      this.addFilesToCart(files, isSelected, mode).then(function (result2: any) {
        // this.cartService.setForceDatacartReload(true);
        // this.allSelected = this.updateAllSelectStatus(this.files);
        if(mode == 'popup'){
          this.allSelected = true;
        }
      }.bind(this), function (err) {
        alert("something went wrong while adding one file to data cart.");
      });
    }.bind(this), function (err) {
      alert("something went wrong while cleaning up data cart select flag.");
    });
    return Promise.resolve(files);
  }

  /**
  * Function to add given file tree to data cart.
  **/
  addFilesToCart(files: any, isSelected: boolean, mode: string) {
    let data: Data;
    let compValue: any;
    for (let comp of files) {
      if (comp.children.length > 0) {
        compValue += this.addFilesToCart(comp.children, isSelected, mode);
      } else {
        this.addtoCart(comp.data, isSelected, mode).then(function (result) {
          compValue = 1;
        }.bind(this), function (err) {
          alert("something went wrong while adding one file to data cart.");
        });
      }
    }
    //Now reload datacart
    return Promise.resolve(compValue);
  }

  /**
  * Function to add one file to data cart with pre-select option.
  **/
  addtoCart(rowData: any, isSelected: boolean, mode: string) {
    let cartMap: any;
    let data: Data;
    data = {
      'cartId': rowData.cartId,
      'ediid': this.ediid,
      'resId': rowData.resId,
      'resTitle': this.record['title'],
      'resFilePath': rowData.filePath,
      'id': rowData.name,
      'fileName': rowData.name,
      'filePath': rowData.filePath,
      'fileSize': rowData.size,
      'filetype': rowData.filetype,
      'downloadUrl': rowData.downloadUrl,
      'mediatype': rowData.mediatype,
      'downloadStatus': rowData.downloadStatus,
      'description': rowData.description,
      'isSelected': isSelected
    };

    this.cartService.addDataToCart(data).then(function (result) {
      if(mode != 'popup')
        rowData.isIncart = true;
      cartMap = result;
    }.bind(this), function (err) {
      alert("something went wrong while fetching the products");
    });
    return Promise.resolve(cartMap);
  }

  /**
  * Remove one node from cart and set flag
  **/
  removeFromNode(rowData: any) {
    this.removeCart(rowData);
    this.allSelected = this.updateAllSelectStatus(this.files);
  }

  /**
  * Remove one node from cart - can be a file or sub-tree
  **/
  removeCart(rowData: any) {
    if (!this.isFile(rowData)) {
      let subFiles: any = null;
      for (let comp of this.files) {
        subFiles = this.searchTree(comp, rowData.cartId);
        if (subFiles != null) {
          break;
        }
      }
      if (subFiles != null) {
        this.removeFilesFromCart(subFiles.children);
        rowData.isIncart = false;
      }
    } else {
      this.cartService.removeCartId(rowData.cartId);
      rowData.isIncart = false;
    }
  }

  /**
  * Remove all files from cart and set flags
  **/
  removeFilesFromCart(files: any) {
    this.removeFromCart(files);
    this.allSelected = this.updateAllSelectStatus(this.files);
    return Promise.resolve(files);
  }

  /**
  * Remove all files from cart - used by removeFilesFromCart()
  **/
  removeFromCart(files: any) {
    for (let comp of files) {
      if (comp.children.length > 0) {
        comp.data.isIncart = false;
        this.removeFromCart(comp.children);
      } else {
        this.cartService.removeCartId(comp.data.cartId);
        comp.data.isIncart = false;
      }
    }

  }

  /**
  * Check if all chirldren nodes were all selected
  **/
  updateAllSelectStatus(files: any) {
    var allSelected = true;
    for (let comp of files) {
      if (comp.children.length > 0) {
        comp.data.isIncart = this.updateAllSelectStatus(comp.children);
        allSelected = allSelected && comp.data.isIncart;
      } else {
        if (!comp.data.isIncart) {
          this.allSelected = false;
          allSelected = false;
        }
      }
    }
    return allSelected;
  }

  /**
  * Once a file was downloaded, we need to update it's parent's status as well
  **/
  updateDownloadStatus(files: any) {
    var allDownloaded = true;
    var noFileDownloadedFlag = true;
    for (let comp of files) {
      if (comp.children.length > 0) {
        var status = this.updateDownloadStatus(comp.children);
        if (status) {
          comp.data.downloadStatus = 'downloaded';
          this.cartService.updateCartItemDownloadStatus(comp.data.cartId, 'downloaded');
        }
        allDownloaded = allDownloaded && status;
      } else {
        if (comp.data.downloadStatus != 'downloaded') {
          allDownloaded = false;
        }
        if (comp.data.downloadStatus == 'downloaded' && comp.data.isIncart) {
          noFileDownloadedFlag = true;
        }
      }
    }

    this.downloadService.setFileDownloadedFlag(!noFileDownloadedFlag);
    return allDownloaded;
  }

  /**
  * Downloaded one file by id
  **/
  downloadById(id: any) {
    let subFiles: any = null;
    for (let comp of this.files) {
      subFiles = this.searchTree(comp, id);
      if (subFiles != null) {
        break;
      }
    }
    if (subFiles != null) {
      this.downloadAllFilesFromAPI(subFiles);
    }
  }

  /**
  * Downloaded one file
  **/
  downloadOneFile(rowData: any) {
    let filename = decodeURI(rowData.downloadUrl).replace(/^.*[\\\/]/, '');
    rowData.downloadStatus = 'downloading';
    this.showDownloadProgress = true;
    rowData.downloadProgress = 0;
    let url = rowData.downloadUrl.replace('http:', 'https:');

    const req = new HttpRequest('GET', url, {
      reportProgress: true, responseType: 'blob'
    });

    rowData.downloadInstance = this.http.request(req).subscribe(event => {
      switch (event.type) {
        case HttpEventType.Response:
          this._FileSaverService.save(<any>event.body, filename);
          this.showDownloadProgress = false;
          this.setFileDownloaded(rowData);
          break;
        case HttpEventType.DownloadProgress:
          rowData.downloadProgress = Math.round(100 * event.loaded / event.total);
          break;
      }
    })
  }

  /**
  * Function to set status when a file was downloaded
  **/
  setFileDownloaded(rowData: any) {
    rowData.downloadStatus = 'downloaded';
    this.cartService.updateCartItemDownloadStatus(rowData.cartId, 'downloaded');
    this.downloadStatus = this.updateDownloadStatus(this.files) ? "downloaded" : null;
    if (rowData.isIncart) {
      this.downloadService.setFileDownloadedFlag(true);
    }
  }

  /**
  * Function to download a single file based on download url.
  **/
  downloadFile(rowData: any) {
    if (!this.isFile(rowData)) {
      this.downloadById(rowData.cartId);
    } else {
      this.downloadOneFile(rowData);
    };

    rowData.downloadStatus = 'downloaded';
    if (rowData.isIncart) {
      this.downloadService.setFileDownloadedFlag(true);
    }
  }

  /**
  * Function to cancel current download.
  **/
  cancelDownload(rowData: any) {
    if (!this.isFile(rowData)) {
      this.cancelDownloadAll();
      rowData.downloadProgress = 0;
      rowData.downloadStatus = null;
    } else {
      rowData.downloadInstance.unsubscribe();
      rowData.downloadInstance = null;
      rowData.downloadProgress = 0;
      rowData.downloadStatus = null;
    }
  }

  /**
  * Function to download all files based on download url.
  **/
  downloadAllFilesFromUrl(files: any) {
    for (let comp of files) {
      if (comp.children.length > 0) {
        this.downloadAllFilesFromUrl(comp.children);
      } else {
        if (comp.data.downloadUrl) {
          this.downloadOneFile(comp.data);
        }
      }
    }
  }

  /**
  * Function to confirm download all.
  **/
  downloadAllConfirm(header: string, massage: string, key: string) {
    this.confirmationService.confirm({
      message: massage,
      header: header,
      key: key,
      accept: () => {
        setTimeout(() => {
          window.open('/datacart/popup', 'DownloadManager', 'height=880,width=1720,top=100,left=100');
          this.cancelAllDownload = false;
          this.downloadFromRoot();
        }, 0);
      },
      reject: () => {
      }
    });
  }

  downloadFromRoot() {
    this.cartService.setCurrentCart('landing_popup');
    this.commonVarService.setLocalProcessing(true);
    setTimeout(() => {
      this.addAllFilesToCart(this.files, true, 'popup').then(function (result) {
        this.commonVarService.setLocalProcessing(false);
        this.cartService.setCurrentCart('cart');
        this.updateStatusFromCart().then(function (result: any) {
          this.commonVarService.setForceLandingPageInit(true);
        }.bind(this), function (err) {
          alert("something went wrong while adding file to data cart.");
        });
      }.bind(this), function (err) {
        alert("something went wrong while adding all files to cart");
      });
    }, 0);

    setTimeout(() => {
      this.commonVarService.setLocalProcessing(false);
    }, 10000);
  }

  /**
  * Function to download all files from API call.
  **/
  downloadAllFilesFromAPI(files: any) {
    let postMessage: any;
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
    files.data.downloadFileName = zipFileBaseName;
    files.data.downloadStatus = 'downloading';

    postMessage.push({ "bundleName": files.data.downloadFileName, "includeFiles": this.downloadData });
    // now use postMessage to request a bundle plan
    this.downloadService.getBundlePlan(this.distApi + "_bundle_plan", JSON.stringify(postMessage[0])).subscribe(
      blob => {
        this.processBundle(blob, zipFileBaseName, files);
      },
      err => {
        console.log(err);
        this.bundlePlanMessage = err;
        this.bundlePlanStatus = "error";
      }
    );
  }

  /**
  * Process each bundle
  **/
  processBundle(res: any, zipFileBaseName, files: any) {
    this.bundlePlanStatus = res.status.toLowerCase();
    this.messageColor = this.getColor();
    this.bundlePlanUnhandledFiles = res.notIncluded;
    let bundlePlan: any[] = res.bundleNameFilePathUrl;
    let downloadUrl: any = this.distApi + res.postEachTo;
    this.bundlePlanMessage = res.messages;
    let tempData: any[] = [];

    for (let bundle of bundlePlan) {
      this.zipData.push({ "fileName": bundle.bundleName, "downloadProgress": 0, "downloadStatus": null, "downloadInstance": null, "bundle": bundle, "downloadUrl": downloadUrl, "downloadErrorMessage": "" });
    }

    // Associate zipData with files
    for (let zip of this.zipData) {
      for (let includeFile of zip.bundle.includeFiles) {
        let resFilePath = includeFile.filePath.substring(includeFile.filePath.indexOf('/'));
        let treeNode = this.downloadService.searchTreeByfilePath(this.treeRoot[0], resFilePath);
        if (treeNode != null) {
          treeNode.data.zipFile = zip.fileName;
        }
      }
    }

    this.downloadService.downloadNextZip(this.zipData, this.treeRoot[0], "landingPage");

    // Start downloading the first one, this will set the downloaded zip file to 1
    this.subscriptions.push(this.downloadService.watchDownloadingNumber("landingPage").subscribe(
      value => {
        if (!this.cancelAllDownload) {
          this.downloadService.downloadNextZip(this.zipData, this.treeRoot[0], "landingPage");
          files.data.downloadProgress = Math.round(100 * this.downloadService.getDownloadedNumber(this.zipData) / this.zipData.length);
        }

        this.downloadStatus = this.updateDownloadStatus(this.files) ? "downloaded" : null;
      }
    ));
  }

  /**
  * Cancel download certain zip file
  **/
  cancelDownloadZip(zip: any) {
    zip.downloadInstance.unsubscribe();
    zip.downloadInstance = null;
    zip.downloadProgress = 0;
    zip.downloadStatus = "cancelled";
  }

  /**
  * Cancel download all
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

  /**
  * Function to set the download status of all files to downloaded.
  **/
  setAllDownloaded(files: any) {
    for (let comp of files) {
      if (comp.children.length > 0) {
        this.setAllDownloaded(comp.children);
      } else {
        comp.data.downloadStatus = 'downloaded';
        this.cartService.updateCartItemDownloadStatus(comp.data.cartId, 'downloaded');
      }
    }
  }

  /**
  * Function to reset the download status of a file.
  **/
  resetDownloadStatus(rowData) {
    rowData.downloadStatus = null;
    rowData.downloadProgress = 0;
    this.cartService.updateCartItemDownloadStatus(rowData.cartId, null);
    this.allDownloaded = false;
  }

  /**
  * Function to check if a node if leaf.
  **/
  isFile(rowData: any) {
    return rowData.name.match(/\./g) == null ? false : true;
  }

  /**
  * Return color based on different bundlePlan response status
  **/
  getColor() {
    if (this.bundlePlanStatus == 'warnings') {
      return "darkorange";
    } else if (this.bundlePlanStatus == 'error') {
      return "red";
    } else {
      return "black";
    }
  }

  /**
  * Return "download all" button color based on download status
  **/
  getDownloadAllBtnColor() {
    if (this.downloadStatus == null)
      return '#1E6BA1';
    else if (this.downloadStatus == 'downloaded')
      return 'green';
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
  * Return "add all to datacart" button color based on select status
  **/
  getAddAllToDataCartBtnColor() {
    if (this.allSelected)
      return 'green';
    else
      return '#1E6BA1';
  }

  /**
  * Return tooltip text based on select status
  **/
  getCartProcessTooltip() {
    if (this.allSelected)
      return 'Remove all from cart';
    else
      return 'Add all to cart';
  }
}
