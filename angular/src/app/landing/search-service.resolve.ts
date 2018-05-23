import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';
import { SearchService } from '../shared/search-service/index';
import { RouterStateSnapshot } from '@angular/router/src/router_state';
import { Observable } from 'rxjs/Observable';
import { Router } from '@angular/router';
import * as _ from 'lodash';
import { Console } from '@angular/core/src/console';
import 'rxjs/add/observable/of';
@Injectable()
export class SearchResolve implements Resolve<any> {
   
  // constructor(private searchService: SearchService, private rtr: Router ) {}
  
  // resolve(route: ActivatedRouteSnapshot, rstate: RouterStateSnapshot): Observable<any> {
  //   let searchId = route.params['id'];
  //   if (_.includes(rstate.url,'ark')) 
  //      searchId = rstate.url.split('/id/').pop();
  //   return this.searchService.searchById(searchId).catch((err: Response, caught: Observable<any[]>) => {
  //     if (err !== undefined) {
  //       if(err.status >= 500){
  //         this.rtr.navigate(["/error", searchId]);
  //       }
  //       if(err.status >= 400 && err.status < 500 ){
  //          this.rtr.navigate(["/usererror", searchId]); 
  //       }
  //     }
  //     return Observable.throw(caught);
  //   });
  // }

  /** Working below **/
  constructor(private searchService: SearchService) {}
  
  resolve(route: ActivatedRouteSnapshot) {
    return this.searchService.searchById(route.params['id'])
    .catch(( error ) => {
      return Observable.throw('data not available at this time'+error);
    });;
  }
}


  