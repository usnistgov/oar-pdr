import { Component, Input, ChangeDetectorRef, NgZone } from '@angular/core';
import { TreeNode } from 'primeng/api';
import { CartService } from '../../datacart/cart.service';
import { Data } from '../../datacart/data';
import { OverlayPanel } from 'primeng/overlaypanel';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { ConfirmationService } from 'primeng/primeng';
import { DownloadData } from '../../shared/download-service/downloadData';
import { ZipData } from '../../shared/download-service/zipData';
import { CommonVarService } from '../../shared/common-var';
import { HttpClient, HttpRequest, HttpEventType } from '@angular/common/http';
import { AppConfig } from '../../config/config';
import { FileSaverService } from 'ngx-filesaver';
import { Router } from '@angular/router';
import { CommonFunctionService } from '../../shared/common-function/common-function.service';
import { TaxonomyListService } from '../../shared/taxonomy-list';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { SearchTopicsComponent } from '../../landing/search-topics/search-topics.component';
import { DescriptionPopupComponent } from './description-popup/description-popup.component';
import { CustomizationServiceService } from '../../shared/customization-service/customization-service.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';

declare var _initAutoTracker: Function;

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
  @Input() recordEditmode: boolean;
  @Input() inBrowser: boolean;   // false if running server-side

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
  messageColor: any;
  noFileDownloaded: boolean; // will be true if any item in data cart is downloaded
  distApi: string;
  isLocalProcessing: boolean;
  showDownloadProgress: boolean = false;
  mobWidth: number = 800;   // default value used in server context
  mobHeight: number = 900;  // default value used in server context
  fontSize: string;
  descriptionObj: any;
  topicObj: any;
  tempTopics: string[] = [];
  keywordObj: any;
  defaultText: string = "Enter description here...";
  taxonomyList: any[];
  errorMsg: any;
  taxonomyTree: TreeNode[] = [];
  selectedData: TreeNode[] = [];
  isVisible: boolean = true;
  updateUrl: string;

  /* Function to Return Keys object properties */
  keys(): Array<string> {
    return Object.keys(this.fileDetails);
  }

  constructor(private cartService: CartService,
    private cdr: ChangeDetectorRef,
    private downloadService: DownloadService,
    private commonVarService: CommonVarService,
    private http: HttpClient,
    private cfg: AppConfig,
    private _FileSaverService: FileSaverService,
    private confirmationService: ConfirmationService,
    private commonFunctionService: CommonFunctionService,
    private taxonomyListService: TaxonomyListService,
    private ngbModal: NgbModal,
    private gaService: GoogleAnalyticsService,
    public router: Router,
    private customizationServiceService: CustomizationServiceService,
    ngZone: NgZone) {
    this.cols = [
      { field: 'name', header: 'Name', width: '60%' },
      { field: 'mediatype', header: 'Media Type', width: 'auto' },
      { field: 'size', header: 'Size', width: 'auto' },
      { field: 'download', header: 'Status', width: 'auto' }];

    if (typeof (window) !== 'undefined') {
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
    }

    this.cartService.watchAddAllFilesCart().subscribe(value => {
      this.addAllFileSpinner = value;
    });
    this.cartService.watchStorage().subscribe(value => {
      this.cartLength = value;
    });
    this.commonVarService.watchRefreshTree().subscribe(value => {
      this.visible = false;
      setTimeout(() => {
        this.visible = true;
      }, 0);
    });

    this.commonVarService.watchForceLandingPageInit().subscribe(value => {
      if (value) {
        this.cartMap = this.cartService.getCart();
        this.allSelected = this.updateAllSelectStatus(this.files);
        this.cartLength = this.cartService.getCartSize();
      }
    });
    this.descriptionObj = this.editingObjectInit();
    this.topicObj = this.editingObjectInit();
    this.keywordObj = this.editingObjectInit();
  }

  ngOnInit() {
    this.distApi = this.cfg.get("distService", "/od/ds/");
    // if (this.files.length != 0)
    //   this.files = <TreeNode[]>this.files[0].data;


    // this.fileNode = { "data": { "name": "", "size": "", "mediatype": "", "description": "", "filetype": "" } };

    this.cartMap = this.cartService.getCart();
    this.ediid = this.commonVarService.getEdiid();
    this.updateUrl = this.cfg.get("distService", "/rmm/") + "update/" + this.ediid;

    this.taxonomyListService.get(0).subscribe((result) => {
      if (result != null && result != undefined)
        this.buildTaxonomyTree(result);

      this.taxonomyList = [];
      for (var i = 0; i < result.length; i++) {
        this.taxonomyList.push({ "taxonomy": result[i].label });
      }
    }, (error) => {
      console.log("There is an error getting taxonomy list.");
      console.log(error);
      this.errorMsg = error;
    });

    // const newPart = {
    //   data: {
    //     cartId: "/",
    //     ediid: this.ediid,
    //     name: "files",
    //     mediatype: "",
    //     size: null,
    //     downloadUrl: null,
    //     description: null,
    //     filetype: null,
    //     resId: "/",
    //     filePath: "/",
    //     downloadProgress: 0,
    //     downloadInstance: null,
    //     isIncart: false,
    //     zipFile: null,
    //     message: ''
    //   }, children: []
    // };
    // newPart.children = this.files;
    // this.treeRoot.push(newPart);
    // this.updateStatusFromCart();
    // this.allSelected = this.updateAllSelectStatus(this.files);
    // this.downloadStatus = this.updateDownloadStatus(this.files) ? "downloaded" : null;
    // this.totalFiles = 0;
    // this.getTotalFiles(this.files);

    // this.buildTree();
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


  ngOnChanges() {
    this.checkAccesspages();
    this.buildTree();
  }

  buildTree(){
    if (this.files.length != 0)
      this.files = <TreeNode[]>this.files[0].data;

    this.fileNode = { "data": { "name": "", "size": "", "mediatype": "", "description": "", "filetype": "" } };

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
        resId: "/",
        filePath: "/",
        downloadProgress: 0,
        downloadInstance: null,
        isIncart: false,
        zipFile: null,
        message: ''
      }, children: []
    };
    newPart.children = this.files;
    this.treeRoot.push(newPart);
    this.updateStatusFromCart();
    this.allSelected = this.updateAllSelectStatus(this.files);
    this.downloadStatus = this.updateDownloadStatus(this.files) ? "downloaded" : null;
    this.totalFiles = 0;
    this.getTotalFiles(this.files);

  }

  /*
  *   build taxonomy tree
  */
  buildTaxonomyTree(result: any) {
    let allTaxonomy: any = result;
    var tempTaxonomyTree = {}
    if (result != null && result != undefined) {
      tempTaxonomyTree["data"] = this.arrangeIntoTree(result);
      this.taxonomyTree.push(tempTaxonomyTree);
    }

    this.taxonomyTree = <TreeNode[]>this.taxonomyTree[0].data;
  }

  private arrangeIntoTree(paths) {
    const tree = [];
    paths.forEach((path) => {
      var fullpath: string;
      if (path.parent != null && path.parent != undefined && path.parent != "")
        fullpath = path.parent + ":" + path.label;
      else
        fullpath = path.label;

      const pathParts = fullpath.split(':');
      let currentLevel = tree; // initialize currentLevel to root

      for (var j = 0; j < pathParts.length; j++) {
        let tempId: string = '';
        for (var k = 0; k < j + 1; k++) {
          tempId = tempId + pathParts[k];
          // tempId = tempId + pathParts[k].replace(/ /g, "");
          if (k < j) {
            tempId = tempId + ": ";
          }
        }

        // check to see if the path already exists.
        const existingPath = currentLevel.filter(level => level.data.treeId === tempId);
        if (existingPath.length > 0) {
          // The path to this item was already in the tree, so don't add it again.
          // Set the current level to this path's children  
          currentLevel = existingPath[0].children;
        } else {
          let newPart = null;
          newPart = {
            data: {
              treeId: tempId,
              name: pathParts[j],
              // name: pathParts[j].replace(/ /g, ""),
              researchTopic: tempId,
              bkcolor: 'white'
            }, children: [],
            expanded: false
          };
          currentLevel.push(newPart);
          currentLevel = newPart.children;
          // }
        }
      };
    });
    return tree;
  }

  /*
  *   Init object - edit buttons for animation purpose
  */
  editingObjectInit() {
    var editingObject = {
      "originalValue": '',
      "detailEditmode": false,
      "buttonOpacity": 0,
      "borderStyle": "0px solid lightgrey",
      "currentState": 'initial'
    }

    return editingObject;
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
        // comp.data.downloadStatus = null;
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
    return this.commonFunctionService.formatBytes(bytes, numAfterDecimal);
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
          this.updateStatusFromCart();
          this.allSelected = this.updateAllSelectStatus(this.files);
          this.downloadStatus = this.updateDownloadStatus(this.files) ? "downloaded" : null;
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
        this.cartService.setForceDatacartReload(true);
        this.allSelected = this.updateAllSelectStatus(this.files);
        if (mode == 'popup') {
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
      'isSelected': isSelected,
      'message': rowData.message
    };

    this.cartService.addDataToCart(data).then(function (result) {
      if (mode != 'popup')
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
    if (!rowData.isLeaf) {
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
    // Google Analytics code to track download event
    this.gaService.gaTrackEvent('download', undefined, 'Resource title: ' + this.record['title'], rowData.downloadUrl);

    rowData.downloadStatus = 'downloaded';
    this.cartService.updateCartItemDownloadStatus(rowData.cartId, 'downloaded');
    this.downloadStatus = this.updateDownloadStatus(this.files) ? "downloaded" : null;
    if (rowData.isIncart) {
      this.downloadService.setFileDownloadedFlag(true);
    }


  }

  /**
  * Function to cancel current download.
  **/
  // cancelDownload(rowData: any) {
  //   if (!rowData.isLeaf) {
  //     this.cancelDownloadAll();
  //     rowData.downloadProgress = 0;
  //     rowData.downloadStatus = null;
  //   } else {
  //     rowData.downloadInstance.unsubscribe();
  //     rowData.downloadInstance = null;
  //     rowData.downloadProgress = 0;
  //     rowData.downloadStatus = null;
  //   }
  // }

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
        // Google Analytics tracking code
        console.log("Tracking download all");
        this.gaService.gaTrackEvent('download', undefined, 'all files', this.record['title']);

        setTimeout(() => {
          let popupWidth: number = this.mobWidth * 0.8;
          let left: number = this.mobWidth * 0.1;
          let screenSize = 'height=880,width=' + popupWidth.toString() + ',top=100,left=' + left.toString();
          window.open('/datacart/popup', 'DownloadManager', screenSize);
          this.cancelAllDownload = false;
          this.downloadFromRoot();
        }, 0);
      },
      reject: () => {
      }
    });
  }

  /**
  * Function to download all.
  **/
  downloadFromRoot() {
    this.cartService.setCurrentCart('landing_popup');
    this.commonVarService.setLocalProcessing(true);
    setTimeout(() => {
      this.cartService.clearTheCart();
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
  * Cancel download certain zip file
  **/
  // cancelDownloadZip(zip: any) {
  //   zip.downloadInstance.unsubscribe();
  //   zip.downloadInstance = null;
  //   zip.downloadProgress = 0;
  //   zip.downloadStatus = "cancelled";
  // }

  /**
  * Cancel download all
  **/
  // cancelDownloadAll() {
  //   for (let zip of this.zipData) {
  //     if (zip.downloadInstance != null) {
  //       zip.downloadInstance.unsubscribe();
  //     }
  //     zip.downloadInstance = null;
  //     zip.downloadProgress = 0;
  //     zip.downloadStatus = null;
  //   }

  //   for (let sub of this.subscriptions) {
  //     sub.unsubscribe();
  //   }

  //   this.downloadService.setDownloadingNumber(0, "landingPage");
  //   this.zipData = [];
  //   this.downloadStatus = null;
  //   this.cancelAllDownload = true;
  //   this.displayDownloadFiles = false;
  //   this.downloadService.resetZipName(this.treeRoot[0]);
  //   this.bundlePlanMessage = null;
  //   this.bundlePlanStatus = null;
  //   this.bundlePlanUnhandledFiles = null;
  // }

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
  * Return color based on different bundlePlan response status
  **/
  // getColor() {
  //   if (this.bundlePlanStatus == 'warnings') {
  //     return "darkorange";
  //   } else if (this.bundlePlanStatus == 'error') {
  //     return "red";
  //   } else {
  //     return "black";
  //   }
  // }

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

  /*
* Following functions set tree table style
*/
  titleStyleHeader() {
    return { 'background-color': '#1E6BA1', 'width': this.cols[0].width, 'color': 'white', 'font-size': this.fontSize };
  }

  typeStyleHeader() {
    return { 'background-color': '#1E6BA1', 'width': this.cols[1].width, 'color': 'white', 'font-size': this.fontSize };
  }

  sizeStyleHeader() {
    return { 'background-color': '#1E6BA1', 'width': this.cols[2].width, 'color': 'white', 'font-size': this.fontSize };
  }

  statusStyleHeader() {
    return { 'background-color': '#1E6BA1', 'width': this.cols[3].width, 'color': 'white', 'font-size': this.fontSize, 'white-space': 'nowrap' };
  }

  titleStyle() {
    return { 'width': this.cols[0].width, 'font-size': this.fontSize };
  }

  typeStyle() {
    return { 'width': this.cols[1].width, 'font-size': this.fontSize };
  }

  sizeStyle() {
    return { 'width': this.cols[2].width, 'font-size': this.fontSize };
  }

  statusStyle() {
    return { 'width': this.cols[3].width, 'font-size': this.fontSize };
  }

  setWidth(mobWidth: number) {
    if (mobWidth > 1340) {
      this.cols[0].width = '60%';
      this.cols[1].width = '20%';
      this.cols[2].width = '15%';
      this.cols[3].width = '100px';
      this.fontSize = '16px';
    } else if (mobWidth > 780 && this.mobWidth <= 1340) {
      this.cols[0].width = '60%';
      this.cols[1].width = '170px';
      this.cols[2].width = '100px';
      this.cols[3].width = '100px';
      this.fontSize = '14px';
    }
    else {
      this.cols[0].width = '50%';
      this.cols[1].width = '20%';
      this.cols[2].width = '20%';
      this.cols[3].width = '10%';
      this.fontSize = '12px';
    }
  }

  /*
  * Make sure the width of popup dialog is less than 500px or 80% of the window width
  */
  getDialogWidth() {
    var w = window.innerWidth > 500 ? 500 : window.innerWidth;
    console.log(w);
    return w + 'px';
  }

  /*
  *   Open Description popup modal
  */
  openDescriptionModal() {
    let i: number;
    let tempDecription: string;

    if (this.record['description'] != null && this.record['description'] != undefined) {
      tempDecription = this.record['description'][0];
      for (i = 1; i < this.record['description'].length; i++) {
        tempDecription = tempDecription + '\r\n\r\n' + this.record['description'][i];
      }
    }

    let ngbModalOptions: NgbModalOptions = {
      backdrop: 'static',
      keyboard: false,
      windowClass: "myCustomModalClass"
    };

    const modalRef = this.ngbModal.open(DescriptionPopupComponent, ngbModalOptions);
    modalRef.componentInstance.tempDecription = tempDecription;
    modalRef.componentInstance.title = 'Description';

    modalRef.componentInstance.returnDescription.subscribe((returnValue) => {
      if (returnValue) {
        var tempDescs = returnValue.split(/\n\s*\n/).filter(desc => desc != '');
        this.record['description'] = JSON.parse(JSON.stringify(tempDescs));

        var postMessage: any = {};
        postMessage["description"] = tempDescs;
        console.log("postMessage", JSON.stringify(postMessage));

        this.customizationServiceService.update(this.updateUrl, JSON.stringify(postMessage)).subscribe(
          blob => {
            console.log("blob:", blob);
          },
          err => {
            console.log("Error when updating description:", err);
          });
      }
    })
  }

  /*
*   Open Description popup modal
*/
  openKeywordModal() {
    let i: number;
    let tempDecription: string = "";

    if (this.checkKeywords()) {
      tempDecription = this.record['keyword'][0];
      for (i = 1; i < this.record['keyword'].length; i++) {
        tempDecription = tempDecription + ',' + this.record['keyword'][i];
      }
    }
    console.log('tempDecription', tempDecription);

    let ngbModalOptions: NgbModalOptions = {
      backdrop: 'static',
      keyboard: false,
      windowClass: "myCustomModalClass"
    };

    const modalRef = this.ngbModal.open(DescriptionPopupComponent, ngbModalOptions);
    modalRef.componentInstance.tempDecription = tempDecription;
    modalRef.componentInstance.title = 'Subject Keywords';

    modalRef.componentInstance.returnDescription.subscribe((returnValue) => {
      if (returnValue) {
        let keywords: string[];
        keywords = returnValue.split(',').filter(keyword => keyword != '');
        this.record['keyword'] = keywords;

        var postMessage: any = {};
        postMessage["description"] = keywords;
        console.log("postMessage", JSON.stringify(postMessage));

        this.customizationServiceService.update(this.updateUrl, JSON.stringify(postMessage)).subscribe(
          blob => {
            console.log("blob:", blob);
          },
          err => {
            console.log("Error when updating description:", err);
          });
      }
    });
  }

  /*
  *   Open Topic popup modal
  */
  openTopicModal() {
    this.tempTopics = [];
    if (this.record['topic'] != null && this.record['topic'].length > 0) {
      for (var i = 0; i < this.record['topic'].length; i++) {
        this.tempTopics.push(this.record['topic'][i].tag);
      }
    }

    let ngbModalOptions: NgbModalOptions = {
      backdrop: 'static',
      keyboard: false,
      windowClass: "myCustomModalClass"
    };

    const modalRef = this.ngbModal.open(SearchTopicsComponent, ngbModalOptions);
    modalRef.componentInstance.tempTopics = this.tempTopics;
    modalRef.componentInstance.recordEditmode = this.recordEditmode;
    modalRef.componentInstance.taxonomyTree = this.taxonomyTree;
    modalRef.componentInstance.passEntry.subscribe((topics) => {
      if (topics) {
        var strtempTopics: string = '';
        var tempTopicsForUpdate: any = [];
        var lTempTopics: any[] = [];

        for (var i = 0; i < topics.length; ++i) {
          strtempTopics = strtempTopics + topics[i];
          lTempTopics.push({ '@type': 'Concept', 'scheme': 'https://www.nist.gov/od/dm/nist-themes/v1.0', 'tag': topics[i] });
          tempTopicsForUpdate.push({ 'tag': topics[i] });
        }
        this.record['topic'] = JSON.parse(JSON.stringify(lTempTopics));

        var postMessage: any = {};
        postMessage["topic"] = tempTopicsForUpdate;
        console.log("postMessage", JSON.stringify(postMessage));

        this.customizationServiceService.update(this.updateUrl, JSON.stringify(postMessage)).subscribe(
          blob => {
            console.log("blob:", blob);
          },
          err => {
            console.log("Error when updating title:", err);
          });
      }
    })
  }

  /*
  *   Return border style
  */
  getBorder() {
    if (this.recordEditmode)
      return { 'border': '1px solid lightgrey' };
    else
      return { 'border': '0px solid lightgrey' };
  }
}
