export class MetricsData {
    hasCurrentMetrics: boolean;
    totalDatasetDownload: number;
    totalUsers: number;
    totalDownloadSize: number;
    url: string;
    dataReady: boolean;

    constructor(hasCurrentMetrics:boolean = false, 
                totalDatasetDownload:number = 0, 
                totalUsers:number = 0,
                totalDownloadSize:number = 0,
                url:string = "",
                dataReady: boolean = false){

        this.hasCurrentMetrics = hasCurrentMetrics;
        this.totalDatasetDownload = totalDatasetDownload;
        this.totalUsers = totalUsers;
        this.totalDownloadSize = totalDownloadSize;
        this.url = url;
        this.dataReady = dataReady;
    }
}