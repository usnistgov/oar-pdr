import { Injectable } from '@angular/core';
import { Subject } from 'rxjs/Subject';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

@Injectable()
export class CommonVarService {

  private userlogin: boolean = false;
  public userObservable = new Subject<boolean>();
  ediid: string = null;
  private _storage = null;
  private random_minimum: number = 1;
  private random_maximum: number = 100000;
  private isLocalTesting: boolean = false;

  localProcessingSub = new BehaviorSubject<boolean>(false);
  showDatacartSub = new BehaviorSubject<boolean>(false);
  forceLandingPageInitSub = new BehaviorSubject<boolean>(false);
  openDownloadModalSub = new BehaviorSubject<boolean>(false);
  contentReadySub = new BehaviorSubject<boolean>(false);

  constructor() {
    if (typeof(localStorage) !== 'undefined')
      this._storage = localStorage;
  }

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
    if (this._storage)
      this._storage.setItem("ediid", ediid);
  }

  getEdiid() {
    if (! this._storage) return "(none)";
    return this._storage.getItem("ediid");
  }

  getRandomMaximum() {
    return this.random_maximum;
  }

  getRandomMinimum() {
    return this.random_minimum;
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

  /**
   * Set show-datacart flag
   **/
  setOpenDownloadModal(value: boolean) {
    this.openDownloadModalSub.next(value);
  }

  /**
  * Watching show-datacart flag
  **/
  watchOpenDownloadModal(): Observable<boolean> {
    return this.openDownloadModalSub.asObservable();
  }

  /**
   * Set landing page ready flag
   **/
  setContentReady(value: boolean) {
    this.contentReadySub.next(value);
  }

  /**
  * Watching landing page ready flag
  **/
 watchContentReady(): Observable<boolean> {
    return this.contentReadySub.asObservable();
  }
}
