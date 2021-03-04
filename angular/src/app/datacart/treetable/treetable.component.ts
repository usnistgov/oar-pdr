import { Component, OnInit, Output, Input, NgZone, HostListener, Inject, PLATFORM_ID, EventEmitter, SimpleChanges } from '@angular/core';
import { TreeNode } from 'primeng/primeng';
import { ZipData } from '../../shared/download-service/zipData';
import { CartService } from '../cart.service';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { CommonFunctionService } from '../../shared/common-function/common-function.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { CartConstants } from '../cartconstants';
import { DataCart } from '../cart';
import { DataCartStatus } from '../cartstatus';
import { OverlayPanel } from 'primeng/overlaypanel';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-treetable',
  templateUrl: './treetable.component.html',
  styleUrls: ['./treetable.component.css', '../datacart.component.css']
})
export class TreetableComponent implements OnInit {
    public CART_CONSTANTS: any;

    dataCart: DataCart;
    dataCartStatus: DataCartStatus;
    inBrowser: boolean = false;
    isGlobalCart: boolean = true;

    // Data
    selectedFileCount: number = 0;
    selectedData: TreeNode[] = [];
    treeRoot = [];
    selectedNodes: TreeNode[] = [];
    dataFiles: TreeNode[] = [];
    fileNode: TreeNode;
    totalDownloaded: number = 0;

    // Display
    isExpanded: boolean = true;
    isVisible: boolean = true;
    showZipFilesNames: boolean = true;
    titleWidth: string;
    typeWidth: string;
    sizeWidth: string;
    actionWidth: string;
    statusWidth: string;
    fontSize: string;
    mobWidth: number;
    mobHeight: number;
    defaultExpandLevel: number = 3;

    @Input() ediid: string;
    @Input() zipData: ZipData[] = [];
    @Output() outputDataFiles = new EventEmitter<TreeNode[]>();
    @Output() outputSelectedData = new EventEmitter<TreeNode[]>();

    // Remove the cart upon tab closed
    @HostListener('window:beforeunload', ['$event'])
    beforeunloadHandler(event) {
        this.dataCartStatus.updateCartStatusInUse(this.ediid, false);
    }

    constructor(
        private downloadService: DownloadService,
        public commonFunctionService: CommonFunctionService,
        public cartService: CartService,
        public gaService: GoogleAnalyticsService,
        private ngZone: NgZone,
        @Inject(PLATFORM_ID) private platformId: Object
    ) { 
        this.inBrowser = isPlatformBrowser(platformId);
        this.CART_CONSTANTS = CartConstants.cartConst;

        if(this.inBrowser){
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

        // Watch remote command from cartControl component
        // removeDownloaded - remove downloaded files from the data cart
        // removeSelected - remove selected files from the data cart

        this.cartService._watchRemoteCommand((command) => {
            if(this.inBrowser){
                switch(command.command) { 
                    case 'removeDownloaded': { 
                    this.removeAllDownloadedFiles();
                    break; 
                    } 
                    case 'removeSelected': {
                        this.removeSelectedData();
                        break;
                    }
                    default: { 
                    //statements; 
                    break; 
                    } 
                } 
            }
        });
    }

    ngOnInit() {
        if(this.inBrowser){
            this.dataCartStatus = DataCartStatus.openCartStatus();
            this.isGlobalCart = (this.ediid == this.CART_CONSTANTS.GLOBAL_CART_NAME);

            if (!this.isGlobalCart) {
                this.dataCart = DataCart.openCart(this.ediid);
                this.loadDataTree();
                this.cartService.executeCommand('downloadSelected', this.selectedData);
            } else {
                this.dataCart = DataCart.openCart(this.CART_CONSTANTS.GLOBAL_CART_NAME);
                this.loadDataTree();
            }
            window.addEventListener("storage", this.cartChanged.bind(this));
        }
    }

    /**
     * When zipData changed
     * @param changes 
     */
    ngOnChanges(changes: SimpleChanges) {
        if (changes['zipData']) {
            if(changes['zipData'].previousValue == undefined && changes['zipData'].currentValue.length == 0)
                return;

            this.updateDataFiles(this.zipData);
        }
    }

    /**
     * Update dataFiles with input zipData
     * @param zipData 
     */
    updateDataFiles(zipData: ZipData[]){
        // Associate zipData with files
        for (let zip of zipData) {
            this.downloadService.setDownloadStatus(zip, this.dataFiles, zip.downloadStatus, this.dataCart);
        }
    }

    /**
     * When storage changed and the key matches current datacart, 
     * reload the datacart and refresh the tree table.
     * @param event - change event
     */
    cartChanged(event){
        if (event.key == this.dataCart.getKey()) {
            this.dataCart.restore();
            this.loadDataTree();
            if (this.ediid == this.CART_CONSTANTS.GLOBAL_CART_NAME) {
                this.cartService.setCartLength(this.dataCart.size());
            }
        }
    }

    /**
     * Load the data cart. If this is not the global data cart (user clicked on Download All button),
     * bundle download function will be fired immediately. Otherwise just display the data cart.
     * @param isGlobal - indicates if this is a global data cart
     */
    loadDataTree() {
        this.selectedData = [];
        this.createDataCartHierarchy();

        // create root
        const root = {
            data: {
                resTitle: "root"
            }, 
            children: this.dataFiles
        };

        this.treeRoot.push(root);
        this.buildSelectNodes(this.dataFiles);
        this.checkNode(this.dataFiles, this.selectedNodes);
        this.selectedDataFileCount();

        this.outputSelectedData.emit(this.selectedData);
        this.cartService.setSelectedFileCount(this.selectedFileCount);
        this.outputDataFiles.emit(this.dataFiles);

        if (this.ediid != this.CART_CONSTANTS.GLOBAL_CART_NAME) {
            if(this.dataFiles[0])
                this.dataCartStatus.updateCartStatusInUse(this.ediid, true, this.dataFiles[0].data.resTitle.substring(0,20)+"...");
        } else {
            this.dataCartStatus.updateCartStatusInUse(this.CART_CONSTANTS.GLOBAL_CART_NAME, true, this.CART_CONSTANTS.GLOBAL_CART_NAME);
        }
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
     * @param selectedNodes  Selected treenodes
     **/
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
        this.outputSelectedData.emit(this.selectedData);
    }

    /**
     * Return color code based on the input download status
     * @param downloadStatus download status
     */
    getDownloadStatusColor(downloadStatus: string){
        return this.cartService.getDownloadStatusColor(downloadStatus);
    }

    /**
     * Some download status for display is different from the status in the dataFiles. This function maps the 
     * status in the dataFiles to the one for display.
     * @param downloadStatus download status
     */
    getStatusForDisplay(downloadStatus: string){
        return this.cartService.getStatusForDisplay(downloadStatus);
    }

    /**
     * Return different icon class based on the input status
     * @param downloadStatus download status
     */
    getIconClass(downloadStatus: string){
        return this.cartService.getIconClass(downloadStatus);
    }

    /**
     * Removes all downloaded files from the dataFiles and the dataCart
     **/
    removeAllDownloadedFiles() {
        this.dataCart.restore();
        this.dataCart.removeDownloadedFiles();
        this.createDataCartHierarchy();
        this.outputDataFiles.emit(this.dataFiles);
        this.cartService.setCartLength(this.dataCart.size());
        this.downloadService.setTotalFileDownloaded(this.downloadService.getTotalDownloadedFiles(this.dataFiles));
        this.selectedData = [];
        this.selectedDataFileCount();
        setTimeout(() => {
            this.expandToLevel(this.dataFiles, true, 1);
        }, 0);
        this.refreshTree();
    }
    
    /**
     * Removes all selected files from the dataFiles and the dataCart
     **/
    removeSelectedData() {
        this.dataCart.restore();
        this.dataCart.removeSelectedData(this.selectedData);
        this.dataCart.save();

        this.createDataCartHierarchy();
        this.cartService.setCartLength(this.dataCart.size());
        this.selectedData = [];
        this.selectedFileCount = 0;
        this.outputSelectedData.emit(this.selectedData);
        this.cartService.setSelectedFileCount(this.selectedFileCount);
        //reset downloaded file count in case some were removed already
        this.downloadService.setTotalFileDownloaded(this.downloadService.getTotalDownloadedFiles(this.dataFiles));
        this.expandToLevel(this.dataFiles, true, 1);
    }

    /**
     * Set data table's column widthes based on the width of the device window
     * @param mobWidth width of the device window
     */
    setWidth(mobWidth: number) {
        if (mobWidth > 1340) {
            this.titleWidth = '60%';
            this.typeWidth = 'auto';
            this.sizeWidth = '100px';
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

    /**
     * Count the selected files
     */
    selectedDataFileCount(emit:boolean = false) {
        this.selectedFileCount = 0;
        for (let selData of this.selectedData) {
            if (selData.data['resFilePath'] != null) {
                if (selData.data.isLeaf) {
                    this.selectedFileCount++;
                }
            }
        }

        if(emit){
            this.outputSelectedData.emit(this.selectedData);
            this.cartService.setSelectedFileCount(this.selectedFileCount);
        }
    }

    /**
     * Set the header style of the tree table 
     * @param width - width of the column
     */
    headerStyle(width) {
        return { 'background-color': '#1E6BA1', 'width': width, 'color': 'white', 'font-size': this.fontSize };
    }

    /**
     * Set the body style of the tree table 
     * @param width - width of the tree table
     */
    bodyStyle(width) {
        return { 'width': width, 'font-size': this.fontSize };
    }

    /**
     * Expand the tree to a level
     * @param dataFiles - tree data file
     * @param isExpanded - flag indicating if the tree is expanded
     * @param targetLevel - level to expand
     */
    expandToLevel(dataFiles: any, isExpanded: boolean, targetLevel: any) {
        this.expandAll(dataFiles, isExpanded, 0, targetLevel)
    }

    /**
     * Expand the tree to a level - recursive
     * @param dataFiles  - tree data file
     * @param isExpanded - flag indicating if the tree is expanded
     * @param level - current level
     * @param targetLevel - level to expand
     */
    expandAll(dataFiles: any, isExpanded: boolean, level: any, targetLevel: any) {
        let currentLevel = level + 1;

        for (let i = 0; i < dataFiles.length; i++) {
            dataFiles[i].expanded = isExpanded;
            if (targetLevel != null) {
                if (dataFiles[i].children.length > 0 && currentLevel < targetLevel) {
                    this.expandAll(dataFiles[i].children, isExpanded, currentLevel, targetLevel);
                }
            } else {
                if (dataFiles[i].children.length > 0) {
                    this.expandAll(dataFiles[i].children, isExpanded, currentLevel, targetLevel);
                }
            }
        }
        this.isExpanded = isExpanded;
        this.refreshTree();
    }

    /**
     * Refresh the tree table
     */
    refreshTree(){
        this.isVisible = false;
        setTimeout(() => {
            this.isVisible = true;
        }, 0);
    }

    /**
     * clears all download status for both dataFiles and dataCart
     */
    clearDownloadStatus() {
        this.dataCart.restore();
        this.dataCart.resetDatafileDownloadStatus(this.dataFiles, '');
        this.dataCart.save();
        this.downloadService.setTotalFileDownloaded(0);
        this.downloadService.resetDownloadData();
    }

    /**
     * Function to display bytes in appropriate format.
     * @param bytes - input data in bytes
     * @param numAfterDecimal - number of digits after decimal
     */
    formatBytes(bytes, numAfterDecimal) {
        return this.commonFunctionService.formatBytes(bytes, numAfterDecimal);
    }

    /**
     * Function to set status when a file was downloaded
     * @param rowData - tree node that the file was downloaded
     */
    setFileDownloaded(rowData: any) {
        // Google Analytics code to track download event
        this.gaService.gaTrackEvent('download', undefined, rowData.ediid, rowData.downloadUrl);

        rowData.downloadStatus = 'downloaded';

        this.dataCart.setDownloadStatus(rowData.resId, rowData.resFilePath, rowData.downloadStatus, true);
        this.downloadService.setFileDownloadedFlag(true);
        this.outputDataFiles.emit(this.dataFiles);
    }

    /**
     * Create Data hierarchy for the tree
     * This is where dafaFiles get generated
     */
    createDataCartHierarchy() {
        this.totalDownloaded = 0;

        let arrayList = this.dataCart.getCartItems().reduce(function (result, current) {
            result[current.resTitle] = result[current.resTitle] || [];
            result[current.resTitle].push({data:current});
            return result;
        }, {});

        var noFileDownloadedFlag = true;
        this.dataFiles = [];
        let parentObj: TreeNode = {};

        var iii: number = 0;
        for (var key in arrayList) {
            if (arrayList.hasOwnProperty(key)) {
                parentObj = {
                    data: {
                        'resTitle': key,
                    },
                    children:[]
                };
                let level = 0;
                for (let fields of arrayList[key]) {
                    level = 0;
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
                                noFileDownloadedFlag = false;
                            }
                            /// Added this code to avoid the issue of extra file layers in the datacart
                            if (fpath[path] !== "") {
                                child2 = this.createDataCartChildrenTree(iii,
                                    "/" + fpath[path],
                                    fields.data.cartId,
                                    resId, ediid,
                                    fpath[path],
                                    fields.data.downloadURL,
                                    fields.data.resFilePath,
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
                            level++;
                            if(level <= this.defaultExpandLevel){
                                parent.expanded = true;
                            }
                        }
                    }
                }
                this.walkData(parentObj, parentObj, 0);
                this.dataFiles.push(parentObj);
            }
        }
        this.downloadService.setFileDownloadedFlag(!noFileDownloadedFlag);
        this.downloadService.setTotalFileDownloaded(this.totalDownloaded);
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
            },
            children: []
        };
        return child1;
    }

    /**
     * Create the hierarchy for the tree
     */
    walkData(inputArray, parent, level) {
        let index: any = {};
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

            if (inputArray.data.downloadStatus == "downloaded") {
                this.totalDownloaded++;
            }
        } else {
            inputArray.data.cartId = null;
            inputArray.data.isLeaf = false;
        }

        if (inputArray && inputArray.data.filePath) {
            var key = level + inputArray.data.filePath;
            if (!(key in index)) {
                index[key] = inputArray;
            } else {
                inputArray.children.forEach((item) => {
                    index[key].children.push(item);
                })
                var indx = 0;
                var found = false;
                parent.children.forEach((item) => {
                    if (!found &&
                        item.filePath === inputArray.data.filePath &&
                        item.resId === inputArray.data.resId
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
}
