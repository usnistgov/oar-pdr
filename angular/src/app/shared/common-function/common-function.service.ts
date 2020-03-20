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
}
