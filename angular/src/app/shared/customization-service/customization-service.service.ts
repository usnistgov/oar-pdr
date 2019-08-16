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
  update(recordid: string, field: string, body: any) {
    const httpOptions = {
      headers: {
        "Authorization": "Bearer "+ this.authService.getToken(),
        "userId": this.authService.getUserId()
      }
    };
    var url = this.commonVarService.getCustomizationUpdateApi() + recordid;
    this.http.post(url, body, httpOptions).subscribe(
      result => {
        console.log("Update result:", result);
      },
      err => {
        console.log("Error when updating " + field + ":", err);
      });
  }

  getSavedData(): Observable<any> {
    const apiToken = localStorage.getItem("apiToken");

    //Need to append ediid to the base API URL
    return this.http.get(this.authService.getBaseApiUrl(), {
      headers: {
        "Authorization": "Bearer " + this.authService.getToken(),
        "userId": this.authService.getUserId()
      }
    });
  }

  /*
  *   Check if there is a edited record
  */
  checkRecordEditStatus(recordid: string){
    var _this = this;
    this.getSavedData().subscribe((res) => {
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
