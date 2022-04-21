import { Injectable } from '@angular/core';

/**
 * DEPRECATED!
 */
@Injectable({
    providedIn: 'root'
})
export class CommonFunctionService {
    constructor() { }

    /**
    * Function to display bytes in appropriate format.
    **/
    formatBytes(bytes, numAfterDecimal) {
        if (bytes == null || bytes == undefined) return '';
        if (0 == bytes) return "0 Bytes";
        if (1 == bytes) return "1 Byte";
        var base = 1000,
            e = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"],
            d = numAfterDecimal || 1,
            f = Math.floor(Math.log(bytes) / Math.log(base));

        var v = bytes / Math.pow(base, f);
        if (f == 0) // less than 1 kiloByte
            d = 0;
        else if (numAfterDecimal == null && v < 10.0)
            d = 2;
        return v.toFixed(d) + ' ' + e[f];
    }

    /**
     * Make a deep copy of an object
     * @param obj 
     * @returns copy of the input object
     */
    deepCopy(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    /**
     *  Convert the file size into display format
     * @param fileSize - input file size in byte
     */
    getSizeForDisplay(fileSize: number)
    {
        let displaySize = "";
        let dm = 0;
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        const i = Math.floor(Math.log(fileSize) / Math.log(k));

        if(i > 2) dm = 2;

        return parseFloat((fileSize / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }    
}
