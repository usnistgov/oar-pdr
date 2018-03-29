import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';
import { SearchService } from '../shared/search-service/index';
import { RouterStateSnapshot } from '@angular/router/src/router_state';
import { Observable } from 'rxjs/Observable';

@Injectable()
export class SearchResolve implements Resolve<any> {
  
  constructor(private searchService: SearchService) {}
  
  resolve(route: ActivatedRouteSnapshot, rstate: RouterStateSnapshot): Observable<any> {
    
    console.log("resolve:"+route.params['id']);
    //return this.searchService.searchSample();
    return this.searchService.searchById(route.params['id']);
  }
}