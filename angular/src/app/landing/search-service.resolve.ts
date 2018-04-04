import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';
import { SearchService } from '../shared/search-service/index';
import { RouterStateSnapshot } from '@angular/router/src/router_state';
import { Observable } from 'rxjs/Observable';
import { Router } from '@angular/router';
import * as _ from 'lodash';
import { Console } from '@angular/core/src/console';

@Injectable()
export class SearchResolve implements Resolve<any> {
   
  constructor(private searchService: SearchService, private rtr: Router ) {}
  
  resolve(route: ActivatedRouteSnapshot, rstate: RouterStateSnapshot): Observable<any> {
    let searchId = route.params['id'];
    if (_.includes(rstate.url,'ark')) 
       searchId = rstate.url.split('/id/').pop();
    return this.searchService.searchById(searchId).catch((err: Response, caught: Observable<any[]>) => {
      if (err !== undefined) {
        if(err.status >= 500){
          this.rtr.navigate(["/error", searchId]);
        }
        if(err.status >= 400 && err.status < 500 ){
           this.rtr.navigate(["/usererror", searchId]); 
        }
        //return Observable.throw('The Web server (running the Web site) is currently unable to handle the request.');
      }
      return Observable.throw(caught);
    });
  }
}


  