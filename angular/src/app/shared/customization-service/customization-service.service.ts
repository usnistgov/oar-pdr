import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CommonVarService } from '../common-var/common-var.service';
import { AuthService } from '../auth-service/auth.service';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

@Injectable({
  providedIn: 'root'
})
export class CustomizationServiceService {

  recordEditedSub = new BehaviorSubject<boolean>(false);
  private customizationUpdateApi: string = "http://localhost:8085/customization/draft/";
  private customizationSaveApi: string = "http://localhost:8085/customization/savedrec/";

  constructor(
    private http: HttpClient,
    private commonVarService: CommonVarService,
    private authService: AuthService) { }

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
    const httpOptions = {
      headers: {
        "Authorization": "Bearer " + this.authService.getToken(),
        "userId": this.authService.getUserId()
      }
    };
    var url = this.customizationUpdateApi + recordid;
    return this.http.patch(url, body, httpOptions);
  }

  /*
   *   Save the whole record. The data will be pushed to mdserver
   */
  saveRecord(recordid: string, body: any): Observable<any> {
    const httpOptions = {
      headers: {
        "Authorization": "Bearer " + this.authService.getToken(),
        "userId": this.authService.getUserId()
      }
    };
    var url = this.customizationSaveApi + recordid;
    return this.http.put(url, body, httpOptions);
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
    var url = this.customizationUpdateApi + recordid;
    return this.http.delete(url, httpOptions);
  }

  /*
   *  Get saved data. If no saved data, backend return null
   */
  getSavedData(recordid: string): Observable<any> {
    const apiToken = localStorage.getItem("apiToken");

    //Need to append ediid to the base API URL
    return this.http.get(this.customizationUpdateApi + recordid, {
      headers: {
        "Authorization": "Bearer " + this.authService.getToken(),
        "userId": this.authService.getUserId()
      }
    });
  }

  /*
  *   Check if there is a edited record
  */
  checkRecordEditStatus(recordid: string) {
    var _this = this;
    this.getSavedData(recordid).subscribe((res) => {
      // console.log("Saved data", res);
      if (res != undefined && res != null) {
        _this.setRecordEdited(true);
      } else {
        _this.setRecordEdited(false);
      }
    }, (error) => {
      console.log("There is an error in searchservice.");
      console.log(error);
      alert('Ooops! We are having difficulty retriving record editing status.');
      _this.setRecordEdited(false);
    });
  }
}
