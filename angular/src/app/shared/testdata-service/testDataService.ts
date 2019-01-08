import { Injectable } from '@angular/core';
import { Observable } from 'rxjs/Observable';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http'; 

@Injectable()
export class TestDataService {
   constructor(private http: HttpClient) {
        // this.getJSON().subscribe(data => {
        //     console.log("Sample data:");
        //     console.log(data);
        // });
    }

    public getJSON(): Observable<any> {
        return this.http.get('./assets/sample2.json');
    }

    public getBundlePlan(): Observable<any> {
        return this.http.get('./assets/bundlePlanResponseSample.json');
    }

    public getBundle(url, params): Observable<any> {
         const req = new HttpRequest('GET', url, {
            reportProgress: true, responseType: 'blob'
        });
        return this.http.request(req);
        // return this.http.get('https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip',  {responseType: 'blob'});
    }
}