/**
 * Non-GUI classes and interfaces for managing the contents of a data cart.  This does *not* include 
 * downloading functionality.
 */
import { TreeNode } from 'primeng/api';

import { Observable, BehaviorSubject } from 'rxjs';

import { NerdmComp } from '../nerdm/nerdm';

/**
 * convert the TreeNode[] data to a string appropriate for saving to local storage
 */
export function stringifyCart(data: DataCartLookup) : string { return JSON.stringify(data); }

/**
 * parse a string pulled from local storage into TreeNode[] data 
 */
export function parseCart(datastr: string) : DataCartLookup {
    return <DataCartLookup>((datastr) ? JSON.parse(datastr) : {});
}

/**
 * a data structure describing a file in the cart.  A CartEntryData object, in effect, is a NerdmComp 
 * that *must* have the filePath property and is expected to have some additional 
 * data cart-specific properties.  
 */
export interface DataCartItem {

    /**
     * a local identifier for resource.  This must not start with an underscore as this is reserved.  
     */
    resId? : string;

    /**
     * the path to the file within its resource file hierarchy.  
     */
    filePath : string;

    /**
     * the URL from where the file can be downloaded
     */
    downloadURL? : string;

    /**
     * a label indicating whether the file has been downloaded yet.  If downloading of this file can 
     * be considered complete, the value will be "downloaded"
     */
    downloadStatus? : string;

    /**
     * a flag indicating if the item has been added to the user's global cart
     */
    isIncart? : boolean;

    /**
     * other parameters are expected
     */
    [propName: string]: any;
}

/**
 * a mapping of DataCartItems by their identifiers
 */
export interface DataCartLookup {
    /**
     * property names are data cart item (slash-delimited) identifiers
     */
    [propName: string]: DataCartItem;
}

/**
 * a container for the contents of a data cart.  This manages persisting the content data to the 
 * user's (via the browser) local disk.  
 */
export class DataCart {

    contents: DataCartLookup = {};      // the list of files in this cart
    cartName: string = null             // the name for this data cart; this is the name it is persisted under
    _storage: Storage = null;           // the persistant storage; if null, this cart is in-memory only

    // Caution: in the current application, this Observerable is not likely to work.  
    // Different listeners--namely a landing page and a data cart window--are not expected to execute
    // in the same runtime space; thus, they can't share their updates to a cart in real time via a Subject
    // 
    // private _statusUpdated = new BehaviorSubject<boolean>(false);   // for alerts about changes to the cart

    /**
     * initialize this cart.  This is not intended to be called directly by users; the static functions
     * should be used instead.
     */
    constructor(name: string, data?: DataCartLookup, store: Storage|null = localStorage) {
        this.cartName = name;
        if (data) this.contents = data;
        this._storage = store;  // if null; cart is in-memory only
    }

    /**
     * return the DataCart from persistent storage.  If it does not exist, create an empty one.
     */
    public static openCart(id: string, store: Storage = localStorage) : DataCart {
        let data: DataCartLookup = <DataCartLookup>{};
        if (store) {
            data = parseCart(store.getItem("cart:"+id));
            if (! data)
                return DataCart.createCart(id, store);
        }
        return new DataCart(id, data, store);
    }

    /**
     * create a new empty DataCart with the given ID and register it into persistent storage.  If 
     * a DataCart already exists with that ID, it will be discarded.
     */
    public static createCart(id: string, store: Storage = localStorage) : DataCart {
        let out: DataCart = new DataCart(id, <DataCartLookup>{}, store);
        out.save();
        return out;
    }

    /**
     * save the contents of this cart to its persistent storage
     */
    public save() : void {
        if (this._storage)
            this._storage.setItem("cart:"+this.cartName, stringifyCart(this.contents));
    }

    /**
     * delete the contents of this cart from persistent storage
     */
    public forget() : void {
        if (this._storage)
            this._storage.removeItem("cart:"+this.cartName);
    }

    /**
     * restore the content of this cart from the last save to persistent storage.  Clients should call 
     * this if they want to ensure they have the latest changes to the cart.  
     */
    public restore() : void {
        if (this._storage)
            this.contents = parseCart(this._storage.getItem("cart:"+this.cartName));
    }

    /**
     * count and return the total number of files in this cart
     */
    public size() : number {
        return Object.keys(this.contents).length;
    }

    /**
     * get the key of this cart
     */
    public getKey() : string {
        return "cart:"+this.cartName;
    }

    /**
     * count and return the total number of files currently marked as downloaded
     */
    public countFilesDownloaded() : number {
        return Object.values(this.contents).filter((c,i?,a?) => {
            return c['downloadStatus'] == "downloaded";
        }).length;
    }

    /**
     * count and return the total number of files currently marked as selected
     */
    public countFilesSelected() : number {
        return Object.values(this.contents).filter((c,i?,a?) => {
            return c['isSelected'] == true;
        }).length;
    }

    /**
     * find the file entry in the contents of this cart with the given file ID or null if the 
     * ID does not exist. 
     * @param cartId    the ID of the file within this cart
     * @return DataCartItem  -- the matching file item
     */
    findFileById(cartId: string) : DataCartItem {
        return this.contents[cartId];
    }

    /**
     * find the file entry in the contents of this cart with the given file ID or null if the 
     * ID does not exist. 
     * @param resId     the local identifier for the resource that the file is from
     * @param filePath  the path to the file within the resource collection.
     */
    public findFile(resId: string, filePath: string) : DataCartItem {
        return this.findFileById(this._idFor(resId, filePath));
    }

    public findItem(item: DataCartItem) {
        return this.findFileById(this._idFor(item['resId'], item['filePath']));
    }

    private _idFor(resId: string, filePath: string) { 
        if(filePath[0] != '/')
            return resId+'/'+filePath; 
        else 
            return resId+filePath; 
    }
    private _idForItem(item: DataCartItem) {
        return this._idFor(item['resId'], item['filePath']);
    }

    /**
     * add a DataCartItem to the cart
     */
    addItem(item: DataCartItem) : void {
        this.contents[this._idForItem(item)] = item;
        // this._statusUpdated.next(true);
    }

    /**
     * add a file to this data cart.  The item must have filePath and a downloadURL properties
     * @param resid   a repository-local identifier for the resource that the file is from
     * @param file    the DataCartItem or NerdmComp that describes the file being added.
     */
    addFile(resid: string, file: DataCartItem|NerdmComp, markSelected: boolean = false) : void {
        let fail = function(msg: string) : void {
            console.error("Unable to load file NERDm component: "+msg+": "+JSON.stringify(file));
        }
        if (! resid) return fail("Missing resid argument");
        if (! file['filePath']) return fail("missing component property, filePath");
        if (! file['downloadURL']) return fail("missing component property, downloadURL");

        let item = JSON.parse(JSON.stringify(file));
        item['resId'] = resid;
        if (item['downloadStatus'] === undefined)
            item['downloadStatus'] = "";
        item['isSelected'] = markSelected;
        this.addItem(item);
    }

    /**
     * remove a single file from the cart as given by its identifiers.  
     * @param resid     a repository-local identifier for the resource that the file is from
     * @param filePath  the path to the file within the resource collection to remove.
     * @return boolean -- true if the file was found to be in the cart and then removed. 
     */
    public removeFileById(resid: string, filePath: string, updateCart: boolean = false) : boolean {
        if(updateCart) this.restore();

        let id = this._idFor(resid, filePath);

        let found = this.contents[id];
        if (found){ 
            delete this.contents[id];
        }

        if(updateCart) this.save();
        return !!found;
    }

    /**
     * Remove all files from cart - used by removeFilesFromCart()
     * @param files - file tree
     */
    removeFromTree(files: TreeNode[]) {
        for (let comp of files) {
            if (comp.children.length > 0) {
                comp.data.isIncart = false;
                this.removeFromTree(comp.children);
            } else {
                this.removeFileById(comp.data.resId,comp.data.filePath);
                // this.cartService.removeCartId(comp.data.cartId);
                comp.data.isIncart = false;
            }
        }
    }

    /**
     * Reset datafile download status. Because this is a recursive function, the datacart should be opened and saved outside this function
     * otherwise it will take a long time for a large dataset. 
     * @param dataFiles 
     * @param dataCart 
     * @param downloadStatus 
     */
    resetDatafileDownloadStatus(dataFiles: any, downloadStatus: string) {
        for (let i = 0; i < dataFiles.length; i++) {
            if (dataFiles[i].children.length > 0) {
                this.resetDatafileDownloadStatus(dataFiles[i].children, downloadStatus);
            } else {
                dataFiles[i].data.downloadStatus = downloadStatus;
                this.setDownloadStatus(dataFiles[i].data.resId, dataFiles[i].data.resFilePath, downloadStatus);
            }
        }
    }

    /**
     * Remove the selected data from the data cart
     * @param selectedData 
     */
    removeSelectedData(selectedData: any){
        for (let selData of selectedData) {
            if(!selData.data.isLeaf){
                    this.removeSelectedData(selData.children);
            }else{
                this.removeFileById(selData.data['resId'], selData.data['resFilePath'])
            }
        }
    }

    /**
     * remove a list of files
     */
    public removeFiles(files: DataCartItem[]) : void {
        this.restore();

        for (let file of files) 
            delete this.contents[this._idForItem(file)]

        this.save();
    }

    /**
     * mark a file as having been downloaded.
     * @param resId     the local identifier for the resource that the file is from
     * @param filePath  the path to the file within the resource collection.
     * @param downloadStatus  download status: "downloaded", "" or "failed".  
     * @return boolean -- true if the identified file was found in this cart and its status updated; 
     *                    false, otherwise.
     */
    public setDownloadStatus(resid: string, filePath: string, downloadedStatus: string = "downloaded", updateCart:boolean = false) : boolean {
        
        if(updateCart) this.restore();

        let item: DataCartItem = this.findFile(resid, filePath);
        if (! item){
            return false;
        }

        item.downloadStatus = downloadedStatus;

        if(updateCart) this.save();
        // this._statusUpdated.next(true);

        return true;
    }

    /**
     * if the given file description is in this cart, update its status to match those of the same files in this 
     * cart.  The status update includes whether the file has been downloaded,
     * and, if markInCart=true (default), whether it is in this cart.  
     *
     * @return boolean -- if the file is has been marked as downloaded (by this function or previously)
     */
    public updateStatusOfFile(file: DataCartItem|NerdmComp, resid: string, markInCart: boolean=true) : boolean {
        let mine : DataCartItem = this.findFile(resid, file['filePath']);
        if (mine) {
            if (typeof mine['downloadStatus'] == 'string')
                file['downloadStatus'] = mine['downloadStatus'];
            if (markInCart) file['inCart'] = true;
        }
        else if (markInCart) 
            file['inCart'] = false;
        
        return (file['downloadStatus'] == 'downloaded');
    }

    /**
     * update the status of the files in a given cart to match those of the same files in this 
     * cart.  The status update includes whether the file has been downloaded,
     * and, if markInCart=true (default), whether it is in this cart.  
     * Files in the given cart that are not in this cart are ignored.  
     *
     * @return number -- the total number of files in the given cart that are now marked as downloaded;
     *                   if this number equals cart.size(), then all files are marked as downloaded. 
     */
    public updateFileStatusInCart(cart: DataCart, markInCart: boolean=true) : number {
        let mine : DataCartItem = null
        let file : DataCartItem = null
        let dlcount = 0;
        for (let key in cart.contents) {
            file = cart.contents[key];
            if (this.updateStatusOfFile(file, file['resId'], markInCart))
                dlcount++;
        }

        return dlcount;
    }

    /**
     * mark the given file or collection as selected.  The filePath will first be searched for explicitly 
     * as if it points to a downloadable file; if not found, the filePath will be assumed to refer to a
     * collection; all files with a path that that starts with the given one will be marked as selected.
     * @param resId     the local identifier for the resource that the file is from
     * @param filePath  the path to the file within the resource collection.
     * @param unselect  if true, unselect the referenced files rather than selecting them
     */
    // public setSelected(resid: string, filePath: string = '', unselect: boolean = false) : void {
    //     this.restore();
    //     let match = this.matchFiles(resid, filePath);
    //     if (match.length) {
    //         for (let file of match) 
    //             file['isSelected'] = !unselect;
    //         this.save();
    //     }
    // }

    /**
     * return an array containing DataCartItem objects for file part of a resource with a given resource ID
     * and whose filePath starts with the given filePath.  If the IDs refer to a single file, the returned 
     * array will contain one element; if the ID refers to a collection, the returned array will list all 
     * of the files contained within the collection.
     * @param resId     the local identifier for the desired resource
     * @param filePath  the path to the file or subcollection within the resource collection; if an empty
     *                     string, all files from the resource will be returned.  
     */
    public matchFiles(resid: string, filePath: string = '') {
        let id = this._idFor(resid, filePath);
        let matched = this.contents[id]
        if (matched) return [matched];

        id += '/'
        let matched2 = Object.keys(this.contents).filter((k) => { return k.startsWith(id); });
        return matched2.map((k) => { return this.contents[k]; });
    }

    /**
     * return a list of the files in the cart
     */
    getFiles() : DataCartItem[] { return Object.values(this.contents); }

    /**
     * return a list of the selected files in the cart
     */
    getSelectedFiles() : DataCartItem[] {
        return Object.values(this.contents).filter( (f) => { return f['isSelected']; } );
    }

    /**
     * return a list of the downloaded files in the cart
     */
    getDownloadedFiles() : DataCartItem[] {
        return Object.values(this.contents).filter( (f) => { return f['downloadStatus'] == 'downloaded'; } );
    }

    /**
     * remove all of the selected files from this cart
     */
    public removeSelectedFiles() : void {
        this.removeFiles(this.getSelectedFiles());
    }

    /**
     * remove all of the selected files from this cart
     */
    public removeDownloadedFiles() : void {
        this.removeFiles(this.getDownloadedFiles());
    }

    /**
     * register to get alerts when files have been downloaded
     */
    // public watchForChanges(subscriber): void {
    //     this._statusUpdated.subscribe(subscriber);
    // }

    /**
     * Return cart items as an array for display purpose
     */
    getCartItems(): DataCartItem[]{
        let cartItems: DataCartItem[] = [];

        // convert the map to an array
        for (let key in this.contents) {
            let value = this.contents[key];
            cartItems.push(value);
        }
        // return the array
        return cartItems;
    }

    markAsDownloaded(resid: string, filePath: string = '', status: boolean = true){
        let found = this.findFile(resid, filePath);
        if(found){
            found.downloadStatus = status? "downloaded" : "";
            return true;
        }else{
            return false;
        }
    }
}
