import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http'; 
import {Observable } from 'rxjs';
import {BehaviorSubject } from 'rxjs/BehaviorSubject';
import { CommonVarService } from '../../shared/common-var';
import { ZipData } from '../../shared/download-service/zipData';

declare var saveAs: any;

@Injectable()
export class DownloadService {
    zipFilesDownloadingSub= new BehaviorSubject<number>(0);
    zipFilesProcessedSub= new BehaviorSubject<boolean>(false);

    constructor(
        private http: HttpClient,
        private commonVarService:CommonVarService,
      ) { }
      
    getFile(url, params): Observable<Blob> {
        return this.http.get(url, {responseType: 'blob', params: params});
        // return this.http.get(url, {responseType: 'arraybuffer'}).map(res => res);
    }

    postFile(url, params): Observable<Blob>{
        // return this.http.post<Blob>(url, {responseType: 'blob', params: params});
        // for testing
        return this.http.get('https://s3.amazonaws.com/nist-midas/1869/ddPCR%20Raw%20Data_Stein%20et%20al%20PLOSOne%202017.zip', {responseType: 'blob'});
        // return this.http.get(url, {responseType: 'arraybuffer'}).map(res => res);
    }

    // downloadFile(url){
    //     let filename = decodeURI(url).replace(/^.*[\\\/]/, '');

    //     this.getFile(url).subscribe(blob => {
    //         this.saveToFileSystem(blob, filename);
    //     },
    //     error => console.log('Error downloading the file.'))
    // }

    /**
     * Save file
     **/
    saveToFileSystem(data, filename) {
        var json = JSON.stringify(data);
        let blob = new Blob([data], {type: "octet/stream"});
        let blobUrl = window.URL.createObjectURL(blob);

        let a = document.createElement('a');
        document.body.appendChild(a);
        a.setAttribute('style', 'display: none');
        a.href = blobUrl;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(blobUrl);
        a.remove();
    }

    /**
     * Download zip
     **/
    download(nextZip: ZipData, zipdata: ZipData[], treeNode: any){
        const req = new HttpRequest('GET', nextZip.downloadUrl, {
            reportProgress: true, responseType: 'blob'
        });

        nextZip.downloadStatus = 'downloading';

        this.setDownloadingNumber(this.zipFilesDownloadingSub.getValue()+1);
        //     this.downloadService.postFile(this.distApi + "_bundle", JSON.stringify(zipdata.bundle)).subscribe(blob => {
        //     this.downloadService.saveToFileSystem(blob, this.downloadFileName);
        //     console.log('All downloaded.');
        //     this.downloadStatus = 'downloaded';
        //     this.setAllDownloaded(this.files);
        //     this.allDownloaded = true;
        // });  

        nextZip.downloadInstance = this.http.request(req).subscribe(
            event => {
                switch (event.type) {
                    case HttpEventType.Response:
                        this.saveToFileSystem(event.body, nextZip.fileName);
                        nextZip.downloadProgress = 0;
                        nextZip.downloadStatus = 'downloaded';
                        this.setDownloadingNumber(this.zipFilesDownloadingSub.getValue()-1);
                        this.setDownloadStatus(nextZip, treeNode, "downloaded");
                        this.setDownloadProcessStatus(this.allDownloadFinished(zipdata));
                        break;
                    case HttpEventType.DownloadProgress:
                        nextZip.downloadProgress = Math.round(100*event.loaded / event.total);
                        break;
                }
                
            },
            err => {
                nextZip.downloadStatus = 'downloadError';
                nextZip.downloadErrorMessage = err.message;
                this.setDownloadingNumber(this.zipFilesDownloadingSub.getValue()-1);
                console.log("Download err:");
                console.log(err);
                console.log("nextZip:");
                console.log(nextZip);
            }
        );
    }

    /**
     * Download next available zip in the queue
     **/
    downloadNextZip(zipData: ZipData[], treeNode: any){
        if(this.zipFilesDownloadingSub.getValue() < this.commonVarService.getDownloadMaximum()){
            let nextZip = this.getNextZipInQueue(zipData);
            if(nextZip != null){
                this.download(nextZip, zipData, treeNode);
            }
        }
    }

    /**
     * Return next available zip in the queue
     **/
    getNextZipInQueue(zipData: ZipData[]){
        let zipQueue = zipData.filter(item => item.downloadStatus == null);

        if(zipQueue.length > 0){
            return zipQueue[0];
        }else{
            return null;
        }
    }

    /**
    * Set the number of downloading zip files
    **/
    watchDownloadingNumber(): Observable<any> {
        return this.zipFilesDownloadingSub.asObservable();
    }

    /**
     * Set the number of downloading zip files
     **/
    setDownloadingNumber(value: number) {
        this.zipFilesDownloadingSub.next(value);
    }

    /**
    * Watch overall process status
    **/
    watchDownloadProcessStatus(): Observable<any> {
        return this.zipFilesProcessedSub.asObservable();
    }

    /**
     * Set overall process status
     **/
    setDownloadProcessStatus(value: boolean) {
        this.zipFilesProcessedSub.next(value);
    }

    /**
     * Set download status of given tree node
     **/
    setDownloadStatus(zip: any, treeNode: any, status: any){
        for(let includeFile of zip.bundle.includeFiles){
            let fullPath = includeFile.filePath.substring(includeFile.filePath.indexOf('/'));
            let node = this.searchTreeByFullPath(treeNode, fullPath);
            if(node != null){
                node.data.downloadStatus = status;
            }
        }
    }

    /**
     * Check if all zip files are downloaded
     **/
    allDownloaded(zipData: any){
        for (let zip of zipData) {
            if(zip.downloadStatus != 'downloaded'){
                return false;
            }
        }
        return true;
    }

    /**
     * Check if all doanload processes have finished
     **/
    allDownloadFinished(zipData: any){
        for (let zip of zipData) {
            if(zip.downloadStatus == null || zip.downloadStatus == 'downloading'){
                return false;
            }
        }
        return true;
    }

    /**
     * Search tree by given full path
     **/
    searchTreeByFullPath(element, fullPath){
        if(element.data.fullPath == fullPath){
             return element;
        }else if (element.children.length > 0){
             var i;
             var result = null;
             for(i=0; result == null && i < element.children.length; i++){
                  result = this.searchTreeByFullPath(element.children[i], fullPath);
             }
             return result;
        }
        return null;
   }
}