import { Injectable } from '@angular/core';
import { Subject } from 'rxjs/Subject';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

@Injectable()
export class CommonVarService {

  private userlogin: boolean = false;
  public userObservable = new Subject<boolean>();
  ediid: string = null;
  private _storage = localStorage;
  private random_minimum: number = 1;
  private random_maximum: number = 100000;
  private download_maximum: number = 1;
  private isLocalTesting: boolean = false;

  processingSub = new BehaviorSubject<boolean>(false);
  localProcessingSub = new BehaviorSubject<boolean>(false);
  showDatacartSub = new BehaviorSubject<boolean>(false);
  forceLandingPageInitSub = new BehaviorSubject<boolean>(false);

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

  setEdiid(ediid: string) {
    this._storage.setItem("ediid", ediid);
  }

  getEdiid() {
    return this._storage.getItem("ediid");
  }

  getRandomMaximum() {
    return this.random_maximum;
  }

  getRandomMinimum() {
    return this.random_minimum;
  }

  getDownloadMaximum() {
    return this.download_maximum;
  }

  /**
   * Get local testing flag
   **/
  getLocalTestingFlag() {
    return this.isLocalTesting;
  }

  /**
   * Set processing flag
   **/
  setProcessing(value: boolean) {
    this.processingSub.next(value);
  }

  /**
  * Watching processing flag
  **/
  watchProcessing(): Observable<any> {
    return this.processingSub.asObservable();
  }

  /**
   * Set processing flag
   **/
  setLocalProcessing(value: boolean) {
    this.localProcessingSub.next(value);
  }

  /**
  * Watching processing flag
  **/
  watchLocalProcessing(): Observable<any> {
    return this.localProcessingSub.asObservable();
  }

  /**
   * Set processing flag
   **/
  setForceLandingPageInit(value: boolean) {
    this.forceLandingPageInitSub.next(value);
  }

  /**
  * Watching processing flag
  **/
  watchForceLandingPageInit(): Observable<any> {
    return this.forceLandingPageInitSub.asObservable();
  }

  /**
   * Set show-datacart flag
   **/
  setShowDatacart(value: boolean) {
    this.showDatacartSub.next(value);
  }

  /**
  * Watching show-datacart flag
  **/
  watchShowDatacart(): Observable<any> {
    return this.showDatacartSub.asObservable();
  }
}