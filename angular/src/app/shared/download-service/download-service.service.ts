import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BehaviorSubject, throwError } from 'rxjs/index';
import { map, catchError } from 'rxjs/operators';
import { AppConfig } from '../../config/config';
import { ZipData } from './zipData';
import { DownloadData } from './downloadData';
import { CartService } from '../../datacart/cart.service';
import { DataCartItem } from '../../datacart/cart';
import { TestDataService } from '../../shared/testdata-service/testDataService';
import { FileSaverService } from 'ngx-filesaver';
import { DataCart } from '../../datacart/cart';
import { DownloadStatus } from '../../datacart/cartconstants';

@Injectable()
export class DownloadService {
    distApi : string = null;
    zipFilesDownloadingSub = new BehaviorSubject<number>(0);
    zipFilesProcessedSub = new BehaviorSubject<boolean>(false);

    zipFilesDownloadingDataCartSub = new BehaviorSubject<number>(0);
    zipFilesProcessedDataCartSub = new BehaviorSubject<boolean>(false);

    anyFileDownloadedFlagSub = new BehaviorSubject<boolean>(false);
    totalFileDownloadedSub = new BehaviorSubject<number>(0);

    private max_concur_download: number = 2;
    _totalBundleSize = 0;
    _totalDownloaded = 0;
    _downloadSpeed = 0.00;
    //By default, download time is calculated every 20sec. But when it's closed to finish, this interval need be changed to 10s, 5s or 1s accordingly.
    _displayInterval = 20; 
    _overallDownloadTime = 0;

    constructor(
        private cfg: AppConfig,
        private http: HttpClient,
        private cartService: CartService,
        private _FileSaverService: FileSaverService,
        private testDataService: TestDataService
    ) {
        this.distApi = this.cfg.get("distService", "/od/ds/");
        this.setDownloadingNumber(-1);
    }

    /**
     *  Return total downloaded size in bytes
     */
    get totalDownloaded()
    {
        return this._totalDownloaded;
    }

    /**
     * Set total downloaded size. Used by cancel function.
     * @param downloaded  
     */
    setTotalDownloaded(downloaded: number)
    {
        this._totalDownloaded = downloaded;
    }

    /**
     * Return total bundle size
     */
    get totalBundleSize()
    {
        return this._totalBundleSize;
    }

    /**
     * Set total bundle size
     * @param size 
     */
    setTotalBundleSize(size: number)
    {
        this._totalBundleSize = size;
    }

    /**
     * Increase total bundle size by input number
     * @param size 
     */
    increaseTotalBundleBySize(size: number)
    {
        this._totalBundleSize += size;
    }

    /**
     * Increase total bundle size by input number
     * @param size 
     */
    decreaseTotalBundleBySize(size: number)
    {
        this._totalBundleSize -= size;
    }

    /**
     * Return estimated overall download time
     */
    get overallDownloadTime()
    {
        return this._overallDownloadTime;
    }

    /**
     *  Return current download speed
     */
    public get downloadSpeed()
    {
        return this._downloadSpeed;
    }

    /**
     *  Reset download data
     */
    resetDownloadData()
    {
        this._totalDownloaded = 0;
        this._downloadSpeed = 0.00;
        this._totalBundleSize = 0;
        this._overallDownloadTime = 0;
    }

    /**
     * Return max download instances allowed at same time
     */
    getMaxConcurDownload() {
        return this.max_concur_download;
    }

    /**
     * Get file from a given url
     * @param url 
     * @param params 
     */
    getFile(url, params): Observable<Blob> {
        return this.http.get(url, { responseType: 'blob', params: params });
    }

    /**
     * Get a bundle plan for a given list of data (from the cart).
     *
     * The returned Observable object is object returned from the service with an extra property added 
     * to it called 'diagnostics'; this property encodes extra information about the call made to the 
     * server that can aid in handling problems in the response.  The diagnostics property is an object 
     * with the following fields:
     *   url        the URL the plan request was sent to (via POST)
     *   time       the datetime that a response came back
     *   body       the message that was POSTed to the URL (as a string)
     *   error      an error message if the response status was something other than 200; if successful,
     *                 this property is not set (i.e. undefined).
     * If the HTTP POST fails, the subscriber's error handler function will be passed this diagnostics object. 
     * @param planname    a name for the plan; this is used as the base name for each bundle file returned
     *                    in the plan
     * @param files       the list of files (as pulled from the data cart) to be downloaded
     * @return Observable of bundle plan object returned by the bundle service (with diagnostic info added)
     */
    getBundlePlan(planName : string, files : DataCartItem[]) : Observable<any> {
        // create the request body
        let reqfiles = [];
        for (let item of files) {
            reqfiles.push({
                "filePath": item.resId + '/' + item.filePath,
                "downloadUrl": item.downloadURL
            });
        }

        let body: string = JSON.stringify({
            "bundleName": planName,
            "includeFiles": reqfiles
        });
        let diagnostics = {
            'url':   this.distApi + '_bundle_plan',
            'body':  body
        };

        // submit the request and return the Observable result; add some diagnostic information on the way out
        let url = this.distApi + "_bundle_plan";
        console.log("Requesting bundle plan for " + reqfiles.length + " from " + url)
        return this._getBundlePlan(url, body).pipe(
            map(plan => {
                diagnostics['time'] = Date();
                plan['diagnostics'] = diagnostics;
                return plan;
            }),
            catchError(err => {
                diagnostics['time'] = Date();
                diagnostics['error'] = err;
                return throwError(diagnostics);
            })
        );
    }

    /**
     * Submit the bundle plan request and return a plan
     * @param url - end point
     * @param body - message body
     * @return Observable of bundle plan object returned by the bundle service
     */
    _getBundlePlan(url: string, body: any): Observable<any> {
        const httpOptions = {
            headers: new HttpHeaders({
                'Content-Type': 'application/json'
            })
        };
        return this.http.post(url, body, httpOptions);
    }

    /**
     * request a single bundle from a plan
     * @param relurl   the URL relative to the distribution service's base URL to retrieve the URL from
     * @param bundle   the bundle description object for assembling the bundle zip file
     */
    getBundle(relurl, bundle) : Observable<any> {
        return this._getBundle(this.distApi + relurl, JSON.stringify(bundle));
    }

    /**
     * Get bundle from the given url
     * @param url - end point
     * @param body - message body
     */
    _getBundle(url, body): Observable<any> {
        const request = new HttpRequest(
            "POST", url, body,
            { headers: new HttpHeaders({ 'Content-Type': 'application/json', 'responseType': 'blob' }), reportProgress: true, responseType: 'blob' });

        return this.http.request(request);
    }

    /**
     * Download zip data
     * @param nextZip - zip to be downloaded
     * @param zipdata - zip queue. To check if all zips have been downloaded.
     * @param dataCart - data cart: update the download status so other tab can be updated.
     */
    download(nextZip: ZipData, zipdata: ZipData[], dataCart: DataCart) {
        let sub = this.zipFilesDownloadingDataCartSub;
        let preTime: number = 0;
        let preTime2: number = 0;
        let preDownloaded: number = 0;
        let preDownloaded2: number = 0;
        let currentTime: number = 0;
        let currentDownloaded: number = 0;

        nextZip.downloadStatus = DownloadStatus.DOWNLOADING;
        this.setDownloadStatus(nextZip, DownloadStatus.DOWNLOADING, dataCart);
        this.increaseNumberOfDownloading();

        nextZip.downloadInstance = this.getBundle(nextZip.downloadUrl, nextZip.bundle).subscribe(
            event => {
                switch (event.type) {
                    case HttpEventType.Response:
                        nextZip.downloadStatus = 'Writing data to destination';
                        this._FileSaverService.save(<any>event.body, nextZip.fileName);
                        nextZip.downloadProgress = 0;
                        nextZip.downloadStatus = DownloadStatus.DOWNLOADED;
                        this.decreaseNumberOfDownloading();
                        if(this.allDownloadFinished(zipdata))
                            this.setDownloadProcessStatus(true);

                        this.setDownloadStatus(nextZip, DownloadStatus.DOWNLOADED, dataCart);
                        this.setFileDownloadedFlag(true);
                        break;
                    case HttpEventType.DownloadProgress:
                        if (nextZip.bundleSize > 0) {
                            nextZip.downloadProgress = Math.round(100 * event.loaded / nextZip.bundleSize);

                            //Estimate download time every 20sec
                            if(preTime == 0){   // init
                                preTime = new Date().getTime() / 1000;
                                preTime2 = preTime;
                                preDownloaded = event.loaded;
                                preDownloaded2 = event.loaded;
                                currentTime = new Date().getTime() / 1000;
                                currentDownloaded = event.loaded;
                                this._totalDownloaded += currentDownloaded;
                            }else{
                                currentTime = new Date().getTime() / 1000;
                                currentDownloaded = event.loaded;
                                this._totalDownloaded += currentDownloaded - preDownloaded;

                                if(currentTime - preTime2 > this._displayInterval) 
                                {
                                    this._downloadSpeed = (currentDownloaded - preDownloaded2)/(currentTime - preTime2);

                                    if(this._downloadSpeed > 0)
                                    {
                                        nextZip.downloadTime = Math.round((nextZip.bundleSize-event.loaded)*(currentTime - preTime2)/(currentDownloaded - preDownloaded2));

                                        this._overallDownloadTime = Math.round((this._totalBundleSize-this._totalDownloaded)/this._downloadSpeed)
                                    }
                                    preTime2 = currentTime;
                                    preTime = currentTime;
                                    preDownloaded = currentDownloaded;
                                    preDownloaded2 = currentDownloaded;

                                    if(nextZip.downloadTime > 60) this._displayInterval = 20;
                                    else if(nextZip.downloadTime > 40) this._displayInterval = 10;
                                    else if(nextZip.downloadTime > 20) this._displayInterval = 5;
                                    else this._displayInterval = 1;
                                }else
                                {
                                    preTime = currentTime;
                                    preDownloaded = currentDownloaded;
                                }
                            }
                        }
                        break;
                    default:
                        break;
                }

            },
            err => {
                console.error('Error:', err);
                console.log('Download details:', nextZip);
                nextZip.downloadStatus = DownloadStatus.ERROR;
                nextZip.downloadErrorMessage = err.message;
                nextZip.downloadProgress = 0;
                this.decreaseNumberOfDownloading();
                this.setDownloadStatus(nextZip, DownloadStatus.FAILED, dataCart, err.message);
            }
        );
    }

    /**
     * Decrease the number of current downloading by 1. If it becomes -1 which means all downloadings
     * are done, set the process status to done.
     */
    decreaseNumberOfDownloading() {
        let sub = this.zipFilesDownloadingDataCartSub;

        if (sub.getValue() >= 0) {
            this.setDownloadingNumber(sub.getValue() - 1);
        }

        if (sub.getValue() == -1) {
            this.setDownloadProcessStatus(true);
        }
    }

    /**
     * Increase the number of current downloading by 1. 
     */
    increaseNumberOfDownloading() {
        let sub = this.zipFilesDownloadingDataCartSub;

        if (sub.getValue() < this.getMaxConcurDownload()) {
            this.setDownloadingNumber(sub.getValue() + 1);
        }
    }

    /**
     * Download next available zip in the queue
     * @param zipData - zip queue
     * @param dataCart - data cart: update the download status so other tab can be updated.
     */
    downloadNextZip(zipData: ZipData[], dataCart: DataCart) {
        let sub = this.zipFilesDownloadingDataCartSub;

        if (sub.getValue() < this.getMaxConcurDownload()) {
            let nextZip = this.getNextZipInQueue(zipData);
            if (nextZip != null) {
                this.download(nextZip, zipData, dataCart);
            }
        }
    }

    /**
     * Return next available zip in the queue
     * @param zipData - zip queue
     */
    getNextZipInQueue(zipData: ZipData[]) {
        let zipQueue = zipData.filter(item => item.downloadStatus == null);

        if (zipQueue.length > 0) {
            return zipQueue[0];
        } else {
            return null;
        }
    }

    /**
     * Watching the number of the zip files that are currently downloading 
     */
    watchDownloadingNumber(): Observable<any> {
        let sub = this.zipFilesDownloadingDataCartSub;
        return sub.asObservable();
    }

    /**
     * Set the number of the zip files that are currently downloading 
     * @param value 
     */
    setDownloadingNumber(value: number) {
        let sub = this.zipFilesDownloadingDataCartSub;
        sub.next(value);
    }

    /**
     * Watch overall process status
     */
    watchDownloadProcessStatus(): Observable<any> {
        let sub = this.zipFilesProcessedDataCartSub;
        return sub.asObservable();
    }

    /**
     * Set overall process status
     * @param value 
     */
    setDownloadProcessStatus(value: boolean) {
        let sub = this.zipFilesProcessedDataCartSub;
        sub.next(value);
    }

    /**
     * Set download statuses of the data files being included in a given zip file
     * @param zip - the zip file that the files are being written to
     * @param status - a string tag indicating the new status to apply to the files
     * @param dataCart - the DataCart that the data files were drawn from.  (It's setDownloadStatus() 
     *                   function will be called for each file.)
     * @param message - a brief message (e.g. an error message) to associate with the files' status
     */
    setDownloadStatus(zip: ZipData, status: string, dataCart: DataCart, message: string = null) {
        let resFilePath: string = null;
        let resId: string = null;
        let p: number = -1;

        dataCart.restore();
        
        for (let includeFile of zip.bundle.includeFiles) {
            resFilePath = includeFile.filePath;
            if(includeFile.filePath.indexOf('ark:') >= 0){
                resFilePath = includeFile.filePath.replace(/ark:\/\d\//, '');
            }
            
            p = resFilePath.indexOf('/');
            if (p < 0) {
                console.warn("Unexpected filePath for member of bundle: "+resFilePath);
                continue;
            }
            resId = resFilePath.substring(0, p);
            resFilePath = resFilePath.substring(p+1);

            let extra = { zipFile: zip.fileName }
            if (message) 
                extra['message'] = message;

            dataCart.setDownloadStatus(resId, resFilePath, status, false, extra);
        }
        dataCart.save();
    }

    /**
     * Check if all doanload processes have finished
     * @param zipData 
     */
    allDownloadFinished(zipData: any) {
        for (let zip of zipData) {
            if (zip.downloadStatus == null || zip.downloadStatus == DownloadStatus.DOWNLOADING) {
                return false;
            }
        }
        return true;
    }

    /**
     * Return total downloaded zip files from a given zipData
     * @param zipData 
     */
    getDownloadedNumber(zipData: any) {
        let totalDownloadedZip: number = 0;
        for (let zip of zipData) {
            if (zip.downloadStatus == DownloadStatus.DOWNLOADED) {
                totalDownloadedZip += 1;
            }
        }
        return totalDownloadedZip;
    }

    /**
     * Reset element's zip files to null
     * @param element 
     */
    resetZipName(element) {
        if (element.data != undefined) {
            element.data.zipFile = null;
        }
        if (element.children.length > 0) {
            for (let i = 0; i < element.children.length; i++) {
                this.resetZipName(element.children[i]);
            }
        }
    }

    /**
     * Set general download flag
     * @param value 
     */
    setFileDownloadedFlag(value: boolean) {
        this.anyFileDownloadedFlagSub.next(value);
    }

    /**
     * Watch general download flag
     */
    watchAnyFileDownloaded(): Observable<any> {
        return this.anyFileDownloadedFlagSub.asObservable();
    }

    /**
     * Set the number of files downloaded
     * @param fileDownloadedCount 
     */
    setTotalFileDownloaded(fileDownloadedCount: number) {
        this.totalFileDownloadedSub.next(fileDownloadedCount);
    }

    /**
     * Watch the number of files downloaded
     * @param subscriber 
     */
    watchTotalFileDownloaded(subscriber) {
        return this.totalFileDownloadedSub.subscribe(subscriber);
    }

    /**
     * Cancel the download process of the given zip file
     * @param zip - the zip file to be cancelled
     */
    cancelDownloadZip(zip: ZipData, dataCart: DataCart) {
        //Need to re-calculate the total file size and total downloaded size
        this.decreaseTotalBundleBySize(zip.bundleSize);
        let downloaded = this.totalDownloaded - zip.bundleSize*zip.downloadProgress/100;
        this.setTotalDownloaded(downloaded);

        zip.downloadInstance.unsubscribe();
        zip.downloadInstance = null;
        zip.downloadProgress = 0;
        zip.downloadStatus = DownloadStatus.CANCELED;
        
        this.setDownloadStatus(zip, DownloadStatus.CANCELED, dataCart);
        this.decreaseNumberOfDownloading();
    }
}
