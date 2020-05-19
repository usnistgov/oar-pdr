import { Injectable } from '@angular/core';

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
            e = ["Bytes", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"],
            d = numAfterDecimal || 1,
            f = Math.floor(Math.log(bytes) / Math.log(base));

        var v = bytes / Math.pow(base, f);
        if (f == 0) // less than 1 kiloByte
            d = 0;
        else if (numAfterDecimal == null && v < 10.0)
            d = 2;
        return v.toFixed(d) + " " + e[f];
    }

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
        if(fileSize >= 1000000000)
            displaySize = Math.round(fileSize / 1000000000) + " GB";
        else if(fileSize >= 1000000)
            displaySize = Math.round(fileSize / 1000000) + " MB";
        else if(fileSize >= 1000)
            displaySize = (fileSize / 1000).toFixed(2) + " KB";
        else
            displaySize = fileSize + " Bytes";

        return displaySize;
    }    
}
