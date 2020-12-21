export class Bundleplan {
    bundlePlanStatus: string;
    bundlePlanMessage: any[];
    bundlePlanUnhandledFiles: any[];
    bundlePlanRef: any;
    messageColor: string;

    constructor(){
        this.bundlePlanStatus = "";
        this.bundlePlanMessage = [];
        this.bundlePlanUnhandledFiles = null;
        this.bundlePlanRef = null;
        this.messageColor = "black";
    }
}