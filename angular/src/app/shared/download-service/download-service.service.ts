import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders } from '@angular/common/http'; 
import {Observable } from 'rxjs';

declare var saveAs: any;

@Injectable()
export class DownloadService {
    constructor(
        private http: HttpClient,
      ) { }
      
    getFile(url) {
        let headers=new HttpHeaders();
        headers.set('Accept','text/plain');
        return this.http.get(url, {responseType: 'blob' as 'json'}).map(res => res);
        // return this.http.get(url, {responseType: 'arraybuffer'}).map(res => res);
    }

    // getFile(url, params): Observable<Blob> {
    //     let headers=new HttpHeaders();
    //     headers.set('Accept','text/plain');
    //     return this.http.get(url, {headers:headers, responseType: 'blob' as 'json'});
    // }

    downloadFile(url){
        let filename = decodeURI(url).replace(/^.*[\\\/]/, '');

        this.getFile(url).subscribe(blob => {
            this.saveToFileSystem(blob, filename);
        },
        error => console.log('Error downloading the file.'))
    }

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
}