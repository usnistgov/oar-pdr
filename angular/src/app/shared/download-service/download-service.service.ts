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

    private max_concur_download: number = 2;
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
     * Get bundle plan from the given url
     * @param url - end point
     * @param body - message body
     */
    getBundlePlan(url: string, body: any): Observable<any> {
        const httpOptions = {
            headers: new HttpHeaders({
                'Content-Type': 'application/json'
            })
        };
        return this.http.post(url, body, httpOptions);
    }

    /**
     * Get bundle from the given url
     * @param url - end point
     * @param body - message body
     */
    getBundle(url, body): Observable<any> {
        const request = new HttpRequest(
            "POST", url, body,
            { headers: new HttpHeaders({ 'Content-Type': 'application/json', 'responseType': 'blob' }), reportProgress: true, responseType: 'blob' });

        return this.http.request(request);
    }

    /**
     * Download zip data
     * @param nextZip - zip to be downloaded
     * @param zipdata - zip queue. To check if all zips have been downloaded.
     * @param dataFiles - data tree
     * @param dataCart - data cart: update the download status so other tab can be updated.
     */
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

        nextZip.downloadInstance = this.getBundle(nextZip.downloadUrl, JSON.stringify(nextZip.bundle)).subscribe(
            event => {
                switch (event.type) {
                    case HttpEventType.Response:
                        nextZip.downloadStatus = 'Writing data to destination';
                        this._FileSaverService.save(<any>event.body, nextZip.fileName);
                        nextZip.downloadProgress = 0;
                        nextZip.downloadStatus = 'downloaded';
                        this.decreaseNumberOfDownloading();
                        if(this.allDownloadFinished(zipdata))
                            this.setDownloadProcessStatus(true);

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
     * @param dataFiles - the data tree. For updating the download status.
     * @param dataCart - data cart: update the download status so other tab can be updated.
     */
    downloadNextZip(zipData: ZipData[], dataFiles: any, dataCart: DataCart) {
        let sub = this.zipFilesDownloadingDataCartSub;

        if (sub.getValue() < this.getMaxConcurDownload()) {
            let nextZip = this.getNextZipInQueue(zipData);
            if (nextZip != null) {
                this.download(nextZip, zipData, dataFiles, dataCart);
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
     * Generate downloadData from a given file tree that will be used to create post message for bundle plan
     * @param files - input file tree
     * @param downloadData - output download data
     */
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
     * Set download status of given zip
     * @param zip - input zip file that has download status in it's include files
     * @param dataFiles - file tree that to be set the download status
     * @param status - download status
     * @param dataCart - data cart that to be set the download status - keep other tab in sync
     * @param message - any message that need to be added to the tree 
     */
    setDownloadStatus(zip: any, dataFiles: any, status: any, dataCart: DataCart, message: string = '') {
        let resFilePath: string;

        dataCart.restore();
        
        for (let includeFile of zip.bundle.includeFiles) {
            resFilePath = includeFile.filePath;

            if(includeFile.filePath.indexOf('ark:') >= 0){
                resFilePath = includeFile.filePath.replace('ark:/88434/', '');
            }
            resFilePath = resFilePath.substring(resFilePath.indexOf('/'));
            for (let dataFile of dataFiles) {
                let node = this.searchTreeByfilePath(dataFile, resFilePath);
                if (node != null) {
                    node.data.downloadStatus = status;
                    node.data.message = message;
                    node.data.zipFile = zip.fileName;
                    dataCart.setDownloadStatus(node.data.resId, node.data.resFilePath, status);

                    break;
                }
            }
        }

        dataCart.save();
    }

    /**
     * Check if all doanload processes have finished
     * @param zipData 
     */
    allDownloadFinished(zipData: any) {
        for (let zip of zipData) {
            if (zip.downloadStatus == null || zip.downloadStatus == 'downloading') {
                return false;
            }
        }
        return true;
    }

    /**
     * Search a given tree by given full path
     * @param tree 
     * @param resFilePath 
     */
    searchTreeByfilePath(tree, resFilePath) {
        if (tree.data.isLeaf && tree.data.resFilePath == resFilePath) {
            return tree;
        } else if (tree.children.length > 0) {
            var i;
            var result = null;
            for (i = 0; result == null && i < tree.children.length; i++) {
                result = this.searchTreeByfilePath(tree.children[i], resFilePath);
            }
            return result;
        }
        return null;
    }

    /**
     * Return total downloaded zip files from a given zipData
     * @param zipData 
     */
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
     * Return total number of downloaded files in a given dataFiles (tree)
     * @param dataFiles 
     */
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
     * Cancel the download process of the given zip file
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