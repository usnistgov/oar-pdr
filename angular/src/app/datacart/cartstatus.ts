/**
 * The purpose of this class is to help the communication among tabs. 
 * Since user can open multiple tabs with different ediid, the DataCart class cannot be used for this purpose.
 * With this class, we can tell the status of all DataCarts that are opened in this app - whether they are still in use 
 * and their download status.
 */

import { CartConstants } from './cartconstants';

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
    itemId: string; 
    displayName: string;
    isInUse: boolean = true; 
    downloadPercentage: number = 0; 

    /**
     * the status of the cart 
     */
    // statusData : DataCartStatusData;

    // constructor(itemId: string, statusData? : DataCartStatusData){
    //     this.itemId = itemId;
    //     if(!statusData){
    //         this.statusData = new DataCartStatusData();
    //     }else{
    //         this.statusData = statusData;
    //     }
    // }

    constructor(itemId: string, isInUse : boolean = true, downloadPercentage : number = 0, displayName? : string){
        this.itemId = itemId;
        this.displayName = displayName;
        this.isInUse = isInUse;
        this.downloadPercentage = downloadPercentage;
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
    public CART_CONSTANTS: any;
    name: string = "cartstatus";
    _storage: Storage = null;           // the persistant storage; if null, this cart is in-memory only
    dataCartStatusItems: DataCartStatusLookup = {};

    constructor(name: string = "cartstatus", dataCartStatusItems: DataCartStatusLookup, store: Storage|null = localStorage){
        this.CART_CONSTANTS = CartConstants.cartConst;
        this.name = name;
        if(dataCartStatusItems){
            this.dataCartStatusItems = dataCartStatusItems;
        }
        this._storage = store;  // if null; cart is in-memory only
    }

    /**
     * return the DataCart from persistent storage.  If it does not exist, create an empty one.
     */
    public static openCartStatus(cartName: string = "cartstatus", store: Storage = localStorage) : DataCartStatus {
        let cartstatusItems: DataCartStatusLookup = <DataCartStatusLookup>{};
        if (store) {
            cartstatusItems = parseCartStatus(store.getItem(cartName));
            if (!cartstatusItems)
                return DataCartStatus.createCartStatus(cartName, store);
        }
        return new DataCartStatus(cartName, cartstatusItems, store);
    }

    /**
     * create a new empty DataCartStatus with the given name and register it into persistent storage.  If 
     * a DataCartStatus already exists with that name, it will be discarded.
     */
    public static createCartStatus(name: string, store: Storage = localStorage) : DataCartStatus {
        let out: DataCartStatus = new DataCartStatus(name, <DataCartStatusLookup>{}, store);
        out.save();
        return out;
    }

    /**
     * save the contents of this cart to its persistent storage
     */
    public save() : void {
        if (this._storage)
            this._storage.setItem(this.name, stringifyCart(this.dataCartStatusItems));
    }

    /**
     * delete the contents of this cart from persistent storage
     */
    public forget() : void {
        if (this._storage)
            this._storage.removeItem(this.name);
    }

    /**
     * restore the content of this cart from the last save to persistent storage.  Clients should call 
     * this if they want to ensure they have the latest changes to the cart.  
     */
    public restore() : void {
        if (this._storage)
            this.dataCartStatusItems = parseCartStatus(this._storage.getItem(this.name));
    }

    /**
     * get the key of this cart
     */
    public getName() : string {
        return this.name;
    }

    /**
     * find the file entry in the contents of this cart with the given file ID or null if the 
     * ID does not exist. 
     * @param cartId    the ID of the file within this cart
     * @return DataCartItem  -- the matching file item
     */
    findStatusById(itemId: string) : DataCartStatusItem {
        return this.dataCartStatusItems[itemId];
    }

    /**
     * add a DataCartStatusItem to the cart
     */
    addItem(item: DataCartStatusItem) : void {
        this.restore();
        this.dataCartStatusItems[item.itemId] = item;
        this.save();
        // this._statusUpdated.next(true);
    }

    /**
     * remove a single item from the cartStatus as given by its cart name.  
     * @param cartName     cart name
     * @return boolean -- true if the item was found to be in the cart and then removed. 
     */
    public removeItemById(itemId: string) : boolean {
        this.restore();

        if (this.dataCartStatusItems[itemId]){ 
            delete this.dataCartStatusItems[itemId];
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
    public updateCartStatusInUse(itemId: string, inUse: boolean=false, displayName?: string){
        let targetItem : DataCartStatusItem = this.findStatusById(itemId);
        let lDisplayName: string = displayName;

        if(!lDisplayName) lDisplayName = itemId;
        
        if(!targetItem) {
            targetItem = new DataCartStatusItem(itemId, inUse, 0, displayName);
            this.addItem(targetItem);
        }else{
            targetItem.isInUse = inUse;
        }

        this.save();
    }

    /**
     * Update the download percentage of the given cart name
     * @param cartName The name of the cart to be updated
     * @param percentage Status to be updated
     */
    public updateDownloadPercentage(itemId: string, percentage: number=0, displayName: string=itemId){
        this.restore();
        let targetItem : DataCartStatusItem = this.findStatusById(itemId);
        if(targetItem){
            targetItem.downloadPercentage = percentage;
            this.save();
        }else{
            targetItem = new DataCartStatusItem(itemId, true, percentage, displayName);
            this.addItem(targetItem);
        }
    }

    /**
     * Clean up status storage - remove items whois not in use
     */
    cleanUpStatusStorage(){
        this.restore();
        for(let key in this.dataCartStatusItems){
            if(!this.dataCartStatusItems[key].isInUse){
                if (this.dataCartStatusItems[key].itemId != this.CART_CONSTANTS.GLOBAL_CART_NAME) 
                    this._storage.removeItem('cart:'+this.dataCartStatusItems[key].itemId);
                delete this.dataCartStatusItems[this.dataCartStatusItems[key].itemId];
            }
        }

        this.save();
    }
}