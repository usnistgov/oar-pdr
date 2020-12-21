/**
 * The purpose of this class is to help the communication among tabs. 
 * Since user can open multiple tabs with different ediid, the DataCart class cannot be used for this purpose.
 * With this class, we can tell the status of all DataCarts that are opened in this app - whether they are still in use 
 * and their download status.
 */

/**
 * convert the TreeNode[] data to a string appropriate for saving to local storage
 */
export function stringifyCart(data: DataCartStatusLookup) : string { return JSON.stringify(data); }

/**
 * parse a string pulled from local storage into TreeNode[] data 
 */
export function parseCartStatus(datastr: string) : DataCartStatusLookup {
    return <DataCartStatusLookup>((datastr) ? JSON.parse(datastr) : {});
}

/**
 * a data structure describing the data in the DataCartStatus.  
 */
export class DataCartStatusData {
    isInUse: boolean = true;           // Indicate if this datacart is still in use (the tab is still open)
    downloadPercentage: number = 0;     // Percentage of total downloaded data

    constructor(isInUse: boolean = true, downloadPercentage: number = 0){
        this.isInUse = isInUse;
        this.downloadPercentage = downloadPercentage;
    }
}
/**
 * a data structure describing the data in the DataCartStatus.  
 */
export class DataCartStatusItem {

    /**
     * Identifier for the cart status data.    
     */
    cartName: string; 

    /**
     * the status of the cart 
     */
    statusData : DataCartStatusData;

    constructor(cartName: string, statusData? : DataCartStatusData){
        this.cartName = cartName;
        if(!statusData){
            this.statusData = new DataCartStatusData();
        }else{
            this.statusData = statusData;
        }
    }
}

/**
 * a mapping of DataCartItems by their identifiers
 */
export interface DataCartStatusLookup {
    /**
     * property names are data cart item (slash-delimited) identifiers
     */
    [propName: string]: DataCartStatusItem;
}

/**
 * a container for the contents of a data cart.  This manages persisting the content data to the 
 * user's (via the browser) local disk.  
 */
export class DataCartStatus {

    _storage: Storage = null;           // the persistant storage; if null, this cart is in-memory only
    dataCartStatusItems: DataCartStatusLookup = {};

    constructor(dataCartStatusItem: DataCartStatusLookup, store: Storage|null = localStorage){
        if(dataCartStatusItem){
            this.dataCartStatusItems = dataCartStatusItem;
        }
        this._storage = store;  // if null; cart is in-memory only
    }

    /**
     * return the DataCart from persistent storage.  If it does not exist, create an empty one.
     */
    public static openCartStatus(cartName: string, store: Storage = localStorage) : DataCartStatus {
        let cartstatusItems: DataCartStatusLookup = <DataCartStatusLookup>{};
        if (store) {
            cartstatusItems = parseCartStatus(store.getItem("cartstatus"));
            if (!cartstatusItems)
                return DataCartStatus.createCartStatus(cartstatusItems, store);
        }
        return new DataCartStatus(cartstatusItems, store);
    }

    /**
     * create a new empty DataCartStatus with the given name and register it into persistent storage.  If 
     * a DataCartStatus already exists with that name, it will be discarded.
     */
    public static createCartStatus(cartstatusItems: DataCartStatusLookup, store: Storage = localStorage) : DataCartStatus {
        let out: DataCartStatus = new DataCartStatus(cartstatusItems, store);
        out.save();
        return out;
    }

    /**
     * save the contents of this cart to its persistent storage
     */
    public save() : void {
        if (this._storage)
            this._storage.setItem("cartstatus", stringifyCart(this.dataCartStatusItems));
    }

    /**
     * delete the contents of this cart from persistent storage
     */
    public forget() : void {
        if (this._storage)
            this._storage.removeItem("cartstatus");
    }

    /**
     * restore the content of this cart from the last save to persistent storage.  Clients should call 
     * this if they want to ensure they have the latest changes to the cart.  
     */
    public restore() : void {
        if (this._storage)
            this.dataCartStatusItems = parseCartStatus(this._storage.getItem("cartstatus"));
    }

    /**
     * find the file entry in the contents of this cart with the given file ID or null if the 
     * ID does not exist. 
     * @param cartId    the ID of the file within this cart
     * @return DataCartItem  -- the matching file item
     */
    findStatusByName(cartName: string) : DataCartStatusItem {
        return this.dataCartStatusItems[cartName];
    }

    /**
     * add a DataCartStatusItem to the cart
     */
    addItem(item: DataCartStatusItem) : void {
        this.restore();
        this.dataCartStatusItems[item.cartName] = item;
        this.save();
        // this._statusUpdated.next(true);
    }

    /**
     * remove a single item from the cartStatus as given by its cart name.  
     * @param cartName     cart name
     * @return boolean -- true if the item was found to be in the cart and then removed. 
     */
    public removeItemByName(cartName: string) : boolean {
        this.restore();

        if (this.dataCartStatusItems[cartName]){ 
            delete this.dataCartStatusItems[cartName];
            this.save();
            return true;
        }
        return false;
    }

    /**
     * Update the inUse status of the given cart name
     * @param cartName The name of the cart to be updated
     * @param inUse Status to be updated
     */
    public updateCartStatusInUse(cartName: string, inUse: boolean=false){
        let targetItem : DataCartStatusItem = this.findStatusByName(cartName);
        targetItem.statusData.isInUse = inUse;
    }

    /**
     * Update the download percentage of the given cart name
     * @param cartName The name of the cart to be updated
     * @param percentage Status to be updated
     */
    public updateDownloadPercentahe(cartName: string, percentage: number=0){
        let targetItem : DataCartStatusItem = this.findStatusByName(cartName);
        targetItem.statusData.downloadPercentage = percentage;
    }
}