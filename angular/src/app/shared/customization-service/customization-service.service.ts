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
    update(body: any): Observable<any> {
        const httpOptions = {
            headers: {
                "Authorization": "Bearer " + this.authService.getToken(),
                "userId": this.authService.getUserId()
            }
        };
        // var url = this.customizationUpdateApi + recordid;

        var url = this.customizationApi + "draft/" + this.commonVarService.getEdiid();
        console.log("Update URL:", url);
        console.log("body:", body);
        // return this.http.patch(url, body);
        return this.http.patch(url, body, httpOptions);
    }

    /*
     *   Save the whole record. The data will be pushed to mdserver
     */
    saveRecord(body: any): Observable<any> {
        const httpOptions = {
          headers: {
            "Authorization": "Bearer " + this.authService.getToken(),
            "userId": this.authService.getUserId()
          }
        };
        var url = this.customizationApi + "savedrecord/" + this.commonVarService.getEdiid();
        console.log("Save rec URL:", url);

        body = "{}";
        console.log("body:", body);
        // return this.http.put(url, body);
        return this.http.put(url, body, httpOptions);
    }

    /*
  *   Update one field in publication. New value is in post body.
  */
    delete(): Observable<any> {
        const httpOptions = {
          headers: {
            "Authorization": "Bearer " + this.authService.getToken(),
            "userId": this.authService.getUserId()
          }
        };
        var url = this.customizationApi + "draft/" + this.commonVarService.getEdiid();
        // return this.http.delete(url);
        return this.http.delete(url, httpOptions);
    }

    /*
     *  Get draft data from staging area. If no saved data, backend return saved record
     */
    getDraftData(): Observable<any> {
        // const apiToken = localStorage.getItem("apiToken");

        //Need to append ediid to the base API URL
        var url = this.customizationApi + "draft/" + this.commonVarService.getEdiid();
        console.log("URL to get draft data:", url);
        // return this.http.get(url);
        return this.http.get(url, {
          headers: {
            "Authorization": "Bearer " + this.authService.getToken(),
            "userId": this.authService.getUserId()
          }
        });
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
     * Function to store draft data update date in local storage
     */
    setUpdateDate(updateDate: string) {
        if (this.inBrowser)
            localStorage.setItem(this.commonVarService.getEdiid(), updateDate);
    }

    /**
     * Function to get draft data update date in local storage
     */
    getUpdateDate() {
        if (this.inBrowser)
            return localStorage.getItem(this.commonVarService.getEdiid());
        else
            return "";
    }

    /**
     * Function to remove draft data status in local storage
     */
    removeUpdateDate() {
        if (this.inBrowser)
            localStorage.removeItem(this.commonVarService.getEdiid());
    }
}
