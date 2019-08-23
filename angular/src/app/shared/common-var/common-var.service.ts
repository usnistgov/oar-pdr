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
  editModeSub = new BehaviorSubject<boolean>(false);
  refreshTreeSub = new BehaviorSubject<boolean>(false);

  constructor() {
    if (typeof (localStorage) !== 'undefined')
      this._storage = localStorage;
  }

  userConfig(val) {
    this.userObservable.next(val);
  }

  setEdiid(ediid: string) {
    this.ediid = ediid;
  }

  getEdiid() {
    return this.ediid;
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
  setRefreshTree(value: boolean) {
    this.refreshTreeSub.next(value);
  }

  /**
  * Watching processing flag
  **/
  watchRefreshTree(): Observable<any> {
    return this.refreshTreeSub.asObservable();
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

  /**
 * Set landing page ready flag
 **/
  setEditMode(value: boolean) {
    this.editModeSub.next(value);
  }

  /**
  * Watching landing page ready flag
  **/
  watchEditMode(): Observable<boolean> {
    return this.editModeSub.asObservable();
  }

  /*
   *   Return a blank author
   */
  getBlankAuthor() {
    return {
      "familyName": "",
      "fn": "",
      "givenName": "",
      "middleName": "",
      "affiliation": [
        {
          "@id": "",
          "title": "National Institute of Standards and Technology",
          "dept": "",
          "@type": [
            ""
          ]
        }
      ],
      "orcid": "",
      "isCollapsed": false,
      "fnLocked": false,
      "dataChanged": false
    };
  }

  /*
  *   Determine if a given value is empty
  */
  emptyString(e: any) {
    switch (e) {
      case "":
      case 0:
      case "0":
      case null:
      case false:
      case typeof this == "undefined":
        return true;
      default:
        return false;
    }
  }

  /*
  *   Return a blank contact point
  */
  getBlankContact() {
    return {
      "fn": "",
      "hasEmail": "",
      "address": [
        ""
      ]
    }
  }
}
