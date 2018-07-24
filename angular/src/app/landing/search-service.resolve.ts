
import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';
import { SearchService } from '../shared/search-service/index';
import { RouterStateSnapshot } from '@angular/router/src/router_state';
import { Observable } from 'rxjs/Observable';
import { Router } from '@angular/router';
import * as _ from 'lodash';
import { Console } from '@angular/core/src/console';
import 'rxjs/add/observable/of';
import {first, tap} from 'rxjs/operators';
import {of} from 'rxjs/observable/of';
import {PLATFORM_ID, Inject} from '@angular/core';
import {isPlatformServer} from '@angular/common';
import {makeStateKey, TransferState} from '@angular/platform-browser';

@Injectable()
export class SearchResolve implements Resolve<any> {
   
  constructor(private searchService: SearchService,
              @Inject(PLATFORM_ID) private platformId,
              private transferState:TransferState) {}
 
  /** Working below **/
  //  constructor(private searchService: SearchService) {}
  
  // resolve(route: ActivatedRouteSnapshot) {
  //   return this.searchService.(route.params['id']);
  // }
  resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<any> {

    const recordid = route.params['id'];
    const recordid_KEY = makeStateKey<any>('record-' + recordid);
    
    if (this.transferState.hasKey(recordid_KEY)) {
        console.log("1. Is it here @@@");
        const record = this.transferState.get<any>(recordid_KEY, null);
        this.transferState.remove(recordid_KEY);
        return of(record);
    }
    else {
        return this.searchService.testdata() 
            .pipe(
                tap(record => {
                    if (isPlatformServer(this.platformId)) {
                        
                      console.log("2 . Is it here @@@:"+this.platformId);
                        this.transferState.set(recordid_KEY, record);
                       console.log(this.transferState.toJson()); 
                    }
                })
            );
    }
  }
}


  