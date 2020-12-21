import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { ZipData } from './zipData';
import { DownloadData } from './downloadData';
import { CartService } from '../../datacart/cart.service';
import { TestDataService } from '../../shared/testdata-service/testDataService';
import { FileSaverService } from 'ngx-filesaver';
import { TreeNode } from 'primeng/primeng';
import { DataCart } from '../../datacart/cart';

@Injectable()
export class DownloadService {
    zipFilesDownloadingSub = new BehaviorSubject<number>(0);
    zipFilesProcessedSub = new BehaviorSubject<boolean>(false);

    zipFilesDownloadingDataCartSub = new BehaviorSubject<number>(0);
    zipFilesProcessedDataCartSub = new BehaviorSubject<boolean>(false);

    anyFileDownloadedFlagSub = new BehaviorSubject<boolean>(false);
    totalFileDownloadedSub = new BehaviorSubject<number>(0);

    private download_maximum: number = 2;
    _totalBundleSize = 0;
    _totalDownloaded = 0;
    _downloadSpeed = 0.00;
    //By default, download time is calculated every 20sec. But when it's closed to finish, this interval need be changed to 10s, 5s or 1s accordingly.
    _displayInterval = 20; 
    _overallDownloadTime = 0;

    constructor(
        private http: HttpClient,
        private cartService: CartService,
        private _FileSaverService: FileSaverService,
        private testDataService: TestDataService
    ) {
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
     **/
    getDownloadMaximum() {
        return this.download_maximum;
    }

    /**
    * Get file from a given url
    **/
    getFile(url, params): Observable<Blob> {
        return this.http.get(url, { responseType: 'blob', params: params });
    }

    /**
     * Calling end point 1 to get the bundle plan
     **/
    getBundlePlan(url: string, body: any): Observable<any> {
        const httpOptions = {
            headers: new HttpHeaders({
                'Content-Type': 'application/json'
            })
        };
        return this.http.post(url, body, httpOptions);
    }

    /**
    * Calling end point 2 to get the bundle
    **/
    getBundle(url, body): Observable<any> {
        const request = new HttpRequest(
            "POST", url, body,
            { headers: new HttpHeaders({ 'Content-Type': 'application/json', 'responseType': 'blob' }), reportProgress: true, responseType: 'blob' });

        return this.http.request(request);
    }

    /**
     * Download zip
     **/
    download(nextZip: ZipData, zipdata: ZipData[], dataFiles: any, dataCart: DataCart) {
        let sub = this.zipFilesDownloadingDataCartSub;
        let preTime: number = 0;
        let preTime2: number = 0;
        let preDownloaded: number = 0;
        let preDownloaded2: number = 0;
        let currentTime: number = 0;
        let currentDownloaded: number = 0;

        nextZip.downloadStatus = 'downloading';
        this.setDownloadStatus(nextZip, dataFiles, "downloading", dataCart);
        this.increaseNumberOfDownloading();

        // console.log('nextZip.bundleSize', nextZip.bundleSize);
        nextZip.downloadInstance = this.getBundle(nextZip.downloadUrl, JSON.stringify(nextZip.bundle)).subscribe(
            event => {
                switch (event.type) {
                    case HttpEventType.Response:
                        nextZip.downloadStatus = 'Writing data to destination';
                        this._FileSaverService.save(<any>event.body, nextZip.fileName);
                        nextZip.downloadProgress = 0;
                        nextZip.downloadStatus = 'downloaded';
                        this.decreaseNumberOfDownloading();
                        this.setDownloadProcessStatus(this.allDownloadFinished(zipdata));
                        this.setDownloadStatus(nextZip, dataFiles, "downloaded", dataCart);
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
                console.log('Error:', err);
                console.log('Download details:', nextZip);
                nextZip.downloadStatus = 'error';
                nextZip.downloadErrorMessage = err.message;
                nextZip.downloadProgress = 0;
                this.decreaseNumberOfDownloading();
                this.setDownloadStatus(nextZip, dataFiles, "failed", err.message);
            }
        );
    }

    /**
     * Decrease the number of current downloading by 1
     **/
    decreaseNumberOfDownloading() {
        let sub = this.zipFilesDownloadingDataCartSub;

        if (sub.getValue() >= 0) {
            this.setDownloadingNumber(sub.getValue() - 1);
        }

        if (sub.getValue() == 0) {
            this.setDownloadProcessStatus(true);
        }
    }

    /**
     * Increase the number of current downloading by 1
     **/
    increaseNumberOfDownloading() {
        let sub = this.zipFilesDownloadingDataCartSub;

        if (sub.getValue() < this.getDownloadMaximum()) {
            this.setDownloadingNumber(sub.getValue() + 1);
        }
    }

    /**
     * Download next available zip in the queue
     **/
    downloadNextZip(zipData: ZipData[], dataFiles: any, dataCart: DataCart) {
        let sub = this.zipFilesDownloadingDataCartSub;

        if (sub.getValue() < this.getDownloadMaximum()) {
            let nextZip = this.getNextZipInQueue(zipData);
            if (nextZip != null) {
                this.download(nextZip, zipData, dataFiles, dataCart);
            }
        }
    }

    /**
     * Return next available zip in the queue
     **/
    getNextZipInQueue(zipData: ZipData[]) {
        let zipQueue = zipData.filter(item => item.downloadStatus == null);

        if (zipQueue.length > 0) {
            return zipQueue[0];
        } else {
            return null;
        }
    }

    /**
     * Generate downloadData from a given file tree that will be used to create post message for bundle plan
     **/
    getDownloadData(files: any, downloadData: any) {
        let existItem: any;
        for (let comp of files) {
            if (comp.children.length > 0) {
                this.getDownloadData(comp.children, downloadData);
            } else {
                if (comp.data['resFilePath'] != null && comp.data['resFilePath'] != undefined) {
                    if (comp.data['resFilePath'].split(".").length > 1) {
                        existItem = downloadData.filter(item => item.filePath === comp.data['ediid'] + comp.data['resFilePath']
                            && item.downloadUrl === comp.data['downloadUrl']);

                        if (existItem.length == 0) {
                            downloadData.push({ "filePath": comp.data['ediid'] + comp.data['resFilePath'], 'downloadUrl': comp.data['downloadUrl'] });
                        }
                    }
                }
            }
        }
    }

    /**
    * Set the number of downloading zip files
    **/
    watchDownloadingNumber(): Observable<any> {
        let sub = this.zipFilesDownloadingDataCartSub;
        return sub.asObservable();
    }

    /**
     * Set the number of downloading zip files
     **/
    setDownloadingNumber(value: number) {
        let sub = this.zipFilesDownloadingDataCartSub;
        sub.next(value);
    }

    /**
    * Watch overall process status
    **/
    watchDownloadProcessStatus(): Observable<any> {
        let sub = this.zipFilesProcessedDataCartSub;
        return sub.asObservable();
    }

    /**
     * Set overall process status
     **/
    setDownloadProcessStatus(value: boolean) {
        let sub = this.zipFilesProcessedDataCartSub;
        sub.next(value);
    }

    /**
     * Set download status of given tree node
     **/
    setDownloadStatus(zip: any, dataFiles: any, status: any, dataCart: DataCart, message: string = '') {
        for (let includeFile of zip.bundle.includeFiles) {
            let resFilePath = includeFile.filePath.substring(includeFile.filePath.indexOf('/'));
            for (let dataFile of dataFiles) {
                let node = this.searchTreeByfilePath(dataFile, resFilePath);
                if (node != null) {
                    node.data.downloadStatus = status;
                    node.data.message = message;
                    dataCart.setDownloadStatus(node.data.resId, node.data.filePath);

                    break;
                }
            }
        }

        dataCart.save();
    }

    /**
     * Check if all zip files are downloaded
     **/
    allDownloaded(zipData: any) {
        for (let zip of zipData) {
            if (zip.downloadStatus != 'downloaded') {
                return false;
            }
        }
        return true;
    }

    /**
     * Check if all doanload processes have finished
     **/
    allDownloadFinished(zipData: any) {
        for (let zip of zipData) {
            if (zip.downloadStatus == null || zip.downloadStatus == 'downloading') {
                return false;
            }
        }
        return true;
    }

    /**
     * Search tree by given full path
     **/
    searchTreeByfilePath(element, resFilePath) {
        if (element.data.isLeaf && element.data.resFilePath == resFilePath) {
            return element;
        } else if (element.children.length > 0) {
            var i;
            var result = null;
            for (i = 0; result == null && i < element.children.length; i++) {
                result = this.searchTreeByfilePath(element.children[i], resFilePath);
            }
            return result;
        }
        return null;
    }

    /**
     * Return total downloaded zip files from a given zipData 
     **/
    getDownloadedNumber(zipData: any) {
        let totalDownloadedZip: number = 0;
        for (let zip of zipData) {
            if (zip.downloadStatus == 'downloaded') {
                totalDownloadedZip += 1;
            }
        }
        return totalDownloadedZip;
    }

    /**
     * Reset element's zip files to null
     **/
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
     **/
    setFileDownloadedFlag(value: boolean) {
        this.anyFileDownloadedFlagSub.next(value);
    }

    /**
     * Watch general download flag
     **/
    watchAnyFileDownloaded(): Observable<any> {
        return this.anyFileDownloadedFlagSub.asObservable();
    }


    /**
     * Set the number of files downloaded
     **/
    setTotalFileDownloaded(fileDownloadedCount: number) {
        this.totalFileDownloadedSub.next(fileDownloadedCount);
    }

    watchTotalFileDownloaded(subscriber) {
        return this.totalFileDownloadedSub.subscribe(subscriber);
    }

    /**
     * Return total number of downloaded files in a given dataFiles (tree)
     **/
    getTotalDownloadedFiles(dataFiles: any) {
        let totalDownloaded: number = 0;
        for (let comp of dataFiles) {
            if (comp.children.length > 0) {
                totalDownloaded += this.getTotalDownloadedFiles(comp.children);
            } else {
                if (comp.data.downloadStatus == 'downloaded') {
                    totalDownloaded += 1;
                }
            }
        }
        return totalDownloaded;
    }

    /**
     *  Cancel the download process of the given zip file
     * @param zip - the zip file to be cancelled
     */
    cancelDownloadZip(zip: ZipData, dataFiles: TreeNode[], dataCart: DataCart) {
        //Need to re-calculate the total file size and total downloaded size
        this.decreaseTotalBundleBySize(zip.bundleSize);
        let downloaded = this.totalDownloaded - zip.bundleSize*zip.downloadProgress/100;
        this.setTotalDownloaded(downloaded);

        zip.downloadInstance.unsubscribe();
        zip.downloadInstance = null;
        zip.downloadProgress = 0;
        zip.downloadStatus = "cancelled";
        this.setDownloadStatus(zip, dataFiles, "cancelled", dataCart);
        this.decreaseNumberOfDownloading();
    }
}