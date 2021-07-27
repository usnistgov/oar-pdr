/**
 * static utility functions useful across the application
 */

/**
 * Function to display bytes in an appropriate format with units
 **/
export function formatBytes(bytes: number, numAfterDecimal: number = null) : string {
    if (bytes == null || bytes == undefined) return '';
    if (0 == bytes) return "0 Bytes";
    if (1 == bytes) return "1 Byte";
    let base = 1000,
        e = ["Bytes", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"],
        d = numAfterDecimal || 1,
        f = Math.floor(Math.log(bytes) / Math.log(base));

    let v = bytes / Math.pow(base, f);
    if (f == 0) // less than 1 kiloByte
        d = 0;
    else if (numAfterDecimal == null && v < 10.0)
        d = 2;
    return v.toFixed(d) + " " + e[f];
}

/**
 * create a deep copy of a data object.  This does the copy by converting it to a JSON string
 * and parsing it back again; thus, the object must not be class instance, and it can only contain
 * JSON-encodable properties
 */
export function deepCopy(obj) {
    return JSON.parse(JSON.stringify(obj));
}

