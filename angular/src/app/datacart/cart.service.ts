import { CartConstants } from './cartconstants';
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { Observable } from 'rxjs';
import * as _ from 'lodash';
import 'rxjs/add/operator/toPromise';
import { DataCart } from '../datacart/cart';

/**
 * The cart service provides a way to store the cart in local store.
 **/
@Injectable()
export class CartService {
    public CART_CONSTANTS: any;
    storageSub = new BehaviorSubject<number>(0);
    selectedFileCountSub = new BehaviorSubject<number>(0);
    addCartSpinnerSub = new BehaviorSubject<boolean>(false);
    addAllCartSpinnerSub = new BehaviorSubject<boolean>(false);
    displayCartSub = new BehaviorSubject<boolean>(false);
    cartEntitesReadySub = new BehaviorSubject<boolean>(false);
    forceDatacartReloadSub = new BehaviorSubject<boolean>(false);

    showAddCartSpinner: boolean = false;
    showAddAllCartSpinner: boolean = false;
    displayCart: boolean = false;
    private _storage = null;
    currentCart: string;
    statusStorageName: string;

    constructor(
        private http: HttpClient) 
    {
        this.CART_CONSTANTS = CartConstants.cartConst;
        this.currentCart = this.CART_CONSTANTS.GLOBAL_CART_NAME;
        this.statusStorageName = this.CART_CONSTANTS.CART_STATUS_STORAGE_NAME;

        // localStorage will be undefined on the server
        if (typeof (localStorage) !== 'undefined')
            this._storage = localStorage;
    }

    watchStorage(): Observable<any> {
        return this.storageSub.asObservable();
    }

    watchAddFileCart(): Observable<any> {
        return this.addCartSpinnerSub.asObservable();
    }

    watchAddAllFilesCart(): Observable<any> {
        return this.addAllCartSpinnerSub.asObservable();
    }

    /**
     * Set the number of cart items
     **/
    setSelectedFileCount(selectedFileCount: number) {
        this.selectedFileCountSub.next(selectedFileCount);
    }

    watchSelectedFileCount(subscriber) {
        return this.selectedFileCountSub.subscribe(subscriber);
    }
    
    private emptyMap(): { [key: string]: number; } {
        return {};
    }

    /**
     * Cart status is used to determine if current cart is still in use. When a new tab opens for certain 
     * ediid, the ediid will be 'registered' in the storage whose name is defined in this.statusStorageName 
     * and the status will be set to 'open'. When the tab is closed, the status will be set to 'close'.
     * When landing page starts up, it will clean up all storages whose status is 'close'. The reason to
     * clean up the storage in this way is to handle the refresh of the tab - when a tab refreshes, it
     * will set the status to 'close' then 'open'. But if a tab closes, it only sets the status to 'close'.
     * 
     * @param status the status of the current cart
     */
    setCartStatus(cartID: string, status: string){
        if (this._storage) {
            let cartStatusObj: any = JSON.parse(this._storage.getItem(this.statusStorageName));

            if(cartStatusObj == undefined) cartStatusObj = {};
            cartStatusObj[cartID] = {status: status};

            this._storage.removeItem(this.statusStorageName);
            this._storage.setItem(this.statusStorageName, JSON.stringify(cartStatusObj));
        }
    }

    /**
     * Return the status of the current cart - 'open' or 'close'. Undefined ot empty means current
     * cart hasn't been processed before.
     */
    getCartStatus(){
        if (!this._storage)
            return '';
        else{
            let cartStatusObj = JSON.parse(this._storage.getItem(this.statusStorageName));
            return cartStatusObj[this.currentCart];
        }
    }

    /**
     * Clean up status storage - remove items whose status is not 'open'
     */
    cleanUpStatusStorage(){
        if (this._storage){
            let oldCartStatusObj = JSON.parse(this._storage.getItem(this.statusStorageName));
            let newCartStatusObj: any = {};

            for (let key in oldCartStatusObj) {
                if(oldCartStatusObj[key]['status'] == 'open'){
                    newCartStatusObj[key] = { status: 'open' };
                }else{
                    this._storage.removeItem(key);
                }
            }
            this._storage.removeItem(this.statusStorageName);
            this._storage.setItem(this.statusStorageName, JSON.stringify(newCartStatusObj));
        }
    }

    /**
     * Set the number of cart items
     **/
    setCartLength(value: number) {
        this.storageSub.next(value);
    }

    /**
     * Behavior subject to remotely start the control function.
     */
    private _remoteCommand : BehaviorSubject<any> = new BehaviorSubject<any>({});
    _watchRemoteCommand(subscriber) {
        this._remoteCommand.subscribe(subscriber);
    }

    /**
     * Execute the remote command
     */
    public executeCommand(command: string = "", data: any = null) : void {
        this._remoteCommand.next({'command':command, 'data': data});
    }

    /**
     * Reset datafile download status
     **/
    resetDatafileDownloadStatus(dataFiles: any, dataCart: DataCart, downloadStatus: string) {
        for (let i = 0; i < dataFiles.length; i++) {
            if (dataFiles[i].children.length > 0) {
                this.resetDatafileDownloadStatus(dataFiles[i].children, dataCart, downloadStatus);
            } else {
                dataFiles[i].data.downloadStatus = downloadStatus;
                dataCart.setDownloadStatus(dataFiles[i].data.resId, dataFiles[i].data.filePath, downloadStatus);
            }
        }

        dataCart.save();
    }

    /**
     * Return "download" button color based on download status
     */
    getDownloadStatusColor(downloadStatus: string) {
        let returnColor = '#1E6BA1';

        switch (downloadStatus) {
            case 'downloaded':
                {
                    returnColor = 'green';
                    break;
                }
            case 'downloading':
                {
                    returnColor = '#00ace6';
                    break;
                }
            case 'warning':
                {
                    returnColor = 'darkorange';
                    break;
                }
            case 'cancelled':
                {
                    returnColor = 'darkorange';
                    break;
                }
            case 'failed':
                {
                    returnColor = 'darkorange';
                    break;
                }
            case 'error':
                {
                    returnColor = 'red';
                    break;
                }
            default:
                {
                    //statements; 
                    break;
                }
        }

        return returnColor;
    }

    /**
     * The status we want to display may not be exactly the same as the status in the database. This function 
     * serves as a mapper.
     * @param rowData - row data of dataFiles
     */
    getStatusForDisplay(downloadStatus: string){
        let status = "";
        switch(downloadStatus){
            case 'complete':
                status = 'Completed';
                break;
            case 'downloaded':
                status = 'Downloaded';
                break;
            case 'downloading':
                status = 'Downloading';
                break;
            case 'pending':
                status = 'Pending';
                break;
            case 'cancelled':
                status = 'Cancelled';
                break;
            case 'failed':
                status = 'Failed';
                break;
            case 'error':
                status = 'Error';
                break;  
            default:
                break;    
        }

        return status;
    }    

    /**
     * Return icon class based on download status
     */
    getIconClass(downloadStatus: string){
        let iconClass = "";
        switch(downloadStatus){
            case 'complete':
                iconClass = 'faa faa-check';
                break;
            case 'downloaded':
                iconClass = 'faa faa-check';
                break;
            case 'pending':
                iconClass = 'faa faa-clock-o';
                break;
            case 'cancelled':
                iconClass = 'faa faa-remove';
                break;
            case 'failed':
                iconClass = 'faa faa-warning';
                break;
            case 'error':
                iconClass = 'faa faa-warning';
                break;  
            default:
                break;              
        }

        return iconClass; 
    }

}
