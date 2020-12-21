import { Component, OnInit, Output, Input, NgZone, HostListener, OnChanges, SimpleChanges, EventEmitter } from '@angular/core';
import { TreeNode } from 'primeng/primeng';
import { ZipData } from '../../shared/download-service/zipData';
import { CartService } from '../cart.service';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { CommonFunctionService } from '../../shared/common-function/common-function.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { CartConstants } from '../cartconstants';
import { DataCart } from '../cart';

@Component({
  selector: 'app-treetable',
  templateUrl: './treetable.component.html',
  styleUrls: ['./treetable.component.css', '../datacart.component.css']
})
export class TreetableComponent implements OnInit {
    public CART_CONSTANTS: any;

    dataCart: DataCart;

    // Data
    selectedFileCount: number = 0;
    selectedData: TreeNode[] = [];
    treeRoot = [];
    selectedNodes: TreeNode[] = [];
    dataFiles: TreeNode[] = [];

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

    @Input() ediid: string;
    @Input() zipData: ZipData[] = [];
    @Output() outputDataFiles = new EventEmitter<TreeNode[]>();
    @Output() outputSelectedData = new EventEmitter<TreeNode[]>();

    // Remove the cart upon tab closed
    @HostListener('window:beforeunload', ['$event'])
    beforeunloadHandler(event) {
        if(this.ediid != this.CART_CONSTANTS.GLOBAL_CART_NAME){
            this.cartService.setCartStatus(this.ediid, 'close');
        }
    }

    constructor(
        private downloadService: DownloadService,
        public commonFunctionService: CommonFunctionService,
        public cartService: CartService,
        public gaService: GoogleAnalyticsService,
        private ngZone: NgZone
    ) { 
        this.CART_CONSTANTS = CartConstants.cartConst;
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

        // Watch remote command from cartControl component
        // removeDownloaded - remove downloaded files from the data cart
        // removeSelected - remove selected files from the data cart

        this.cartService._watchRemoteCommand((command) => {
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
        });
    }

    ngOnInit() {
        if (this.ediid != this.CART_CONSTANTS.GLOBAL_CART_NAME) {
            this.dataCart = DataCart.openCart(this.ediid);

            this.cartService.setCartStatus(this.ediid, 'open');

            this.loadDataTree(false);
        } else {
            this.dataCart = DataCart.openCart(this.CART_CONSTANTS.GLOBAL_CART_NAME);
            this.loadDataTree();
        }

        window.addEventListener("storage", this.cartChanged.bind(this));
    }

    // When storage changed and the key matches current datacart, reload the datacart and refresh the tree table.
    cartChanged(ev){
        if (ev.key == this.dataCart.getKey()) {
            this.dataCart.restore();
            this.loadDataTree();
            if (this.ediid == this.CART_CONSTANTS.GLOBAL_CART_NAME) {
                this.cartService.setCartLength(this.dataCart.size());
            }
        }
    }

    /*
    * Loaing datacart
    */
    loadDataTree(isGlobal: boolean = true) {
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
        this.dataFileCount();
        this.expandToLevel(this.dataFiles, true, 3);
        this.outputDataFiles.emit(this.dataFiles);

        if(!isGlobal){
            this.cartService.executeCommand('downloadSelected', this.selectedData);
        }else{
            this.downloadService.setTotalFileDownloaded(this.downloadService.getTotalDownloadedFiles(this.dataFiles));
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
     * 
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
        this.dataFileCount();
        setTimeout(() => {
            this.expandToLevel(this.dataFiles, true, 1);
        }, 0);
        this.refreTree();
    }
    
    /**
     * Removes all selected files from the dataFiles and the dataCart
     **/
    removeSelectedData() {
        this.removeSelectedDataFromCart(this.selectedData);

        this.dataCart.save();
        this.createDataCartHierarchy();
        this.cartService.setCartLength(this.dataCart.size());
        this.selectedData = [];
        this.dataFileCount();
        this.expandToLevel(this.dataFiles, true, 1);
    }

    removeSelectedDataFromCart(selectedData: any){
        for (let selData of selectedData) {
            if(!selData.data.isLeaf){
                    this.removeSelectedDataFromCart(selData.children);
            }else{
                this.dataCart.removeFileById(selData.data['resId'], selData.data['resFilePath'])
            }
        }
    }

    /**
     * Set data table's column widthes based on the width of the device window
     * @param mobWidth width of the device window
     */
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

        this.outputSelectedData.emit(this.selectedData);
        this.cartService.setSelectedFileCount(this.selectedFileCount);
    }

    /**
     * Set the header style of the tree table 
     */
    headerStyle(width) {
        return { 'background-color': '#1E6BA1', 'width': width, 'color': 'white', 'font-size': this.fontSize };
    }

    /**
     * Set the body style of the tree table 
     */
    bodyStyle(width) {
        return { 'width': width, 'font-size': this.fontSize };
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
        this.refreTree();
    }

    /**
     * Refresh the tree table
     */
    refreTree(){
        this.isVisible = false;
        setTimeout(() => {
            this.isVisible = true;
        }, 0);
    }

    /**
     * clears all download status for both dataFiles and dataCart
     **/
    clearDownloadStatus() {
        this.cartService.resetDatafileDownloadStatus(this.dataFiles, this.dataCart, '');
        this.downloadService.setTotalFileDownloaded(0);
        this.downloadService.resetDownloadData();
    }

    /**
     * Function to display bytes in appropriate format.
     **/
    formatBytes(bytes, numAfterDecimal) {
        return this.commonFunctionService.formatBytes(bytes, numAfterDecimal);
    }

    /**
     * Function to set status when a file was downloaded
     **/
    setFileDownloaded(rowData: any) {
        // Google Analytics code to track download event
        this.gaService.gaTrackEvent('download', undefined, rowData.ediid, rowData.downloadUrl);

        rowData.downloadStatus = 'downloaded';

        this.dataCart.setDownloadStatus(rowData.resId, rowData.resFilePath);
        this.downloadService.setFileDownloadedFlag(true);
        this.outputDataFiles.emit(this.dataFiles);
    }

    /**
     * Create Data hierarchy for the tree
     * This is where dafaFiles get generated
     */
    createDataCartHierarchy() {
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
            // let resId = key;
            if (arrayList.hasOwnProperty(key)) {
                parentObj = {
                    data: {
                        'resTitle': key,
                    },
                    children:[]
                };

                // parentObj.children = [];
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
                        }
                    }
                }
                this.walkData(parentObj, parentObj, 0);
                this.dataFiles.push(parentObj);
            }
        }
        this.downloadService.setFileDownloadedFlag(!noFileDownloadedFlag);
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

}
