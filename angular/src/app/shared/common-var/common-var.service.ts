import { Injectable } from '@angular/core';
import { Subject } from 'rxjs/Subject';
import {Observable } from 'rxjs';

@Injectable()
export class CommonVarService {

  private userlogin : boolean = false;
  public userObservable = new Subject<boolean>();
  ediid: string = null;
  private _storage = localStorage;

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
    
  setEdiit(ediid:string) {
    this._storage.setItem("ediid", ediid);
  }

  getEdiid(){
    return this._storage.getItem("ediid");
  }
}