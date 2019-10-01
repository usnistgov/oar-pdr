import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CommonVarService } from '../common-var/common-var.service';
import { AuthService } from '../auth-service/auth.service';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { AppConfig } from '../../config/config';
import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID, APP_ID, Inject } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class CustomizationServiceService {
  customizationApi: string;
  inBrowser: boolean = false;
  draftStatusCookieName: string = "draft_status";

  recordEditedSub = new BehaviorSubject<boolean>(false);


  constructor(
    private http: HttpClient,
    private cfg: AppConfig,
    private commonVarService: CommonVarService,
    private authService: AuthService,
    @Inject(PLATFORM_ID) private platformId: Object) {
    // this.customizationApi = "http://localhost:8085/customization/";
    this.customizationApi = this.cfg.get("customizationApi", "/customization");
    if (!(this.customizationApi.endsWith('/'))) this.customizationApi = this.customizationApi + '/';
    this.inBrowser = isPlatformBrowser(platformId);
  }

  /**
   * Set processing flag
   **/
  setRecordEdited(value: boolean) {
    this.recordEditedSub.next(value);
  }

  /**
  * Watching processing flag
  **/
  watchRecordEdited(): Observable<any> {
    return this.recordEditedSub.asObservable();
  }

  /*
  *   Update one field in publication. New value is in post body.
  */
  update(recordid: string, body: any): Observable<any> {
    // const httpOptions = {
    //   headers: {
    //     "Authorization": "Bearer " + this.authService.getToken(),
    //     "userId": this.authService.getUserId()
    //   }
    // };
    // var url = this.customizationUpdateApi + recordid;
    // return this.http.patch(url, body, httpOptions);

    var url = this.customizationApi + "draft/" + recordid;
    console.log("Update URL:", url);
    console.log("body:", body);
    return this.http.patch(url, body);
  }

  /*
   *   Save the whole record. The data will be pushed to mdserver
   */
  saveRecord(recordid: string, body: any): Observable<any> {
    // const httpOptions = {
    //   headers: {
    //     "Authorization": "Bearer " + this.authService.getToken(),
    //     "userId": this.authService.getUserId()
    //   }
    // };
    var url = this.customizationApi + "savedrecord/" + recordid;
    console.log("Save rec URL:", url);
    console.log("body:", body);
    body = "{}";
    return this.http.put(url, body);
    // return this.http.put(url, body, httpOptions);
  }

  /*
*   Update one field in publication. New value is in post body.
*/
  delete(recordid: string): Observable<any> {
    // const httpOptions = {
    //   headers: {
    //     "Authorization": "Bearer " + this.authService.getToken(),
    //     "userId": this.authService.getUserId()
    //   }
    // };
    var url = this.customizationApi + "draft/" + recordid;
    return this.http.delete(url);
    // return this.http.delete(url, httpOptions);
  }

  /*
   *  Get draft data from staging area. If no saved data, backend return saved record
   */
  getDraftData(recordid: string): Observable<any> {
    const apiToken = localStorage.getItem("apiToken");

    //Need to append ediid to the base API URL
    var url = this.customizationApi + "draft/" + recordid;
    console.log("URL to get draft data:", url);
    return this.http.get(url);
    // return this.http.get(this.customizationUpdateApi + recordid, {
    //   headers: {
    //     "Authorization": "Bearer " + this.authService.getToken(),
    //     "userId": this.authService.getUserId()
    //   }
    // });
  }

  /**
   * Function to Check whether record has keyword
   */
  checkKeywords(record: any) {
    if (record['keyword'] != undefined && record['keyword'].length > 0 && record['keyword'][0] != "") {
      return true;
    }
    else {
      return false;
    }
  }

  /**
   * Function to set draft data status in local storage
   */
  setDraftDataStatus(ediid: string, updateDate: string) {
    if (this.inBrowser)
      localStorage.setItem(ediid, updateDate);
  }

  /**
   * Function to get draft data status in local storage
   */
  getDraftDataStatus(ediid: string){
    if (this.inBrowser)
      return localStorage.getItem(ediid);
    else 
      return "";
  }

  /**
   * Function to remove draft data status in local storage
   */
  removeDraftDataStatus(ediid: string) {
    if(this.inBrowser)
      localStorage.removeItem(ediid);
  }
}
