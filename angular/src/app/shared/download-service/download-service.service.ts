import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { ZipData } from './zipData';
import { DownloadData } from './downloadData';
import { CartService } from '../../datacart/cart.service';
import { TestDataService } from '../../shared/testdata-service/testDataService';
import { FileSaverService } from 'ngx-filesaver';

@Injectable()
export class DownloadService {
    zipFilesDownloadingSub = new BehaviorSubject<number>(0);
    zipFilesProcessedSub = new BehaviorSubject<boolean>(false);

    zipFilesDownloadingDataCartSub = new BehaviorSubject<number>(0);
    zipFilesProcessedDataCartSub = new BehaviorSubject<boolean>(false);

    anyFileDownloadedFlagSub = new BehaviorSubject<boolean>(false);
    private download_maximum: number = 2;
    _totalDownloaded = 0;
    _downloadSpeed = 0.00;


    constructor(
        private http: HttpClient,
        private cartService: CartService,
        private _FileSaverService: FileSaverService,
        private testDataService: TestDataService
    ) {
        this.setDownloadingNumber(-1, 'datacart');
    }

    /**
     *  Return total downloaded size in bytes
     */
    public get totalDownloaded()
    {
        return this._totalDownloaded;
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
    download(nextZip: ZipData, zipdata: ZipData[], dataFiles: any, whichPage: any) {
        let sub = this.zipFilesDownloadingSub;
        let preTime: number = 0;
        let preDownloaded: number = 0;
        let currentTime: number = 0;
        let currentDownloaded: number = 0;

        if (whichPage == "datacart") {
            sub = this.zipFilesDownloadingDataCartSub;
        }

        nextZip.downloadStatus = 'downloading';
        this.setDownloadStatus(nextZip, dataFiles, "downloading");
        this.increaseNumberOfDownloading(whichPage);

        console.log('nextZip.bundleSize', nextZip.bundleSize);
        nextZip.downloadInstance = this.getBundle(nextZip.downloadUrl, JSON.stringify(nextZip.bundle)).subscribe(
            event => {
                switch (event.type) {
                    case HttpEventType.Response:
                        nextZip.downloadStatus = 'Writing data to destination';
                        this._FileSaverService.save(<any>event.body, nextZip.fileName);
                        nextZip.downloadProgress = 0;
                        nextZip.downloadStatus = 'downloaded';
                        this.decreaseNumberOfDownloading(whichPage);
                        this.setDownloadProcessStatus(this.allDownloadFinished(zipdata), whichPage);
                        this.setDownloadStatus(nextZip, dataFiles, "downloaded");
                        this.setFileDownloadedFlag(true);
                        break;
                    case HttpEventType.DownloadProgress:
                        if (nextZip.bundleSize > 0) {
                            nextZip.downloadProgress = Math.round(100 * event.loaded / nextZip.bundleSize);

                            //Estimate download time every 20sec
                            if(preTime == 0){   // init
                                preTime = new Date().getTime() / 1000;
                                preDownloaded = event.loaded;
                                currentTime = new Date().getTime() / 1000;
                                currentDownloaded = event.loaded;
                                this._totalDownloaded += currentDownloaded;
                            }else{
                                currentTime = new Date().getTime() / 1000;
                                currentDownloaded = event.loaded;
                                
                                if(currentTime - preTime > 20) 
                                {
                                    this._totalDownloaded += currentDownloaded - preDownloaded;
                                    nextZip.downloadTime = Math.round((nextZip.bundleSize-event.loaded)*(currentTime - preTime)/(currentDownloaded - preDownloaded));
                                    this._downloadSpeed = (currentDownloaded - preDownloaded)/(currentTime - preTime);
                                    preTime = currentTime;
                                    preDownloaded = currentDownloaded;
                                }
                            }
                            new Date().getTime() / 1000;
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
                this.decreaseNumberOfDownloading(whichPage);
            }
        );
    }

    /**
     * Decrease the number of current downloading by 1
     **/
    decreaseNumberOfDownloading(whichPage: any) {
        let sub = this.zipFilesDownloadingSub;
        if (whichPage == "datacart") {
            sub = this.zipFilesDownloadingDataCartSub;
        }

        if (sub.getValue() >= 0) {
            this.setDownloadingNumber(sub.getValue() - 1, whichPage);
        }
    }

    /**
     * Increase the number of current downloading by 1
     **/
    increaseNumberOfDownloading(whichPage: any) {
        let sub = this.zipFilesDownloadingSub;
        if (whichPage == "datacart") {
            sub = this.zipFilesDownloadingDataCartSub;
        }

        if (sub.getValue() < this.getDownloadMaximum()) {
            this.setDownloadingNumber(sub.getValue() + 1, whichPage);
        }
    }

    /**
     * Download next available zip in the queue
     **/
    downloadNextZip(zipData: ZipData[], dataFiles: any, whichPage: any) {
        let sub = this.zipFilesDownloadingSub;
        if (whichPage == "datacart") {
            sub = this.zipFilesDownloadingDataCartSub;
        }
        if (sub.getValue() < this.getDownloadMaximum()) {
            let nextZip = this.getNextZipInQueue(zipData);
            if (nextZip != null) {
                this.download(nextZip, zipData, dataFiles, whichPage);
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
    watchDownloadingNumber(whichPage: any): Observable<any> {
        let sub = this.zipFilesDownloadingSub;
        if (whichPage == "datacart") {
            sub = this.zipFilesDownloadingDataCartSub;
        }

        return sub.asObservable();
    }

    /**
     * Set the number of downloading zip files
     **/
    setDownloadingNumber(value: number, whichPage: any) {
        let sub = this.zipFilesDownloadingSub;
        if (whichPage == "datacart") {
            sub = this.zipFilesDownloadingDataCartSub;
        }

        sub.next(value);
    }

    /**
    * Watch overall process status
    **/
    watchDownloadProcessStatus(whichPage: any): Observable<any> {
        let sub = this.zipFilesProcessedSub;
        if (whichPage == "datacart") {
            sub = this.zipFilesProcessedDataCartSub;
        }

        return sub.asObservable();
    }

    /**
     * Set overall process status
     **/
    setDownloadProcessStatus(value: boolean, whichPage: any) {
        let sub = this.zipFilesProcessedSub;
        if (whichPage == "datacart") {
            sub = this.zipFilesProcessedDataCartSub;
        }

        sub.next(value);
    }

    /**
     * Set download status of given tree node
     **/
    setDownloadStatus(zip: any, dataFiles: any, status: any) {
        for (let includeFile of zip.bundle.includeFiles) {
            let resFilePath = includeFile.filePath.substring(includeFile.filePath.indexOf('/'));
            for (let dataFile of dataFiles) {
                let node = this.searchTreeByfilePath(dataFile, resFilePath);
                if (node != null) {
                    node.data.downloadStatus = status;
                    this.cartService.updateCartItemDownloadStatus(node.data['cartId'], status);
                    break;
                }
            }
        }
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
}