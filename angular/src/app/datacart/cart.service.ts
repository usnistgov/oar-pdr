import { CartConstants } from './cartconstants';
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { Observable } from 'rxjs';
import { DataCart } from '../datacart/cart';

/**
 * The cart service provides a way to store the cart in local store.
 **/
@Injectable()
export class CartService {
    public CART_CONSTANTS: any;
    cartLengthSub = new BehaviorSubject<number>(0);
    selectedFileCountSub = new BehaviorSubject<number>(0);
    private _storage = null;

    constructor() 
    {
        this.CART_CONSTANTS = CartConstants.cartConst;

        // localStorage will be undefined on the server
        if (typeof (localStorage) !== 'undefined')
            this._storage = localStorage;
    }

    /**
     * Watch the cart length
     */
    watchCartLength(): Observable<any> {
        return this.cartLengthSub.asObservable();
    }

    /**
     * Set the number of selected cart items
     **/
    setSelectedFileCount(selectedFileCount: number) {
        this.selectedFileCountSub.next(selectedFileCount);
    }

    /**
     * Watch the number of selected cart items
     **/
    watchSelectedFileCount(subscriber) {
        return this.selectedFileCountSub.subscribe(subscriber);
    }
    
    /**
     * Set the number of cart items
     **/
    setCartLength(value: number) {
        this.cartLengthSub.next(value);
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
     * Reset datafile download status. Because this is a recursive function, the datacart should be opened and saved outside this function
     * otherwise it will take a long time for a large dataset. 
     * @param dataFiles 
     * @param dataCart 
     * @param downloadStatus 
     */
    // resetDatafileDownloadStatus(dataFiles: any, dataCart: DataCart, downloadStatus: string) {
    //     for (let i = 0; i < dataFiles.length; i++) {
    //         if (dataFiles[i].children.length > 0) {
    //             this.resetDatafileDownloadStatus(dataFiles[i].children, dataCart, downloadStatus);
    //         } else {
    //             dataFiles[i].data.downloadStatus = downloadStatus;
    //             dataCart.setDownloadStatus(dataFiles[i].data.resId, dataFiles[i].data.filePath, downloadStatus);
    //         }
    //     }
    // }

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
