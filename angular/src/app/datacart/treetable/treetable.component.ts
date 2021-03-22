import { Component, OnInit, Output, Input, NgZone, HostListener, Inject, PLATFORM_ID, EventEmitter, SimpleChanges } from '@angular/core';
import { TreeNode } from 'primeng/primeng';
import { CartService } from '../cart.service';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { CommonFunctionService } from '../../shared/common-function/common-function.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { CartConstants, DownloadStatus } from '../cartconstants';
import { DataCart, DataCartItem } from '../cart';
import { DisplayPrefs } from '../displayprefs';
import { DataCartStatus } from '../cartstatus';
import { OverlayPanel } from 'primeng/overlaypanel';
import { isPlatformBrowser } from '@angular/common';

/**
 * the structure used as the data item in a TreeNode displaying an item in the cart (or its parent collection) 
 */
interface CartTreeData {

    /**
     * a unique key for identifying this item
     */
    key: string;

    /**
     * the name of the file or collection
     */
    name: string;

    /**
     * a label indicating which type of file this represents.  The value should be one of "Subcollection",
     * "DataFile", or "ChecksumFile".  
     */
    filetype: string;

    /**
     * the description of the file in the cart.  This is a direct reference to DataCartItem for the file
     * that is in the cart.  If this item refers to a file's enclosing collection, this will not be set.
     */
    cartItem?: DataCartItem;

    /**
     * the media type to display for the file or subcollection
     */
    mediaType?: string;

    /**
     * the formatted size to display for the file (or subcollection)
     */
    size?: string;

    /**
     * the title of the resource that this file (or subcollection) is a part of 
     */
    resTitle?: string;

    /**
     * the name of the zip file that contains (or will contain) this file
     */
    zipFile?: string;

    /**
     * A message to display regarding the download status
     */
    message?: string;
}

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

    // Data
    dataFiles: TreeNode[] = [];     // data for TreeTable
    selectedData: TreeNode[] = [];  // selected data for TreeTable
    fileNode: CartTreeData;

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

    @Input() cartName: string;

    // Remove the cart upon tab closed
    @HostListener('window:beforeunload', ['$event'])
    beforeunloadHandler(event) {
        this.dataCartStatus.updateCartStatusInUse(this.cartName, false);
    }

    constructor(
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
    }

    ngOnInit() {
        if(this.inBrowser){
            this.dataCartStatus = DataCartStatus.openCartStatus();
            this.dataCart = this.cartService.getCart(this.cartName);
            this.loadDataTree();
            this.dataCart.watchForChanges(this.cartChanged.bind(this));
        }
    }

    /**
     * @param changes 
     */
    ngOnChanges(changes: SimpleChanges) {
    }

    /**
     * When storage changed and the key matches current datacart, 
     * reload the datacart and refresh the tree table.
     * @param event - change event
     */
    cartChanged(which) {
        this.createDataCartHierarchy();
    }

    /**
     * Load the data cart. If this is not the global data cart (user clicked on Download All button),
     * bundle download function will be fired immediately. Otherwise just display the data cart.
     * @param isGlobal - indicates if this is a global data cart
     */
    loadDataTree() {
        this.createDataCartHierarchy();

        let dispname : string = this.dataCart.getDisplayName();
        this.dataCartStatus.updateCartStatusInUse(this.cartName, true, dispname);
    }

    /**
     * respond to the user's selection of a file or collection
     */
    onNodeSelect(ev) {
        if (ev.node && ev.node.data) {
            let parts = ev.node.data.key.split('/', 2);
            if (parts.length > 1)
                this.dataCart.setSelected(parts[0], parts[1], false, true);
        }
    }

    /**
     * respond to the user's de-selection of a file or collection
     */
    onNodeUnselect(ev) {
        if (ev.node && ev.node.data) {
            let parts = ev.node.data.key.split('/', 2);
            if (parts.length > 1)
                this.dataCart.setSelected(parts[0], parts[1], true, true);
        }
    }

    /**
     * Return color code based on the input download status
     * @param downloadStatus download status
     */
    getDownloadStatusColor(downloadStatus: string){
        return DisplayPrefs.getDownloadStatusColor(downloadStatus);
    }

    /**
     * Some download status for display is different from the status in the dataFiles. This function maps the 
     * status in the dataFiles to the one for display.
     * @param downloadStatus download status
     */
    getStatusForDisplay(downloadStatus: string){
        return DisplayPrefs.getDownloadStatusLabel(downloadStatus);
    }

    /**
     * Return different icon class based on the input status
     * @param downloadStatus download status
     */
    getIconClass(downloadStatus: string){
        return DisplayPrefs.getDownloadStatusIcon(downloadStatus);
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
        this._clearCartDownloadStatus(this.dataFiles);
        this.dataCart.save();
    }

    _clearCartDownloadStatus(dataFiles: TreeNode[]) {
        // this will only clear the status of files that are not currently being downloaded
        for (let dfile of dataFiles) {
            if (dfile.children.length > 0)
                this._clearCartDownloadStatus(dfile.children);
            else if (dfile.data.downloadStatus != DownloadStatus.DOWNLOADING)
                this.dataCart.setDownloadStatus(dfile.data.cartItem.resId, dfile.data.cartItem.filePath,
                                                DownloadStatus.NO_STATUS, false);
        }
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

        rowData.downloadStatus = DownloadStatus.DOWNLOADED;

        this.dataCart.setDownloadStatus(rowData.resId, rowData.cartItem.filepath, rowData.downloadStatus, true);
    }

    /**
     * Rebuild the TreeTable's data structure (TreeNode[]) and its selection array from the 
     * current data cart contents
     */
    createDataCartHierarchy() {
        let makeParent = (name: string, key: string, title: string=null) : TreeNode => {
            return {
                data: { key: key, name: name, filetype: 'Subcollection', resTitle: title,
                        mediaType: '', size: '' },
                children: []
            }
        };
        let getParent = (item: DataCartItem, tree: TreeNode) => {
            let parent_levels = [item.resId, ...item.filePath.split('/').slice(0, -1)];
            return _getParent(parent_levels, tree, item.resTitle);
        };
        let _getParent = (levels: string[], tree: TreeNode, title: string=null) => {
            for(let child of tree.children) {
                if (child.data.name == levels[0]) {
                    if (levels.length > 1)
                        return _getParent(levels.slice(1), child, title);
                    else
                        return tree;
                }
            }
            // ancestor does not exist yet; create it
            let key = (tree.data.key) ? tree.data.key + '/' + levels[0] : levels[0];
            let child = makeParent(levels[0], key, title);
            tree.children.push(child);
            if (levels.length > 1)
                return _getParent(levels.slice(1), child);
            else
                return child;
        };
        
        let root : TreeNode = makeParent('', '');
        let selected : TreeNode[] = [];

        let filenode : TreeNode = null;
        for (let item of this.dataCart.getFiles()) {
            filenode = {
                data: {
                    key: item.key,
                    name: item.filePath.split('/')[-1],
                    filetype: (item["@type"] &&
                               item["@type"].length > 0) ? item["@type"][0]
                                                         : "DataFile",
                    cartItem: item,
                    resTitle: item.resTitle,
                    mediaType: item.mediaType || '',
                    size: (item.size) ? this.formatBytes(item.size, null) : '',
                    zipFile: (item.zipFile) ? item.zipFile : '',
                    message: (item.message) ? item.message : ''
                }
            };
            if (filenode.data.filetype.indexOf(':') >= 0)
                filenode.data.filetype =
                    filenode.data.filetype.substring(filenode.data.filetype.indexOf(':')+1);
            getParent(item, root).children.push(filenode);
            if (item.isSelected) 
                selected.push(filenode);
            // do we need to explicitly set selected parents?
        }

        // change the name of the top level items to the resource title
        for (let ds of root.children) {
            if (ds.data.resTitle)
                ds.data.name = ds.data.resTitle;
        }

        this.dataFiles = root.children;
        this.selectedData = selected;
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
    openDetails(event, rowdata: CartTreeData, overlaypanel: OverlayPanel) {
        this.fileNode = rowdata;
        overlaypanel.hide();
        setTimeout(() => {
            overlaypanel.show(event);
        }, 100);
    }
}
