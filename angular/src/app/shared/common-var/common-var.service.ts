import { Injectable } from '@angular/core';
import { Subject } from 'rxjs/Subject';


@Injectable()
export class CommonVarService {

  private userlogin : boolean = false;
  public userObservable = new Subject<boolean>();

  constructor() { }
  
    // setLogin(setlogin : boolean){
    //     this.userlogin = setlogin;
    // }

    // getLogin(){
    //     return this.userlogin;
    // }

    userConfig(val) {
        this.userObservable.next(val);
      }  
    
}