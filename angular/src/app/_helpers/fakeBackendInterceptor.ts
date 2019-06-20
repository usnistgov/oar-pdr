import { Injectable } from '@angular/core';
import { HttpClient, HttpRequest, HttpResponse, HttpHandler, HttpEvent, HttpInterceptor, HTTP_INTERCEPTORS } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { delay, mergeMap, materialize, dematerialize } from 'rxjs/operators';
import { TestDataService } from '../shared/testdata-service/testDataService';
import { DownloadService } from '../shared/download-service/download-service.service';

@Injectable()
export class FakeBackendInterceptor implements HttpInterceptor {

  constructor(private testDataService: TestDataService,
    private downloadService: DownloadService,
    private http: HttpClient) { }

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // array in local storage for registered users

    const sampleData: any = require('../../assets/sample2.json');
    const bundlePlanRes: any = require('../../assets/bundle-sample.json');

    // let httpRequest: any[] = [
    //     {"url":"https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip","body":null,"reportProgress":true,"withCredentials":false,"responseType":"blob","method":"GET","headers":{"normalizedNames":{},"lazyUpdate":null,"headers":{}},"params":{"updates":null,"cloneFrom":null,"encoder":{},"map":null},"urlWithParams":"https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip"}
    // ];

    // wrap in delayed observable to simulate server api call
    return of(null).pipe(mergeMap(() => {
      // get bundlePlan
      // if (request.url.endsWith('/od/ds/_bundle_plan') && request.method === 'POST') {
      //   return of(new HttpResponse({ status: 200, body: JSON.parse(bundlePlanRes) }));
      // }

      // For e2e test
      if (request.url.endsWith('/rmm/records/SAMPLE123456') && request.method === 'GET') {
        return of(new HttpResponse({ status: 200, body: sampleData }));
      }


      // get bundle
      // if (request.url.endsWith('/od/ds/_bundle') && request.method === 'POST') {
      //     // return new Observable(observer => {
      //     //     observer.next(this.testDataService.getBundle('https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip', params););
      //     //     observer.complete();
      //     //   });
      //     // return this.testDataService.getBundle('https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip', bundlePlanRes);
      //     console.log("Handling /od/ds/_bundle:");

      //     const duplicate = request.clone({
      // method: 'get' 
      //     })
      //     return next.handle(request);
      // }

      // pass through any requests not handled above
      return next.handle(request);

    }))

      // call materialize and dematerialize to ensure delay even if an error is thrown (https://github.com/Reactive-Extensions/RxJS/issues/648)
      .pipe(materialize())
      .pipe(delay(500))
      .pipe(dematerialize());
  }
}

export let fakeBackendProvider = {
  // use fake backend in place of Http service for backend-less development
  provide: HTTP_INTERCEPTORS,
  useClass: FakeBackendInterceptor,
  multi: true
};