/**
 * Non-GUI classes and interfaces for managing the contents of a data cart.  This does *not* include 
 * downloading functionality.
 */
import { Observable, Subject } from 'rxjs';

import { NerdmComp } from '../nerdm/nerdm';
import { CartConstants, DownloadStatus } from './cartconstants';

/**
 * convert a data cart contents to a string appropriate for saving to local storage
 */
export function stringifyCart(data: DataCartLookup) : string { return JSON.stringify(data); }
export function stringifyMD(data: DataCartMD) : string { return JSON.stringify(data); }

/**
 * parse a string pulled from local storage into data cart contents
 */
export function parseCart(datastr: string) : DataCartLookup {
    return <DataCartLookup>((datastr) ? JSON.parse(datastr) : {});
}
export function parseMD(datastr: string) : DataCartMD {
    return <DataCartMD>((datastr) ? JSON.parse(datastr) : null);
}

/**
 * a data structure describing a file in the cart.  A CartEntryData object, in effect, is a NerdmComp 
 * that *must* have the filePath property and is expected to have some additional 
 * data cart-specific properties.  
 */
export interface DataCartItem {
    /**
     * a unique key for identifying this item.  
     */
    key? : string;

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
     * true if this item has been selected (for download)
     */
    isSelected? : boolean;

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

interface DataCartMD {
    /**
     * the epoch time when this data was updated last
     */
    updated : number;

    /**
     * a display name set for this cart
     */
    dispName?: string;
}

/**
 * a container for the contents of a data cart.  This manages persisting the content data to the 
 * user's (via the browser) local disk.  It can be watched for changes.
 *
 * The contents can be accessed via the "contents" property, which itself is a javascript object where 
 * the properties are file properties and the values are DataCartItem objects describe a file in the cart 
 * and its status.  
 * 
 * Gemerally, watchers and users should instantiate a cart directly but rather get a cart via 
 * a CartService (injected) instance.  The service will ensure that all clients receive the same instance
 * of the cart, thereby having a synchronized view of its contents.  
 */
export class DataCart {

    public CART_CONSTANTS: any = CartConstants.cartConst;
    contents: DataCartLookup = {};      // the list of files in this cart
    cartName: string = null;            // the name for this data cart; this is the name it is persisted under
    dispName: string = null;            // a name for this cart to use for display purposes
    _storage: Storage = null;           // the persistant storage; if null, this cart is in-memory only
    lastUpdated: number = 0;            // epoch time the contents were last updated; used to control updates
                                        //    to subscribers

    private _statusUpdated = new Subject<any>();   // for alerts about changes to the cart

    /**
     * initialize this cart.  This is not intended to be called directly by users; the static functions
     * should be used instead.
     */
    constructor(name: string, data?: DataCartLookup, store: Storage|null = localStorage, update: number = 0) {
        this.cartName = name;
        if (data) this.contents = data;
        this._storage = store;  // if null; cart is in-memory only
        this.lastUpdated = update;

        // watch for changes that occur in other browser tabs/windows
        if (this._storage && window) 
            window.addEventListener("storage", this._checkForUpdate.bind(this))
    }

    /**
     * return the DataCart from persistent storage.  If it does not exist, create an empty one.
     */
    public static openCart(id: string, store: Storage = localStorage) : DataCart {
        let data: DataCartLookup = <DataCartLookup>{};
        let md: string = null;
        if (store) {
            data = parseCart(store.getItem(DataCart.storeKeyFor(id)));
            if (! data) 
                return DataCart.createCart(id, store);
            md = store.getItem(DataCart.storeKeyFor(id)+".md");
        }
        return new DataCart(id, data, store, (md != null) ? parseMD(md).updated : 0);
    }

    /**
     * create a new empty DataCart with the given ID and register it into persistent storage.  If 
     * a DataCart already exists with that ID, it will be discarded.
     */
    public static createCart(id: string, store: Storage = localStorage) : DataCart {
        let out: DataCart = new DataCart(id, <DataCartLookup>{}, store);
        if (out.isGlobalCart()) out.setDisplayName("Global Data Cart", false);
        out.save();
        return out;
    }

    static storeKeyFor(id: string) : string {
        return "cart:"+id;
    }

    /**
     * save the contents of this cart to its persistent storage
     */
    public save() : void {
        this.lastUpdated = Date.now();
        if (this._storage) {
            this._storage.setItem(this.getStoreKey()+".md", stringifyMD(this._updatedMD(this.lastUpdated))); 
            this._storage.setItem(this.getStoreKey(), stringifyCart(this.contents));
        }

        // alert watchers.  (Note that a window-originating event will only occur if the cart
        // was changed from _another_ window/tab; thus, no worry about double alerts.)
        this._alertWatchers(this.lastUpdated);
    }

    private _alertWatchers(when : number) : void {
        this._statusUpdated.next({
            cartName: this.cartName,
            when: when
        });
    }        

    private _updatedMD(time : number) : DataCartMD {
        return { updated: time, dispName: this.dispName };
    }

    /**
     * delete the contents of this cart from persistent storage
     */
    _forget() : void {
        if (this._storage) {
            this._storage.removeItem(this.getStoreKey());
            this._storage.removeItem(this.getStoreKey()+".md");
        }
    }

    /**
     * restore the content of this cart from the last save to persistent storage.  Clients should call 
     * this if they want to ensure they have the latest changes to the cart.  
     */
    public restore() : void {
        if (this._storage) {
            let md : DataCartMD|null = this._getStoreMD();
            this.lastUpdated = (md != null) ? md.updated : Date.now();
            this.dispName = (md != null && md.dispName) ? md.dispName : null;
            this.contents = parseCart(this._storage.getItem(this.getStoreKey()));
        }
    }

    /*
     * check to see if this cart has been updated via another instance
     */
    _checkForUpdate(ev) : void {
        if (ev.key != this.getStoreKey())
            // not this cart
            return;

        let md : DataCartMD|null = this._getStoreMD();
        if (md == null)
            // not saved yet (or was forgotten)
            return;
        if (md.updated > this.lastUpdated) {
            // another instance updated this cart
            this.restore();
            this._alertWatchers(md.updated);
        }
    }

    private _getStoreMD() : DataCartMD|null {
        if (this._storage) 
            return parseMD(this._storage.getItem(this.getStoreKey()+".md"));
        return null;
    }

    /**
     * count and return the total number of files in this cart
     */
    public size() : number {
        return Object.keys(this.contents).length;
    }

    /** 
     * return the name of this cart
     */
    public getName() : string { return this.cartName; }

    /**
     * return true if this cart serves as the global data cart
     */
    public isGlobalCart() : boolean { return this.cartName == this.CART_CONSTANTS.GLOBAL_CART_NAME; }

    /**
     * return a default name to use for display purposes.  If this is not a global cart, the resource title
     * associated with the first item in the cart will be returned.
     */
    public getDisplayName() : string {
        if (this.dispName)
            return this.dispName;
        if (this.isGlobalCart())
            return "Global Data Cart";
        if (this.contents && Object.keys(this.contents).length > 0 &&
            this.contents[Object.keys(this.contents)[0]].name)
        {
            let key = Object.keys(this.contents)[0];
            return this.contents[key].resTitle || this.contents[key].resId;
        }
        return this.cartName;
    }

    /**
     * set a name to use for display purposes for this cart
     */
    public setDisplayName(name: string, dosave: boolean = true) : void {
        if (this.dispName != name) {
            this.dispName = name;
            if (dosave) this.save();
        }
    }

    /**
     * get the key of this cart
     */
    public getStoreKey() : string {
        return DataCart.storeKeyFor(this.cartName);
    }

    /**
     * count and return the total number of files currently marked as downloaded
     */
    public countFilesDownloaded() : number {
        return Object.values(this.contents).filter((c,i?,a?) => {
            return c['downloadStatus'] == DownloadStatus.DOWNLOADED;
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

    private _idFor(resId: string, filePath: string) : string {
        return DataCart.itemKeyFor(resId, filePath);
    }

    static itemKeyFor(resId: string, filePath: string) : string {
        let localid = resId || '';
        localid = localid.replace(/^ark:\/\d+\//, '');
        if(filePath[0] != '/')
            return localid+'/'+filePath; 
        else 
            return localid+filePath; 
    }
    private _idForItem(item: DataCartItem) {
        return item['key'];
    }

    /**
     * add a DataCartItem to the cart
     */
    addItem(item: DataCartItem, dosave: boolean = true) : void {
        this.contents[this._idForItem(item)] = item;

        if (dosave) this.save();
    }

    /**
     * add a file to this data cart.  The item must have filePath and a downloadURL properties.
     * If the file is already in the cart, it will be replaced with the given description.  If
     * the given file is a NerdmComp, all of the component metadata will be added as extra metadata
     * to the saved DataCartItem (e.g. mediaType, size, etc.).  
     * @param resid   a repository-local identifier for the resource that the file is from
     * @param file    the DataCartItem or NerdmComp that describes the file being added.
     * @param markSelected   if true, the new file will be marked as selected
     * @param dosave         if true, the updated cart contents will be added after adding the file
     * @return DataCartItem -- the item representing the file that was added to the cart
     */
    addFile(resid: string, file: DataCartItem|NerdmComp,
            markSelected: boolean = false, dosave: boolean = true) : DataCartItem
    {
        let fail = function(msg: string) : DataCartItem {
            console.error("Unable to load file NERDm component: "+msg+": "+JSON.stringify(file));
            return null;
        }
        if (! resid) return fail("Missing resid argument");
        if (! file['filePath'] && ! file['filepath']) return fail("missing component property, filepath");
        if (! file['downloadURL']) return fail("missing component property, downloadURL");

        let item = JSON.parse(JSON.stringify(file));
        item['resId'] = resid;
        if (! item['filePath']) {
            item['filePath'] = item['filepath']
            delete item['filepath']
        }
        item['key'] = this._idFor(resid, item['filePath']);
        if (item['downloadStatus'] === undefined)
            item['downloadStatus'] = "";
        item['isSelected'] = markSelected;
        this.addItem(item, dosave);
        return item;
    }

    /**
     * remove a single file from the cart as given by its identifiers.  
     * @param resid     a repository-local identifier for the resource that the file is from
     * @param filePath  the path to the file within the resource collection to remove.
     * @return boolean -- true if the file was found to be in the cart and then removed. 
     */
    public removeFileById(resid: string, filePath: string, dosave: boolean = true) : boolean {
        let id = this._idFor(resid, filePath);

        let found = this.contents[id];
        if (found) { 
            delete this.contents[id];
        }

        if (dosave) this.save();
        return !!found;
    }

    /**
     * remove a list of files
     */
    public removeFiles(files: DataCartItem[], dosave: boolean = true) : void {
        for (let file of files) 
            delete this.contents[this._idForItem(file)]

        if (dosave && files.length > 0) this.save();
    }

    /**
     * remove all files matching the given resource ID and filepath.  If filepath points to a collection,
     * all files in the cart that are part of that collection are removed.  
     * @param resId     the local identifier for the resource that the file is from
     * @param filePath  the path to a file or subcollection within the resource collection.  If empty, null,
     *                    or undefined, all files with the matching resId will be removed. 
     */
    public removeMatchingFiles(resId: string, filepath: string = '', dosave: boolean = true) : void {
        this.removeFiles(this.matchFiles(resId, filepath), dosave);
    }
    

    /**
     * mark a file as having been downloaded.
     * @param resId     the local identifier for the resource that the file is from
     * @param filePath  the path to the file within the resource collection.
     * @param downloadStatus  a string tag taken from the DownloadStatus constants representing the file's
     *                  download status
     * @param dosave    if true (default), commit the cart to storage after this update.  Set to false, when
     *                  making multiple updates, then call save() explicitly
     * @param extra     an optional object of additional properties to associate and save with this item.  If 
     *                  null (default), no additional properties are saved.  This object should not include 
     *                  standard properties from the DataCartItem interface definition.
     * @return boolean -- true if the identified file was found in this cart and its status updated; 
     *                    false, otherwise.
     */
    public setDownloadStatus(resid: string, filePath: string, downloadStatus: string = DownloadStatus.DOWNLOADED, 
                             dosave: boolean = true, extra: {[p:string]: any} = null) : boolean
    {
        let item: DataCartItem = this.findFile(resid, filePath);
        if (! item)
            return false;

        item.downloadStatus = downloadStatus;
        if (extra) 
            item = {...extra, ...item};

        if(dosave) this.save();

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
        let filepath = file['filePath'] || file['filepath'];
        let mine : DataCartItem = this.findFile(resid, file['filePath']);
        if (mine) {
            if (typeof mine['downloadStatus'] == 'string')
                file['downloadStatus'] = mine['downloadStatus'];
            if (markInCart) file['inCart'] = true;
        }
        else if (markInCart) 
            file['inCart'] = false;
        
        return (file['downloadStatus'] == DownloadStatus.DOWNLOADED);
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
    public setSelected(resid: string, filePath: string = '',
                       unselect: boolean = false, dosave: boolean = true) : void
    {
        let match = this.matchFiles(resid, filePath);
        if (match.length) {
            for (let file of match) 
                file['isSelected'] = !unselect;
            if (dosave) this.save();
        }
    }

    /**
     * return an array containing DataCartItem objects for file part of a resource with a given resource ID
     * and whose filePath starts with the given filePath.  If the IDs refer to a single file, the returned 
     * array will contain one element; if the ID refers to a collection, the returned array will list all 
     * of the files contained within the collection.
     * @param resId     the local identifier for the desired resource
     * @param filePath  the path to the file or subcollection within the resource collection; if an empty
     *                     string, all files from the resource will be returned.  
     */
    public matchFiles(resid: string, filePath: string = '') : DataCartItem[] {
        let id = this._idFor(resid, filePath);
        let matched = this.contents[id]
        if (matched) return [matched];

        id = resid || '';
        id = id.replace(/ark:\/\d+\//,'');
        if (filePath) id = id+'/'+filePath;
        id += '/';
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
        return Object.values(this.contents).filter( (f) => {
            return f['downloadStatus'] == DownloadStatus.DOWNLOADED;
        });
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
     * register to get alerts when files have been downloaded.  The subscriber is a function
     * that takes an event object that will have the foloowing properties:
     *    + cartName -- the name of the cart issuing the alert
     *    + when -- an integer representing the epoch time (milliseconds since 1/1/1970) of the cart update
     */
    public watchForChanges(subscriber): void {
        this._statusUpdated.subscribe(subscriber);
    }

    /**
     * Return cart items as an array for display purpose
     */
    getCartItems(): DataCartItem[] {
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
            found.downloadStatus = status ? DownloadStatus.DOWNLOADED : "";
            return true;
        }else{
            return false;
        }
    }
}
