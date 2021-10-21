export class MetricsData {
    hasCurrentMetrics: boolean;
    totalDatasetDownload: number;
    totalUsers: number;
    totalDownloadSize: number;
    url: string;

    constructor(hasCurrentMetrics:boolean = false, 
                totalDatasetDownload:number = 0, 
                totalUsers:number = 0,
                totalDownloadSize:number = 0,
                url:string = ""){

        this.hasCurrentMetrics = hasCurrentMetrics;
        this.totalDatasetDownload = totalDatasetDownload;
        this.totalUsers = totalUsers;
        this.totalDownloadSize = totalDownloadSize;
        this.url = url;
    }
}