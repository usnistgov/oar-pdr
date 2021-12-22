
import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';
import { SearchService } from '../shared/search-service/index';
import { RouterStateSnapshot } from '@angular/router';
import { Observable } from 'rxjs/Observable';
// import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import * as _ from 'lodash';
// import { Console } from '@angular/core/src/console';
import 'rxjs/add/observable/of';
import { first, tap } from 'rxjs/operators';
import { of } from 'rxjs/observable/of';
import { PLATFORM_ID, Inject } from '@angular/core';
import { isPlatformServer } from '@angular/common';
import { makeStateKey, TransferState } from '@angular/platform-browser';
import { _throw } from 'rxjs/observable/throw';
@Injectable()
export class SearchResolve implements Resolve<any> {

  constructor(private searchService: SearchService,
    @Inject(PLATFORM_ID) private platformId,
    private transferState: TransferState, private rtr: Router) { }

  resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<any> {
    var recordid = route.params['id'];

    //console.log(state.url.toString().split("/id/").pop());
    if (state.url.toString().includes("ark")) {
      recordid = state.url.toString().split("/id/").pop();
    }

    const recordid_KEY = makeStateKey<any>('record-' + recordid);

    if (this.transferState.hasKey(recordid_KEY)) {
      const record = this.transferState.get<any>(recordid_KEY, null);
      this.transferState.remove(recordid_KEY);
      return of(record);
    }
    else {
      return this.searchService.searchById(recordid)
        .catch((err: Response, caught: Observable<any[]>) => {
          console.log(err);
          if (err !== undefined) {
            console.log("ERROR STATUS :::" + err.status);
            if (err.status >= 500) {
              this.rtr.navigate(["/usererror", recordid, { errorcode: err.status }]);
            }
            if (err.status >= 400 && err.status < 500) {
              this.rtr.navigate(["/usererror", recordid, { errorcode: err.status }]);
            }
            //return Observable.throw('The Web server (running the Web site) is currently unable to handle the request.');
          }
          return Observable.throw(caught);
        })
    }
  }
}


