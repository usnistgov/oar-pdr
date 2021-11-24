/**
 * This module provide defined constant values used throughout the DataCartModule
 */

export class CartActions {
    public static get cartActions(): any { 
        return {
            CREATE: 'create',
            REMOVE_ITEM: 'remove_item',
            ADD_ITEM: 'add_item',
            SET_IN_USE: 'set_in_use',
            SET_PERCENTAGE: "set_percentage",
            SET_DOWNLOAD_COMPLETE: "set_download_complete",
            CLEANUP_STATUS: "cleanup_status"
        }
    }
}


export class CartConstants {
    public static get cartConst(): any { 
        return {
            GLOBAL_CART_NAME: 'global_datacart',
            CART_STATUS_STORAGE_NAME: 'cartstatus'
        }
    }
}

/**
 * constants representing the download status of a file in a cart.  
 */
export class DownloadStatus {

    /** the last attempt to download the file was successful */
    static readonly DOWNLOADED = 'downloaded';

    /** 
     * the process for downloading a set of bundle files is finished.  This applies specifically 
     * to a collection of bundle (zip) files, rather than any individual file in a cart.
     */
    static readonly COMPLETED = 'complete';

    /** the file is currently being downloaded */
    static readonly DOWNLOADING = 'downloading';

    /** the file is currently being downloaded */
    static readonly PENDING = 'pending';

    /** a warning was issued while attempting or preparing to download the file */
    static readonly WARNING = 'warning';

    /** the last attempt to download the file was canceled while it was in progress */
    static readonly CANCELED = 'canceled';

    /** the last attempt to download the file failed */
    static readonly FAILED = 'failed';

    /** the last attempt to download the file encountered an error */
    static readonly ERROR = 'error';

    /** downloading this file has yet to be attempted or queued */
    static readonly NO_STATUS = '';
}

