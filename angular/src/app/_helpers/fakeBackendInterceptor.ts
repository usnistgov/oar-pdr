import { Injectable } from '@angular/core';
import { HttpClient, HttpRequest, HttpResponse, HttpHandler, HttpEvent, HttpInterceptor, HTTP_INTERCEPTORS, HttpErrorResponse } from '@angular/common/http';
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
    const sampleRecord: any = require('../../assets/sampleRecord2.json');

    // Choose one of the following files to simulate different cases:
    // bundle-plan-complete.json - no error. Bundle plan returns all zip files.
    // bundle-plan-warning.json - Unable to get part of the requested files.
    // bundle-plan-error.json - Unable to get all requested files.
    const bundlePlanRes: any = require('../../assets/bundle-plan-complete.json');
    // const bundlePlanRes: any = require('../../assets/bundle-plan-warning.json');
    // const bundlePlanRes: any = require('../../assets/bundle-plan-error.json');

    // wrap in delayed observable to simulate server api call
    return of(null).pipe(mergeMap(() => {
      console.log("request.url", request.url);
      console.log("request.url.indexOf('_bundle_plan')", request.url.indexOf('_bundle_plan'));
      // For e2e test
      // if (request.url.endsWith('/rmm/records/SAMPLE123456') && request.method === 'GET') {
      //   return of(new HttpResponse({ status: 200, body: sampleData }));
      // }

      // Generate bundle plan
    //   if (request.url.indexOf('_bundle_plan') > -1 && request.method === 'POST') 
    //   {
    //     console.log("Record saved...");
    //     return of(new HttpResponse({ status: 200, body: bundlePlanRes }));
    //   }

      // Generate bundle plan internal error
      // if (request.url.indexOf('_bundle_plan') > -1 && request.method === 'POST') 
      // {
      //   console.log("Throw error...");
      //   throw new HttpErrorResponse(
      //     {
      //       error: 'internal error message goes here...',
      //       headers: request.headers,
      //       status: 500,
      //       statusText: 'internal error',
      //       url: request.url
      //     });
      // }

    // Generate bundle download internal error
      if (request.url.indexOf('_bundle') > -1 && request.url.indexOf('_bundle_plan') <= 0 && request.method === 'POST') 
      {
        console.log("Throw error...");
        throw new HttpErrorResponse(
          {
            error: 'internal error message goes here...',
            headers: request.headers,
            status: 500,
            statusText: 'internal error',
            url: request.url
          });
      }

      // // authenticate
      // if (request.url.indexOf('auth/_perm/') > -1 && request.method === 'GET') {
      //     let body: ApiToken = {
      //         userId: 'xyz@nist.gov',
      //         token: 'fake-jwt-token'
      //     };
      //     console.log("logging in...")
      //     return of(new HttpResponse({ status: 200, body }));
      // }

      // return 401 not authorised if token is null or invalid
      // if (request.url.indexOf('auth/_perm/') > -1 && request.method === 'GET') {
      //     let body: ApiToken = {
      //         userId: '1234',
      //         token: 'fake-jwt-token'
      //     };
      //     console.log("logging in...")
      //     return Observable.throw(
      //         JSON.stringify({
      //             "status": 401,
      //             "Userid": "xyz@nist.gov",
      //             "message": "Unauthorizeduser: User token is empty or expired."
      //         })

      //     );
      // }

      // if (request.url.endsWith('/auth/token') && request.method === 'GET') {
      //     let body: ApiToken = {
      //         userId: '1234',
      //         token: 'fake-jwt-token'
      //     };
      //     console.log("getting token...")
      //     // window.alert('Click ok to login');
      //     return of(new HttpResponse({ status: 200, body }));
      // }

      // if (request.url.endsWith('/saml-sp/auth/token') && request.method === 'GET') {
      //   let body: ApiToken = {
      //     userId: '1234',
      //     token: 'fake-jwt-token'
      //   };
      //   // window.alert('Click ok to login');
      //   return of(new HttpResponse({ status: 200, body }));
      // }

      // if (request.url.indexOf('/customization/api/draft') > -1 && request.method === 'GET') {
      //     console.log("Interceptor returning sample record...");
      //     return of(new HttpResponse({ status: 200, body: sampleRecord }));
      // }

      // if (request.url.indexOf('/customization/api/draft') > -1 && request.method === 'PATCH') {
      //     console.log("Record updated...");
      //     return of(new HttpResponse({ status: 200, body: undefined }));
      //     // return Observable.throw('Username or password is incorrect');
      // }

      // if (request.url.indexOf('/customization/api/draft') > -1 && request.method === 'DELETE') {
      //     console.log("Record deleted...");
      //     return of(new HttpResponse({ status: 200, body: undefined }));
      // }

      // if (request.url.indexOf('/customization/api/savedrec') > -1 && request.method === 'PUT') {
      //     console.log("Record saved...");
      //     return of(new HttpResponse({ status: 200, body: undefined }));
      // }

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