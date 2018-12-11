import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http'; 
import {Observable } from 'rxjs';

declare var saveAs: any;

@Injectable()
export class DownloadService {

    constructor(
        private http: HttpClient,
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
        console.log("Downloaded data:");
        console.log(data);

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
}