import { Component, Input, Output, ChangeDetectorRef, NgZone, EventEmitter } from '@angular/core';
import { TreeNode } from 'primeng/api';
import { CartService } from '../../datacart/cart.service';
import { CartConstants } from '../../datacart/cartconstants';
import { OverlayPanel } from 'primeng/overlaypanel';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { ConfirmationService } from 'primeng/primeng';
import { ZipData } from '../../shared/download-service/zipData';
import { HttpClient, HttpRequest, HttpEventType } from '@angular/common/http';
import { AppConfig } from '../../config/config';
import { FileSaverService } from 'ngx-filesaver';
import { Router } from '@angular/router';
import { CommonFunctionService } from '../../shared/common-function/common-function.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { EditStatusService } from '../editcontrol/editstatus.service';
import { NerdmComp } from '../../nerdm/nerdm';
import { DataCart, DataCartItem } from '../../datacart/cart';
import { DataCartStatus } from '../../datacart/cartstatus';

declare var _initAutoTracker: Function;

@Component({
    moduleId: module.id,
    styleUrls: ['../landing.component.css'],
    selector: 'description-resources',
    templateUrl: `data-files.component.html`,
    providers: [ConfirmationService]
})

export class DataFilesComponent {

    @Input() record: any[];
    @Input() files: TreeNode[];
    @Input() editContent: boolean;
    @Input() metadata: boolean;
    @Input() inBrowser: boolean;   // false if running server-side
    @Input() ediid: string;
    @Input() editEnabled: boolean;    //Disable download all functionality if edit is enabled

    globalDataCart: DataCart;
    specialDataCart: DataCart;
    dataCartStatus: DataCartStatus;

    accessPages: NerdmComp[] = [];
    isReferencedBy: boolean = false;
    isDocumentedBy: boolean = false;
    cols: any[];
    fileNode: TreeNode;
    displayDownloadFiles: boolean = false;
    allSelected: boolean = false;
    allDownloaded: boolean = false;
    downloadStatus: any = null;
    totalFiles: any;
    zipData: ZipData[] = [];
    isExpanded: boolean = false;
    visible: boolean = true;
    cancelAllDownload: boolean = false;
    cartLength: number;
    treeRoot = [];
    showZipFiles: boolean = true;
    allProcessed: boolean = false;
    noFileDownloaded: boolean; // will be true if any item in data cart is downloaded
    isLocalProcessing: boolean;
    showDownloadProgress: boolean = false;
    mobWidth: number = 800;   // default value used in server context
    mobHeight: number = 900;  // default value used in server context
    fontSize: string;
    public CART_CONSTANTS: any = CartConstants.cartConst;

    /* Function to Return Keys object properties */
    //   keys(): Array<string> {
    //     return Object.keys(this.fileDetails);
    //   }

    constructor(private cartService: CartService,
        private cdr: ChangeDetectorRef,
        private downloadService: DownloadService,
        private http: HttpClient,
        private cfg: AppConfig,
        private _FileSaverService: FileSaverService,
        private confirmationService: ConfirmationService,
        private commonFunctionService: CommonFunctionService,
        private gaService: GoogleAnalyticsService,
        public router: Router,
        private notificationService: NotificationService,
        private edstatsvc: EditStatusService,
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

        this.edstatsvc._watchForceDataFileTreeInit((start) => {
            if (start && this.inBrowser) {
                this.globalDataCart = DataCart.openCart(this.CART_CONSTANTS.GLOBAL_CART_NAME);
                this.allSelected = this.updateAllSelectStatus(this.files);
                this.cartLength = this.globalDataCart.size();
            }
        });

        this.cartService.watchCartLength().subscribe(value => {
            this.cartLength = value;
        });
    }

    ngOnInit() {
        if(this.inBrowser){
            this.globalDataCart = DataCart.openCart(this.CART_CONSTANTS.GLOBAL_CART_NAME);
            this.dataCartStatus = DataCartStatus.openCartStatus();

            this.cartLength = this.globalDataCart.size();
            this.updateStatusFromCart();

            window.addEventListener("storage", this.cartChanged.bind(this));
        }
    }

    cartChanged(ev){
        if (ev.key == this.globalDataCart.getKey()) {
            this.globalDataCart = DataCart.openCart(this.CART_CONSTANTS.GLOBAL_CART_NAME);
            this.cartLength = this.globalDataCart.size();
            this.buildTree();
        }
    }

    ngOnChanges() {
        this.accessPages = []
        if (this.record['components'])
            this.accessPages = this.selectAccessPages(this.record['components']);
        this.buildTree();
    }

    /**
     * Build data file tree
     */
    buildTree() {
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
            }, children: this.files
        };
        this.treeRoot.push(newPart);
        this.updateStatusFromCart();
        this.allSelected = this.updateAllSelectStatus(this.files);
        this.downloadStatus = this.updateDownloadStatus(this.files) ? "downloaded" : null;
        this.totalFiles = 0;
        this.getTotalFiles(this.files);

    }

    /**
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
     * @param dataFiles - file tree
     * @param expanded - expand flag 
     * @param targetLevel 
     */
    expandToLevel(dataFiles: any, expanded: boolean, targetLevel: any) {
        this.expandAll(dataFiles, expanded, 0, targetLevel)
    }

    /**
     * Function to expand tree display to certain level - used by expandToLevel()
     * @param dataFiles - file tree
     * @param expanded 
     * @param level 
     * @param targetLevel 
     */
    expandAll(dataFiles: any, expanded: boolean, level: any, targetLevel: any) {
        let currentLevel = level + 1;
        for (let i = 0; i < dataFiles.length; i++) {
            dataFiles[i].expanded = expanded;
            if (targetLevel != null) {
                if (dataFiles[i].children.length > 0 && currentLevel < targetLevel) {
                    this.expandAll(dataFiles[i].children, expanded, currentLevel, targetLevel);
                }
            } else {
                if (dataFiles[i].children.length > 0) {
                    this.expandAll(dataFiles[i].children, expanded, currentLevel, targetLevel);
                }
            }
        }
        this.isExpanded = expanded;
        this.visible = false;
        setTimeout(() => {
            this.visible = true;
        }, 0);
    }

    /**
     * Function to reset the download status and incart status.
     * @param files - file tree 
     */
    resetStatus(files: any) {
        for (let comp of files) {
            if (comp.children && comp.children.length > 0) {
                this.resetStatus(comp.children);
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
        this.resetStatus(this.files);

        if(this.inBrowser){
            if(!this.globalDataCart)
                this.globalDataCart = DataCart.openCart(this.CART_CONSTANTS.GLOBAL_CART_NAME);

            for (let key in this.globalDataCart.contents) {
                this.setFilesDownloadStatus(this.files, this.globalDataCart.contents[key].resId, this.globalDataCart.contents[key].downloadStatus);
                if (this.globalDataCart.contents[key].cartId != undefined) {
                    let treeNode = this.searchTree(this.treeRoot[0], this.globalDataCart.contents[key].cartId);
                    if (treeNode != null) {
                        treeNode.data.isIncart = true;
                    }
                }
            }
        }

        return Promise.resolve(this.files);
    }

    /**
     * Function to get total number of files.
     * @param files - file tree
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
     * @param files - file tree
     * @param cartId - cart ID of the item to be set the status
     * @param downloadStatus - download status
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
        if (this.record['references'] && this.record['references'].length > 0) {
            return true;
        }else{
            return false;
        }
    }

    /**
     * return an array of AccessPage components from the given input components array
     * @param comps 
     */
    selectAccessPages(comps : NerdmComp[]) : NerdmComp[] {
        let use : NerdmComp[] = comps.filter(cmp => cmp['@type'].includes("nrdp:AccessPage") &&
                                       ! cmp['@type'].includes("nrd:Hidden"));
        use = (JSON.parse(JSON.stringify(use))) as NerdmComp[];
        return use.map((cmp) => {
            if (! cmp['title']) cmp['title'] = cmp['accessURL']
            return cmp;
        });
    }

    /**
     * Function to display bytes in appropriate format.
     * @param bytes 
     * @param numAfterDecimal - number of digits after decimal
     */
    formatBytes(bytes, numAfterDecimal) {
        return this.commonFunctionService.formatBytes(bytes, numAfterDecimal);
    }

    /**
     *  Open a popup window to display file details
     * @param event 
     * @param fileNode 
     * @param overlaypanel 
     */
    openDetails(event, fileNode: TreeNode, overlaypanel: OverlayPanel) {
        this.fileNode = fileNode;
        overlaypanel.hide();
        setTimeout(() => {
            overlaypanel.show(event);
        }, 100);
    }

    /**
     * Function to add whole subfolder files to data cart then update status
     * @param rowData - node in the file tree
     * @param isSelected - flag indicating if the node is selected
     */
    addSubFilesToCartAndUpdate(rowData: any, isSelected: boolean) {
        this.addSubFilesToCart(rowData, isSelected).then(function (result: any) {
            this.allSelected = this.updateAllSelectStatus(this.files);
        }.bind(this), function (err) {
            alert("something went wrong while adding file to data cart.");
        });
    }

    /**
     * Function to add whole subfolder files to data cart
     * @param rowData - node in the file tree
     * @param isSelected - flag indicating if the node is selected
     */
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
     * @param element - tree to be searched
     * @param cartId - cart ID for searching
     */
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
     * @param files - file tree
     */
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
                    this.cartService.setCartLength(this.globalDataCart.size());
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
     * @param files - file tree
     * @param isSelected - flag indicating if the node is selected
     * @param cartKey - key of the cart
     */
    addAllFilesToCart(files: any, isSelected: boolean, cartKey: string) {
        this.addFilesToCart(files, isSelected, cartKey).then(function (result2: any) {
            this.allSelected = this.updateAllSelectStatus(this.files);
            if (cartKey != '') {
                this.allSelected = true;
            }
        }.bind(this), function (err) {
            alert("something went wrong while adding one file to data cart.");
        });

        return Promise.resolve(files);
    }

    /**
     * Function to add given file tree to data cart.
     * @param files - file tree
     * @param isSelected - flag indicating if the node is selected
     * @param cartKey - key of the cart
     */
    addFilesToCart(files: any, isSelected: boolean, cartKey: string) {
        let compValue: any;
        for (let comp of files) {
            if (comp.children.length > 0) {
                compValue += this.addFilesToCart(comp.children, isSelected, cartKey);
            } else {
                this.addtoCart(comp.data, isSelected, cartKey).then(function (result) {
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
     * @param rowData - node in the file tree
     * @param isSelected - flag indicating if the node is selected
     * @param cartKey - key of the cart
     */
    addtoCart(rowData: any, isSelected: boolean, cartKey: string) {
        let dataCartItem: DataCartItem = {
            cartId: rowData.cartId,
            resId: rowData.resId, 
            ediid: this.ediid,
            filePath: rowData.filePath,
            downloadURL: rowData.downloadUrl,
            downloadStatus: rowData.downloadStatus,
            isIncart: true,
            resTitle: this.record['title'],
            resFilePath: rowData.filePath,
            fileName: rowData.name,
            fileSize: rowData.size,
            filetype: rowData.filetype,
            mediatype: rowData.mediatype,
            description: rowData.description,
            isSelected: false,
            message: rowData.message
        }
        if(cartKey == '') {   // general data cart
            this.globalDataCart.addFile(rowData.resId, dataCartItem, isSelected);
            this.globalDataCart.save();
            this.cartService.setCartLength(this.globalDataCart.size());
            if (cartKey == '')
                rowData.isIncart = true;
        }else{
            this.specialDataCart.addFile(rowData.resId, dataCartItem, isSelected);
            this.specialDataCart.save();
        }

        return Promise.resolve(true);
    }

    /**
     * Remove one node from cart and set flag
     * @param rowData - node in the file tree
     */
    removeFromNode(rowData: any) {
        this.removeCart(rowData);
        this.cartService.setCartLength(this.globalDataCart.size());
        this.allSelected = this.updateAllSelectStatus(this.files);
    }

   /**
    * Remove one node from cart - can be a file or sub-tree
    * @param rowData - node in the file tree 
    */
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
            this.globalDataCart.removeFileById(rowData.resId,rowData.filePath);
            // this.cartService.removeCartId(rowData.cartId);
            rowData.isIncart = false;
        }
    }

    /**
     * Remove all files from cart and set flags
     * @param files - file tree
     */
    removeFilesFromCart(files: TreeNode[]) {
        this.removeFromCart(files);
        this.allSelected = this.updateAllSelectStatus(this.files);
        return Promise.resolve(files);
    }

    /**
     * Remove all files from cart - used by removeFilesFromCart()
     * @param files - file tree
     */
    removeFromCart(files: TreeNode[]) {
        for (let comp of files) {
            if (comp.children.length > 0) {
                comp.data.isIncart = false;
                this.removeFromCart(comp.children);
            } else {
                this.globalDataCart.removeFileById(comp.data.resId,comp.data.filePath);
                // this.cartService.removeCartId(comp.data.cartId);
                comp.data.isIncart = false;
            }
        }

    }

    /**
     * Update select status - Check if all chirldren nodes were selected
     * @param files - file tree
     */
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
     * Update download status - once a file was downloaded, we need to update it's parent's status as well
     * @param files - file tree
     */
    updateDownloadStatus(files: any) {
        var allDownloaded = true;
        var noFileDownloadedFlag = true;
        for (let comp of files) {
            if (comp.children != undefined && comp.children.length > 0) {
                var status = this.updateDownloadStatus(comp.children);
                if (status) {
                    comp.data.downloadStatus = 'downloaded';
                    // this.cartService.updateCartItemDownloadStatus(comp.data.cartId, 'downloaded');
                    this.globalDataCart.setDownloadStatus(comp.data.resId, comp.data.filePath);
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
     * @param rowData - tree node
     */
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
     * @param rowData - tree node
     */
    setFileDownloaded(rowData: any) {
        rowData.downloadStatus = 'downloaded';
        // this.cartService.updateCartItemDownloadStatus(rowData.cartId, 'downloaded');
        this.globalDataCart.setDownloadStatus(rowData.resId, rowData.filePath);
        this.downloadStatus = this.updateDownloadStatus(this.files) ? "downloaded" : null;
        if (rowData.isIncart) {
            this.downloadService.setFileDownloadedFlag(true);
        }
    }

    /**
     * Function to download all files based on download url.
     * @param files - file tree
     */
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
     * Function to download all.
     */
    downloadFromRoot() {
        this.cancelAllDownload = false;
        this.specialDataCart = DataCart.createCart(this.ediid);

        setTimeout(() => {
            // this.cartService.clearTheCart();
            this.addAllFilesToCart(this.files, true, this.ediid).then(function (result) {
                // this.cartService.setCurrentCart(this.CART_CONSTANTS.GLOBAL_CART_NAME);
                window.open('/datacart/'+this.ediid, this.ediid);
                this.updateStatusFromCart().then(function (result: any) {
                    this.edstatsvc.forceDataFileTreeInit();
                }.bind(this), function (err) {
                    alert("something went wrong while adding file to data cart.");
                });
            }.bind(this), function (err) {
                alert("something went wrong while adding all files to cart");
            });
        }, 0);
    }

    /**
     * Function to set the download status of all files to downloaded.
     * @param files - file tree
     */
    setAllDownloaded(files: any) {
        for (let comp of files) {
            if (comp.children.length > 0) {
                this.setAllDownloaded(comp.children);
            } else {
                comp.data.downloadStatus = 'downloaded';
                // this.cartService.updateCartItemDownloadStatus(comp.data.cartId, 'downloaded');
                this.globalDataCart.setDownloadStatus(comp.data.resId, comp.data.filePath);
            }
        }
    }

    /**
     * Function to reset the download status of a file.
     * @param rowData - tree node
     */
    resetDownloadStatus(rowData) {
        rowData.downloadStatus = null;
        rowData.downloadProgress = 0;
        // this.cartService.updateCartItemDownloadStatus(rowData.cartId, null);
        this.globalDataCart.setDownloadStatus(rowData.resId, rowData.filePath);
        this.allDownloaded = false;
    }

    /**
     * Return "download all" button color based on download status
     */
    getDownloadAllBtnColor() {
        if (this.downloadStatus == null)
            return '#1E6BA1';
        else if (this.downloadStatus == 'downloaded')
            return 'green';
    }

    /**
     * Return "download" button color based on download status
     * @param rowData - tree node
     */
    getDownloadBtnColor(rowData: any) {
        if (rowData.downloadStatus == 'downloaded')
            return 'green';

        return '#1E6BA1';
    }

    /**
     * Return "add all to datacart" button color based on select status
     */
    getAddAllToDataCartBtnColor() {
        if (this.allSelected)
            return 'green';
        else
            return '#1E6BA1';
    }

    /**
     * Return tooltip text based on select status
     */
    getCartProcessTooltip() {
        if (this.allSelected)
            return 'Remove all from cart';
        else
            return 'Add all to cart';
    }

    /**
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

    /**
     * Set column width
     * @param mobWidth 
     */
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

    /**
     * Make sure the width of popup dialog is less than 500px or 80% of the window width
     */
    getDialogWidth() {
        if(this.inBrowser){
            var w = window.innerWidth > 500 ? 500 : window.innerWidth;
            return w + 'px';
        }
    }

    /**
     * Return the link text of the given reference.
     * 1. the value of the citation property (if set and is not empty)
     * 2. the value of the label property (if set and is not empty)
     * 3. to "URL: " appended by the value of the location property.
     * @param refs reference object
     */
    getReferenceText(refs){
        if(refs['citation']) 
            return refs['citation'];
        if(refs['label'])
            return refs['label'];
        return refs['location'];
    }
}
