import { Component, Input, Output, ChangeDetectorRef, NgZone, EventEmitter } from '@angular/core';
import { TreeNode } from 'primeng/api';
import { CartService } from '../../datacart/cart.service';
import { OverlayPanel } from 'primeng/overlaypanel';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { ConfirmationService } from 'primeng/primeng';
// import { ZipData } from '../../shared/download-service/zipData';  // currently disabled
import { HttpClient, HttpRequest, HttpEventType } from '@angular/common/http';
import { AppConfig } from '../../config/config';
import { FileSaverService } from 'ngx-filesaver';  // currently disabled
import { Router } from '@angular/router';
import { CommonFunctionService } from '../../shared/common-function/common-function.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { NerdmRes, NerdmComp } from '../../nerdm/nerdm';
import { DataCart, DataCartItem } from '../../datacart/cart';
import { DownloadStatus } from '../../datacart/cartconstants';
import { DataCartStatus } from '../../datacart/cartstatus';

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

@Component({
    moduleId: module.id,
    styleUrls: ['../landing.component.css'],
    selector: 'description-resources',
    templateUrl: `data-files.component.html`,
    providers: [ConfirmationService]
})

export class DataFilesComponent {

    @Input() record: NerdmRes;
    @Input() metadata: boolean;
    @Input() inBrowser: boolean;   // false if running server-side
    @Input() ediid: string;
    @Input() editEnabled: boolean;    //Disable download all functionality if edit is enabled

    files: TreeNode[] = [];           // the hierarchy of collections and files
    fileCount: number = 0;            // number of files being displayed
    downloadStatus: string = '';      // the download status for the dataset collection as a whole
    globalDataCart: DataCart = null;
    dataCartStatus: DataCartStatus;
    allInCart: boolean = false;
    isAddingToDownloadAllCart: boolean = false;
    isTogglingAllInGlobalCart: boolean = false;

    accessPages: NerdmComp[] = [];
    cols: any[];
    fileNode: TreeNode;               // the node whose description has been opened
    isExpanded: boolean = false;
    visible: boolean = true;
    cartLength: number;
    showZipFileNames: boolean = false;    // zip file display is currently disabled
    showDownloadProgress: boolean = false;
    mobWidth: number = 800;   // default value used in server context
    mobHeight: number = 900;  // default value used in server context
    fontSize: string;

    constructor(private cartService: CartService,
        private cdr: ChangeDetectorRef,
        private http: HttpClient,
        private cfg: AppConfig,
        private _FileSaverService: FileSaverService,
        private confirmationService: ConfirmationService,
        private commonFunctionService: CommonFunctionService,
        private gaService: GoogleAnalyticsService,
        public router: Router,
        private notificationService: NotificationService,
        ngZone: NgZone) {
        this.cols = [
            { field: 'name', header: 'Name', width: '60%' },
            { field: 'mediaType', header: 'Media Type', width: 'auto' },
            { field: 'size', header: 'Size', width: 'auto' },
            { field: 'download', header: 'Status', width: 'auto' }];

        if (this.inBrowser && typeof (window) !== 'undefined') {
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
            this.globalDataCart = this.cartService.getGlobalCart();
            this.cartLength = this.globalDataCart.size();
            this.globalDataCart.watchForChanges((ev) => { this.cartChanged(ev); })

            this.dataCartStatus = DataCartStatus.openCartStatus();
            this.buildTree();
        }
    }

    cartChanged(ev){
        this.cartLength = this.globalDataCart.size();
        if (this.files.length > 0) {
            console.log("updating status from cart");
            setTimeout(() => {
                this.allInCart = this._updateNodesFromCart(this.files, this.globalDataCart);
            }, 0);
        }
    }
    _updateNodesFromCart(nodes: TreeNode[], dc: DataCart): boolean {
        let allIn: boolean = true;
        for (let child of nodes) {
            if (child.children.length > 0) {
                child.data.isInCart = this._updateNodesFromCart(child.children, dc);
                if (! child.data.isInCart) 
                    allIn = false;
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
            }
        }

        return allIn;
    }

    /*
    ngOnChanges() {
        this.accessPages = []
        if (this.record['components'])
            this.accessPages = this.selectAccessPages(this.record['components']);
        this.buildTree();
    }
    */

    /**
     * Build data file tree
     */
    buildTree() : void {
        if (! this.record['components'])
            return;

        let makeNodeData = (name: string, parentKey: string, comp: NerdmComp) => {
            let key = (parentKey) ? parentKey + '/' + name : name;
            let out = { name: name, key: key, comp: null, size: '', mediaType: '',
                        isInCart: false, downloadStatus: '', downloadProgress: 0   };
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
        let inCartCount = 0;
        let root: TreeNode = { data: { name: '', key: '' }, children: [] };
        let node: TreeNode = null;
        let cartitem: DataCartItem = null;
        for (let comp of this.record['components']) {
            if (comp.filepath && comp['@type'].filter(tp => tp.includes(':Hidden')).length == 0) {
                node = insertComp(comp, root);
                /*
                cartitem = this.globalDataCart.findFile(this.record['@id'], comp.filepath);
                if (cartitem) {
                    node.data.isInCart = true;
                    inCartCount++;
                    node.data.downloadStatus = cartitem.downloadStatus;
                }
                */
                if (node.data.comp['@type'].filter(tp => tp.endsWith("File")).length > 0) {
                    count++;
                    if (node.data.downloadStatus == DownloadStatus.DOWNLOADED) downloadedCount++;
                }
            }
        }
        this.files = [...root.children];
        this.fileCount = count;
        this.allInCart = this._updateNodesFromCart(this.files, this.globalDataCart);
        if (count > 0 && downloadedCount == count) 
            this.downloadStatus = DownloadStatus.DOWNLOADED
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
            comp.data['isInCart'] = false;
            comp.data['downloadStatus'] = '';
            if (comp.children && comp.children.length > 0) 
                this.resetStatus(comp.children);
        }
        return Promise.resolve(files);
    }

    /**
     * Function to sync the download status from data cart.
     */
    updateStatusFromCart() {
        let _setStatus = (nodes: TreeNode[]) => {
            for (let node of nodes) {
                if (node.children.length > 0)
                    _setStatus(node.children);
                else {
                    let cartitem = this.globalDataCart.findFile(node.data.resId, node.data.comp.filepath);
                    if (cartitem) {
                        node.data.isInCart = true;
                        node.data.downloadStatus = cartitem.downloadStatus;
                    }
                }
            }
        }
        if (this.globalDataCart) 
            _setStatus(this.files);
        return Promise.resolve(this.files);
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
     */
    formatBytes(bytes) {
        return this.commonFunctionService.formatBytes(bytes, null);
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
    addFileToCart(file: NerdmComp, cart: DataCart, selected: boolean =false, dosave: boolean =true) : DataCartItem {
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
        
        setTimeout(() => {
            for (let child of this.files) 
                this._addAllWithinToCart(child, downloadAllCart, true);
            downloadAllCart.save();
            this.isAddingToDownloadAllCart = false;
            window.open('/datacart/'+cartName, cartName);
        }, 0);
    }

    /**
     * mark a file as downloaded in the data cart.  This will happen if the user clicks on the 
     * individual file download icon.
     */
    setFileDownloaded(rowData: DataFileItem) : void {
        if (this.globalDataCart) {
            this.globalDataCart.restore();
            this.globalDataCart.setDownloadStatus(this.record.ediid, rowData.comp.filepath);
        }
    }

    /*
     * Note: downloadOneFile() and downloadAllFromUrl() are currently not used
     */
    
    /**
     * Downloaded one file
     * @param rowData - tree node
     */
    downloadOneFile(rowData: any) {
        let filename = decodeURI(rowData.downloadUrl).replace(/^.*[\\\/]/, '');
        rowData.downloadStatus = DownloadStatus.DOWNLOADING;
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
        }else{
            return "500px";
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
