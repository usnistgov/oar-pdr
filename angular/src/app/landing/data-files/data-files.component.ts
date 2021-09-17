import { Component, Input, Output, NgZone, OnInit, OnChanges, SimpleChanges, EventEmitter } from '@angular/core';
import { TreeNode } from 'primeng/api';
import { CartService } from '../../datacart/cart.service';
import { OverlayPanel } from 'primeng/overlaypanel';
import { AppConfig } from '../../config/config';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { NerdmRes, NerdmComp } from '../../nerdm/nerdm';
import { DataCart, DataCartItem } from '../../datacart/cart';
import { DownloadStatus } from '../../datacart/cartconstants';
import { DataCartStatus } from '../../datacart/cartstatus';
import { formatBytes } from '../../utils';

declare var _initAutoTracker: Function;

/**
 * the structure used as the data item in a TreeNode displaying a file or collection component
 */
interface DataFileItem {

    /**
     * a unique key for identifying this item
     */
    key : string;

    /**
     * the name of the file or collection
     */
    name : string;

    /**
     * the NERDm component metadata
     */
    comp : NerdmComp;

    /**
     * a display rendering of the size of the file
     */
    size : string;

    /**
     * a display rendering of the file's media type
     */
    mediaType : string;

    /**
     * true if the component is currently in the global data cart
     */
    isInCart? : boolean;

    /**
     * a label indicating the download status of this file
     */
    downloadStatus? : string;

    /**
     * a number representing the progress toward completing the download of this file. 
     * (Note: use of this feature is currently disabled.)
     */
    downloadProgress? : number;
}

/**
 * A component that displays the hierarchical collection of files available as downloadable 
 * distributions.  
 *
 * This implementation is based on the TreeTable component from primeng.  
 */
@Component({
    moduleId: module.id,
    styleUrls: ['../landing.component.css'],
    selector: 'pdr-data-files',
    templateUrl: `data-files.component.html`,
    providers: [ ]
})
export class DataFilesComponent implements OnInit, OnChanges {

    @Input() record: NerdmRes;
    @Input() inBrowser: boolean;   // false if running server-side
    @Input() editEnabled: boolean;    //Disable download all functionality if edit is enabled

    // Download status to trigger metrics refresh in parent component
    @Output() dlStatus: EventEmitter<string> = new EventEmitter();  

    ediid: string = '';
    files: TreeNode[] = [];           // the hierarchy of collections and files
    fileCount: number = 0;            // number of files being displayed
    downloadStatus: string = '';      // the download status for the dataset collection as a whole
    globalDataCart: DataCart = null;
    dataCartStatus: DataCartStatus;
    allInCart: boolean = false;
    isAddingToDownloadAllCart: boolean = false;
    isTogglingAllInGlobalCart: boolean = false;

    cols: any[];
    fileNode: TreeNode;               // the node whose description has been opened
    isExpanded: boolean = false;
    visible: boolean = true;
    cartLength: number;
    showZipFileNames: boolean = false;    // zip file display is currently disabled
    showDownloadProgress: boolean = false;
    appWidth: number = 800;   // default value used in server context
    appHeight: number = 900;  // default value used in server context
    fontSize: string;

    constructor(private cfg: AppConfig,
                private cartService: CartService,
                private gaService: GoogleAnalyticsService,
                ngZone: NgZone)
    {
        this.cols = [
            { field: 'name', header: 'Name', width: '60%' },
            { field: 'mediaType', header: 'Media Type', width: 'auto' },
            { field: 'size', header: 'Size', width: 'auto' },
            { field: 'download', header: 'Status', width: 'auto' }];

        if (this.inBrowser && typeof (window) !== 'undefined') {
            this.appHeight = (window.innerHeight);
            this.appWidth = (window.innerWidth);
            this.setWidth(this.appWidth);

            window.onresize = (e) => {
                ngZone.run(() => {
                    this.appWidth = window.innerWidth;
                    this.appHeight = window.innerHeight;
                    this.setWidth(this.appWidth);
                });
            };
        }
    }

    ngOnInit() {
        if(this.inBrowser){
            this.globalDataCart = this.cartService.getGlobalCart();
            this.cartLength = this.globalDataCart.size();
            this.globalDataCart.watchForChanges((ev) => { this.cartChanged(); })

            this.dataCartStatus = DataCartStatus.openCartStatus();
        }
        if (this.record)
            this.useMetadata();
    }

    ngOnChanges(ch: SimpleChanges) {
        if (this.record && ch.record)
            this.useMetadata();
    }

    useMetadata() {
        this.ediid = this.record['ediid']
        this.buildTree();
    }

    /**
     * Handle datacart change event
     */
    cartChanged(){
        this.cartLength = this.globalDataCart.size();
        if (this.files.length > 0) {
            setTimeout(() => {
                this.updateStatusFromCart();
            }, 0);
        }
    }

    /**
     * Update treenode's downloadStatus and isInCart properties from a given datacart
     * @param nodes Treenodes to be updated
     * @param dc Datacart to update the treenodes
     * @returns if all treenodes are in the datacart
     */
    _updateNodesFromCart(nodes: TreeNode[], dc: DataCart): boolean[] {
        let allIn: boolean = true;   // whether all files are in the cart
        let allDld: boolean = true;  // whether all files have been downloaded
        let allstats: boolean[] = [];
        for (let child of nodes) {
            if (child.children.length > 0) {
                allstats = this._updateNodesFromCart(child.children, dc);
                child.data.isInCart = allstats[0];
                child.data.downloadStatus=(allstats[1]) ? DownloadStatus.DOWNLOADED : DownloadStatus.NO_STATUS;
                if (! child.data.isInCart) 
                    allIn = false;
                if (child.data.downloadStatus != DownloadStatus.DOWNLOADED)
                    allDld = false;
            }
            else if (child.data.comp && child.data.comp.downloadURL) {
                // a file node
                let dci: DataCartItem = dc.findFile(this.ediid, child.data.comp.filepath);
                if (dci) {
                    child.data.downloadStatus = dci.downloadStatus;
                    child.data.isInCart = true;
                }
                else 
                    child.data.isInCart = false;
                if (! child.data.isInCart)
                    allIn = false;
                if (child.data.downloadStatus != DownloadStatus.DOWNLOADED)
                    allDld = false;
            }
        }

        return [allIn, allDld];
    }

    /**
     * Build data file tree. Exclude .sha files.
     */
    buildTree() : void {
        if (! this.record['components'])
            return;

        let makeNodeData = (name: string, parentKey: string, comp: NerdmComp) => {
            let key = (parentKey) ? parentKey + '/' + name : name;
            let out = { name: name, key: key, comp: null, size: '', mediaType: '',
                        isInCart: false, downloadStatus: DownloadStatus.NO_STATUS, downloadProgress: 0   };
            if (comp) {
                out['comp'] = comp;
                out['mediaType'] = comp.mediaType || '';
                out['size'] = (comp.size === null || comp.size === undefined) ? ''
                                                                              : this.formatBytes(comp.size);
            }
            return out;
        }
        let _insertComp = (levels: string[], comp: NerdmComp, tree: TreeNode) => {
            for (let child of tree.children) {
                if (child.data.name == levels[0]) {
                    if (levels.length > 1) 
                        return _insertComp(levels.slice(1), comp, child);
                    else  {
                        // this is the node we are looking for
                        child.data = makeNodeData(levels[0], tree.data.key, comp);
                        return child;
                    }
                }
            }
            // anscestor node does not exist yet
            if (levels.length > 1) {
                // haven't found leaf yet
                let child = { data: makeNodeData(levels[0], tree.data.key, null), children: [] };
                tree.children.push(child);
                return _insertComp(levels.slice(1), comp, child);
            }
            else {
                let child = { data: makeNodeData(levels[0], tree.data.key, comp), children: [] };
                tree.children.push(child);
                return child;
            }
        }
        let insertComp = (comp: NerdmComp, root: TreeNode) => {
            let levels = comp.filepath.split('/');
            return _insertComp(levels, comp, root);
        };

        let count = 0;
        let downloadedCount = 0;
        let root: TreeNode = { data: { name: '', key: '' }, children: [] };
        let node: TreeNode = null;

        // Filter out sha files
        for (let comp of this.record['components']) {
            if (comp.filepath && comp['@type'].filter(tp => tp.includes(':Hidden')).length == 0 &&
                comp['@type'].filter(tp => tp.includes(':ChecksumFile')).length == 0)
            {
                node = insertComp(comp, root);
                if (node.data.comp['@type'].filter(tp => tp.endsWith("File")).length > 0) 
                    count++;
            }
        }
        this.files = [...root.children];
        this.fileCount = count;
        this.updateStatusFromCart();
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
            comp.data['isInCart'] = false;
            comp.data['downloadStatus'] = DownloadStatus.NO_STATUS;
            if (comp.children && comp.children.length > 0) 
                this.resetStatus(comp.children);
        }
        this.allInCart = false;
        this.downloadStatus = DownloadStatus.NO_STATUS;
        return Promise.resolve(files);
    }

    /**
     * Function to sync the all download statuses from data cart.
     */
    updateStatusFromCart() {
        if (this.globalDataCart) {  // Note: not set on server-side
            let allstats: boolean[] = this._updateNodesFromCart(this.files, this.globalDataCart);
            this.allInCart = allstats[0]
            this.downloadStatus = (allstats[1]) ? DownloadStatus.DOWNLOADED : DownloadStatus.NO_STATUS;
        }
        return Promise.resolve(this.files);
    }

    /**
     * Function to display bytes in appropriate format.
     * @param bytes  an integer file size in bytes
     */
    formatBytes(bytes) {
        return formatBytes(bytes, null);
    }

    /**
     *  Open a popup window to display file details
     * @param event          the event that triggered the display
     * @param fileNode       the TreeNode for the file to provide details for
     * @param overlaypanel   the OverlayPanel that is to contain the details
     */
    openDetails(event, fileNode: TreeNode, overlaypanel: OverlayPanel) {
        this.fileNode = fileNode;
        overlaypanel.hide();
        setTimeout(() => {
            overlaypanel.show(event);
        }, 100);
    }

    /**
     * return the TreeNode with the given key or null if not found
     */
    findNode(nodes: TreeNode[], key: string) : TreeNode {
        for (let node of nodes) {
            if (node.data.key == key)
                return node;
            else if (node.children.length > 0) {
                let out = this.findNode(node.children, key);
                if (out) return out;
            }
        }
        return null;
    }

    /**
     * Remove one node from cart and set flag
     * @param rowData - node in the file tree
     */
    removeFromGlobalCart(rowData: any) {
        if (!this.globalDataCart)
            // not inBrowser or otherwise ready
            return;

        setTimeout(() => {
            console.log("Removing all within "+this.ediid+"/"+rowData.comp.filepath+" from global cart");
            this.globalDataCart.removeMatchingFiles(this.ediid, rowData.comp.filepath, true);
            this.allInCart = false;
        }, 0);
    }

    /**
     * Add a node to the global data cart
     */
    addToGlobalCart(rowData: any) : void {
        if (! this.globalDataCart)
            // not inBrowser or otherwise ready
            return;
        
        setTimeout(() => {
            let node : TreeNode = this.findNode(this.files, rowData.key);
            if (node) {
                console.log("Adding all within "+node.data.key+" to global cart");
                this._addAllWithinToCart(node, this.globalDataCart, false);
                this.globalDataCart.save();
                this.allInCart = this._areAllInCart(this.files);
            }
            else
                console.error("Unable to add row with key="+rowData.key+"; Failed to find node in tree");
        }, 0);
    }
    _addAllWithinToCart(node: TreeNode, cart: DataCart, selected: boolean = false) : void {
        if (node.children.length > 0) {
            for(let child of node.children) 
                this._addAllWithinToCart(child, cart, selected);
        }
        else 
            this.addFileToCart(node.data.comp, cart, selected, false);
    }

    /**
     * add a single file component to the global data cart
     */
    addFileToCart(file: NerdmComp, cart: DataCart,
                  selected: boolean =false, dosave: boolean =true) : DataCartItem
    {
        if (cart && file.filepath && file.downloadURL) {
            let added: DataCartItem = cart.addFile(this.ediid, file, selected, dosave);
            added['resTitle'] = this.record['title'];
            return added;
        }
    }

    /**
     * walk through the files tree to determine if all files from this dataset are currently in 
     * the global cart
     */
    _areAllInCart(nodes: TreeNode[]) : boolean {
        for (let node of nodes) {
            if (node.children.length > 0) {
                if (! this._areAllInCart(node.children))
                    return false;
            }
            else if (! node.data.isInCart)
                return false;
        }
        return true;
    }

    /** 
     * Either add/remove all files to/from the global data cart.  This responds to the user clicking 
     * on the "add all to cart" icon.  If all files are already in the cart, all files will be removed;
     * otherwise, all not in the cart will be added.
     */
    toggleAllFilesInGlobalCart() : void {
        if (! this.globalDataCart) return;
        this.isTogglingAllInGlobalCart = true;
        setTimeout(() => {
            if (this.allInCart) {
                console.log("Removing all files from "+this.ediid+" from cart");
                this.globalDataCart.removeMatchingFiles(this.ediid, '', false);
                this.allInCart = false;
            }
            else {
                console.log("Adding all files from "+this.ediid+" to cart");
                for (let child of this.files) 
                    this._addAllWithinToCart(child, this.globalDataCart, false);
                this.allInCart = true;
            }
            this.globalDataCart.save();
            this.isTogglingAllInGlobalCart = false;
        }, 0);
    }

    /**
     * open up an exclusive cart and start to download all files from this dataset.  This
     * responds to the user clicking on the download-all icon.  
     */
    downloadAllFiles() {
        let cartName : string = this.ediid;
        if (cartName.startsWith("ark:/"))
            cartName = cartName.replace(/^ark:\/\d+\//, '');
        let downloadAllCart = this.cartService.getCart(cartName);
        downloadAllCart.setDisplayName(this.record['title'], false);
        this.isAddingToDownloadAllCart = true;
        this.dlStatus.emit("downloading"); // for reseting metrics refresh flag
        
        setTimeout(() => {
            for (let child of this.files) 
                this._addAllWithinToCart(child, downloadAllCart, true);

            downloadAllCart.save();
            this.isAddingToDownloadAllCart = false;
            window.open('/datacart/'+cartName+'?downloadSelected=true', cartName);
        }, 0);
    }

    /**
     * mark a file as downloaded in the data cart.  This will happen if the user clicks on the 
     * individual file download icon.
     */
    setFileDownloaded(rowData: DataFileItem) : void {
        // Emit the download flag so parent component can refresh the metrics data after couple of minutes
        this.dlStatus.emit("downloading"); // for reseting metrics refresh flag
        this.dlStatus.emit("downloaded");  // trigger metrics refresh

        if (this.globalDataCart) {
            this.globalDataCart.restore();
            this.globalDataCart.setDownloadStatus(this.record.ediid, rowData.comp.filepath);
        }
    }

    /**
     * Return "download all" button color based on download status
     */
    getDownloadAllBtnColor() {
        if (this.downloadStatus == DownloadStatus.DOWNLOADED)
            return 'green';
        else
            return '#1E6BA1';
    }

    /**
     * Return "download" button color based on download status
     * @param rowData - tree node
     */
    getDownloadBtnColor(rowData: any) {
        if (rowData.downloadStatus == DownloadStatus.DOWNLOADED)
            return 'green';

        return '#1E6BA1';
    }

    /**
     * Return "add all to datacart" button color based on select status
     */
    getAddAllToDataCartBtnColor() {
        if (this.allInCart)
            return 'green';
        else
            return '#1E6BA1';
    }

    /**
     * Return tooltip text based on select status
     */
    getCartProcessTooltip() {
        if (this.allInCart)
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
     * Set column width based on screen width
     * @param appWidth - width of current window
     */
    setWidth(appWidth: number) {
        if (appWidth > 1340) {
            this.cols[0].width = '60%';
            this.cols[1].width = '20%';
            this.cols[2].width = '15%';
            this.cols[3].width = '100px';
            this.fontSize = '16px';
        } else if (appWidth > 780 && this.appWidth <= 1340) {
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
        }else{
            return "500px";
        }
    }
}
