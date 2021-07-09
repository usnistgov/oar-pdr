/**
 * Classes supporting the view of the list of data cart files.  The files are displayed as a hierarchical 
 * tree using the PrimeNG component, TreeTable.  The top level of the hierarchy represents the dataset the 
 * files are a part of, and levels below it represent the subcollections that contain the files.  The key 
 * entities provide in this source file are:
 * 
 *   * CartTreeData -- an interface representing the data used to visualize the file; it serves as the
 *          data properties for the TreeNodes provided to the TreeTable.
 *   * CartTreeNode -- an implementation of the TreeNode interface that provides functions useful for 
 *          creating and updating the TreeNode hierarchy.  
 *   * TreetableComponent -- the Angular component class that provides the view of the data cart list; it 
 *          holds the TreeNode hierarchy and uses the PrimeNG TreeTable component to display it.
 *
 */
import { Component, OnInit, OnChanges, AfterViewInit, Output, Input, ViewChild, NgZone, HostListener, Inject,
         PLATFORM_ID, EventEmitter, SimpleChanges } from '@angular/core';
import { TreeNode, TreeTable } from 'primeng/primeng';
import { CartService } from '../cart.service';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { formatBytes } from '../../utils';
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

/**
 * A TreeNode that knows how to insert and update items from a data cart
 */
export class CartTreeNode implements TreeNode {
    children = [];
    data = {
        key: '', name: '', filetype: 'Subcollection', cartItem: null,
        mediaType: '',  size: '', resTitle: '', zipFile: '', message: ''
    };
    isExpanded = false;
    keyname: string = '';
    
    constructor(name: string='', key: string=null, title: string = '') {
        this.data.key = key;
        this.data.name = name;
        this.data.resTitle = title;
        if (this.data.key == null)
            this.data.key = name;
        this.keyname = name;
    }

    /**
     * insert or update a node within this tree corresponding to the given data cart item
     * @return CartTreeNode   the node that was inserted or updated
     */
    upsertNodeFor(item: DataCartItem) : CartTreeNode {
        let levels = item.key.split("/");
        return this._upsertNodeFor(levels, item);
    }

    _upsertNodeFor(levels: string[], item: DataCartItem) : CartTreeNode {
        // find the node corresponding to the given item in the data cart 
        for (let child of this.children) {
            if (child.keyname == levels[0]) {
                if (levels.length > 1)
                    return child._upsertNodeFor(levels.slice(1), item);
                else {
                    child.updateData(item);
                    return child;
                }
            }
        }

        // ancestor does not exist yet; create it
        let key = (this.data.key) ? this.data.key + '/' + levels[0] : levels[0];
        let child = new CartTreeNode(levels[0], key, item.resTitle || '');
        this.children.push(child);
        if (levels.length > 1)
            return child._upsertNodeFor(levels.slice(1), item);

        child.updateData(item);
        return child;
    }

    /**
     * update the data for this node to match the given data cart item
     */
    updateData(item: DataCartItem) : void {
        if (! this.data.cartItem) {
            this.data.filetype = "File";
            this.data.mediaType = item.mediaType || '';
            this.data.size = (item.size !== null && item.size !== undefined) ? formatBytes(item.size) : '';
            this.data.resTitle = item.resTitle;
        }
        this.data.cartItem = item;
        if (item.zipFile) this.data.zipFile = item.zipFile;
        if (item.message) this.data.message = item.message;
    }

    /**
     * find the node within this tree with the given key or null if not found
     */
    findNode(key: string) : CartTreeNode {
        for (let node of this.children) {
            if (node.data.key == key)
                return node;
            else if (node.children.length > 0) {
                let out = node.findNode(key);
                if (out) return out;
            }
        }
        return null;
    }

    /**
     * remove any descentdent node, along with its then empty ancestors, that is not found 
     * in the given data cart
     * @param cart      the data cart to use to determine if a file represented by a node is 
     *                  currently in the cart.
     * @param removing  a callback function that takes a TreeNode that is about to be removed 
     *                  from the display tree.  This allows the caller to meddle with the node
     *                  before it is removed (e.g. change its selection status and that of its 
     *                  parent nodes).  
     */
    cleanNodes(cart: DataCart, removing: (TreeNode) => void = null) : boolean {
        if (this.children.length == 0 && this.data.cartItem)
            // only operates on parent nodes
            return true;

        let newchildren: CartTreeNode[] = []  // a modified list of the children (minus removed ones)
        let updated = false;                  // true if any current children were removed (by not
                                              //   being put into newchildren)
        for (let child of this.children) {
            if (child.children.length > 0) {
                if (child.cleanNodes(cart, removing)) 
                    // child is not empty; retain it (otherwise, it will be dropped)
                    newchildren.push(child);
                else {
                    if (removing) removing(child);
                    updated = true;
                }
            }
            else if (child.data.cartItem && cart.findFileById(child.data.cartItem.key))
                // found the child in the data cart
                newchildren.push(child);
            else {
                // child was not found in cart
                if (removing) removing(child);
                updated = true;
            }
        }
        if (updated)
            // we removed some children; update our list
            this.children = newchildren;

        // false if this node is now empty
        return this.children.length > 0;
    }
}

/**
 * the component providing the view of the files in the data cart.
 */
@Component({
  selector: 'app-treetable',
  templateUrl: './treetable.component.html',
  styleUrls: ['./treetable.component.css', '../datacart.component.css']
})
export class TreetableComponent implements OnInit, AfterViewInit {
    public CART_CONSTANTS: any;

    dataCart: DataCart;
    dataCartStatus: DataCartStatus;
    inBrowser: boolean = false;

    // Data
    dataTree: CartTreeNode = new CartTreeNode(); // its children are the TreeNode[] given to TreeTable
    selectedData: TreeNode[] = [];               // selected data for TreeTable
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

    @ViewChild("ngtt")
    tt : TreeTable;

    // Remove the cart upon tab closed
    @HostListener('window:beforeunload', ['$event'])
    beforeunloadHandler(event) {
        this.dataCartStatus.updateCartStatusInUse(this.cartName, false);
    }

    constructor(
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

    ngAfterViewInit() {
        // this will properly select and mark parent nodes for selected files
        this.propagateSelections();
    }

    /**
     * ensure that parent nodes of selected files are properly shown as selected or partially selected.
     * 
     * When the tree table (this.dataTree) is built or updated from the data cart, only the file nodes 
     * are put into the selected list (this.selectedData).  This method will update the selection status
     * for all the parent nodes accordingly.  Without calling this, the selection status may not initially 
     * reflect the selection status until the user starts clicking boxes.  
     */
    propagateSelections() : void {
        if (this.tt) {
            let selcount = this.selectedData.length;
            for (let selnode of this.selectedData) {
                if (selnode.children && selnode.children.length == 0)
                    this.tt.propagateSelectionUp(selnode, true);
            }
            if (this.tt.selection.length != selcount)
                this.dataTree.children = [...this.dataTree.children];
        }
    }

    /**
     * When storage changed and the key matches current datacart, 
     * reload the datacart and refresh the tree table.
     * @param event - change event
     */
    cartChanged(which) {
        console.log("Updating view for change in cart");
        let node: CartTreeNode = null;
        for (let item of this.dataCart.getFiles()) {
            node = this.dataTree.upsertNodeFor(item);
            if (item.isSelected && (!this.tt || !this.tt.isSelected(node))) {
                this.selectedData.push(node);
                if (this.tt) this.tt.propagateSelectionUp(node, true);
            }
        }

        // remove deleted items
        this.dataTree.cleanNodes(this.dataCart, (node) => {
            if (this.tt && this.tt.isSelected(node)) {
                this.tt.propagateSelectionDown(node, false);
                this.tt.propagateSelectionUp(node, false);
            }
        });

        // make sure the top level name is set to the resource title
        for (let child of this.dataTree.children) {
            if (child.data.resTitle) child.data.name = child.data.resTitle
        }
        
        this.dataTree.children = [...this.dataTree.children];  // trigger refresh of table
        // this.refreshTree();
    }

    /**
     * Load the data cart. If this is not the global data cart (user clicked on Download All button),
     * bundle download function will be fired immediately. Otherwise just display the data cart.
     * @param isGlobal - indicates if this is a global data cart
     */
    loadDataTree() {
        let node: CartTreeNode = null;
        this.selectedData = []
        for (let item of this.dataCart.getFiles()) {
            node = this.dataTree.upsertNodeFor(item);
            if (item.isSelected) 
                this.selectedData.push(node);
        }

        // tweak the top level: set name to the resource title, open first level
        for (let child of this.dataTree.children) {
            if (child.data.resTitle) child.data.name = child.data.resTitle
            child.expanded = true;
        }

        let dispname : string = this.dataCart.getDisplayName();
        this.dataCartStatus.updateCartStatusInUse(this.cartName, true, dispname);
    }

    /**
     * respond to the user's selection of a file or collection
     */
    onNodeSelect(ev) {
        if (ev.node && ev.node.data) {
            let parts = this._keySplit(ev.node.data.key);
            this.dataCart.setSelected(parts[0], parts[1], false, true, this);
        }
    }

    /**
     * respond to the user's de-selection of a file or collection
     */
    onNodeUnselect(ev) {
        if (ev.node && ev.node.data) {
            let parts = this._keySplit(ev.node.data.key);
            this.dataCart.setSelected(parts[0], parts[1], true, true, this);
        }
    }

    _keySplit(key: string) {
        let p: number = key.indexOf("/");
        if (p < 0) return [key];
        return [key.substring(0,p), key.substring(p+1)]
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
        this._clearCartDownloadStatus(this.dataTree.children);
        this.dataCart.save(this);
    }

    _clearCartDownloadStatus(dataFiles: TreeNode[]) {
        // this will only clear the status of files that are not currently being downloaded
        for (let dfile of dataFiles) {
            if (dfile.children.length > 0)
                this._clearCartDownloadStatus(dfile.children);
            else if (dfile.data.downloadStatus != DownloadStatus.DOWNLOADING)
                this.dataCart.setDownloadStatus(dfile.data.cartItem.resId, dfile.data.cartItem.filePath,
                                                DownloadStatus.NO_STATUS, false, null, this);
        }
    }

    /**
     * Function to display bytes in appropriate format.
     * @param bytes - input data in bytes
     */
    formatBytes(bytes) {
        return formatBytes(bytes);
    }

    /**
     * Function to set status when a file was downloaded
     * @param rowData - tree node that the file was downloaded
     */
    setFileDownloaded(rowData: any) {
            // Google Analytics code to track download event
        this.gaService.gaTrackEvent('download', undefined, rowData.ediid, rowData.downloadUrl);

        rowData.downloadStatus = DownloadStatus.DOWNLOADED;

        this.dataCart.setDownloadStatus(rowData.resId, rowData.cartItem.filepath, rowData.downloadStatus, 
                                        true, null, this);
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
