import { Injectable } from '@angular/core';
import { Subject } from 'rxjs/Subject';
import {Observable } from 'rxjs';

@Injectable()
export class CommonVarService {

  private userlogin : boolean = false;
  public userObservable = new Subject<boolean>();
  ediid: string = null;
  private _storage = localStorage;
  private random_minimum: number = 1;
  private random_maximum: number = 100000;

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
    
  setEdiid(ediid:string) {
    this._storage.setItem("ediid", ediid);
  }

  getEdiid(){
    return this._storage.getItem("ediid");
  }

  getRandomMaximum(){
    return this.random_maximum;
  }

  getRandomMinimum(){
    return this.random_minimum;
  }

}