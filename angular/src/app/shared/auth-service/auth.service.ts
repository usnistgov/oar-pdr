import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  authenticatedSub= new BehaviorSubject<boolean>(false);

  constructor() { }

  /**
    * Watch authenticate status
    **/
  watchAuthenticateStatus(): Observable<any> {
    return this.authenticatedSub.asObservable();
  }

  /**
   * Set authenticate status
   **/
  setAuthenticateStatus(value: boolean) {
        this.authenticatedSub.next(value);
  }
}
