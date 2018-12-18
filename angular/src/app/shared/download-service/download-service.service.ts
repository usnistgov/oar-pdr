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

    download(nextZip: ZipData, zipdata: ZipData[]){
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
                        break;
                    case HttpEventType.DownloadProgress:
                        nextZip.downloadProgress = Math.round(100*event.loaded / event.total);
                        break;
                }
            }
            // err => {
            //     this.downloadStatus == 'downloadError';
            //     this.downloadErrorMessage = err.message;
            //     this.cancelDownloadAll();
            //     console.log("Download err:");
            //     console.log(err);
            //     console.log("downloadStatus:");
            //     console.log(this.downloadStatus);
            // }
        );
    }

    downloadNextZip(zipData: ZipData[]){
        if(this.zipFilesDownloadingSub.getValue() < this.commonVarService.getDownloadMaximum()){
            let nextZip = this.getNextZipInQueue(zipData);
            if(nextZip != null){
                this.download(nextZip, zipData);
            }
        }
    }

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

    allDownloaded(zipData: any){
        for (let zip of zipData) {
            if(zip.downloadStatus != 'downloaded'){
                return false;
            }
        }
        return true;
    }
}