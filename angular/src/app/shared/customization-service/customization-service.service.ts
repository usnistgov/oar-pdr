import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CommonVarService } from '../common-var/common-var.service';
import { AuthService } from '../auth-service/auth.service';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { AppConfig } from '../../config/config';

@Injectable({
  providedIn: 'root'
})
export class CustomizationServiceService {
  customizationApi: string;

  recordEditedSub = new BehaviorSubject<boolean>(false);


  constructor(
    private http: HttpClient,
    private cfg: AppConfig,
    private commonVarService: CommonVarService,
    private authService: AuthService) {
    this.customizationApi = "http://localhost:8085/customization/";
    // this.customizationApi = this.cfg.get("customizationApi", "/customization");
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
    console.log("body", body);
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
    var url = this.customizationApi + "savedrec/" + recordid;
    return this.http.put(url, body);
    // return this.http.put(url, body, httpOptions);
  }

  /*
*   Update one field in publication. New value is in post body.
*/
  delete(recordid: string): Observable<any> {
    const httpOptions = {
      headers: {
        "Authorization": "Bearer " + this.authService.getToken(),
        "userId": this.authService.getUserId()
      }
    };
    var url = this.customizationApi + "draft/" + recordid;
    return this.http.delete(url, httpOptions);
  }

  /*
   *  Get draft data from staging area. If no saved data, backend return saved record
   */
  getDraftData(recordid: string): Observable<any> {
    const apiToken = localStorage.getItem("apiToken");

    //Need to append ediid to the base API URL
    console.log("Calling: " + this.customizationApi + "draft/" + recordid);
    return this.http.get(this.customizationApi + "draft/" + recordid);
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
}
