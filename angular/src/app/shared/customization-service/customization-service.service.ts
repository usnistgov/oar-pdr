import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { SharedService } from '../shared/shared.service';
import { AuthService } from '../auth-service/auth.service';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { AppConfig } from '../../config/config';
import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID, APP_ID, Inject } from '@angular/core';
import { EditControlService } from '../../landing/edit-control-bar/edit-control.service';
import { DatePipe } from '@angular/common';

@Injectable({
    providedIn: 'root'
})
export class CustomizationService {
    customizationApi: string;
    inBrowser: boolean = false;
    draftStatusCookieName: string = "draft_status";
    recordEditedSub = new BehaviorSubject<boolean>(false);
    updateDateSub = new BehaviorSubject<string>("");
    ediid: string;

    constructor(
        private http: HttpClient,
        private cfg: AppConfig,
        private commonVarService: SharedService,
        private authService: AuthService,
        private datePipe: DatePipe,
        private editControlService: EditControlService,
        @Inject(PLATFORM_ID) private platformId: Object) {
        this.customizationApi = "http://localhost:8085/customization/";
        // this.customizationApi = this.cfg.get("customizationApi", "/customization");
        // this.customizationApi = "https://oardev.nist.gov/customization/";
        if (!(this.customizationApi.endsWith('/'))) this.customizationApi = this.customizationApi + '/';
        this.customizationApi = this.customizationApi + 'api/';
        this.inBrowser = isPlatformBrowser(platformId);

        this.editControlService.watchEdiid().subscribe(value => {
            this.ediid = value;
        });
    }

    /**
     * Set record edit mode
     **/

    setUpdateDateSub(date: string) {
        this.updateDateSub.next(date);
    }

    /**
     * Watching record edit mode
     **/
    watchUpdatedateSub(): Observable<any> {
        return this.updateDateSub.asObservable();
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

        var url = this.customizationApi + "draft/" + this.ediid;
        console.log("Update URL:", url);
        console.log("body:", body);
        console.log("Header:", httpOptions);
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
        var url = this.customizationApi + "savedrecord/" + this.ediid;
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
        var url = this.customizationApi + "draft/" + this.ediid;
        // return this.http.delete(url);
        return this.http.delete(url, httpOptions);
    }

    /*
     *  Get draft data from staging area. If no saved data, backend return saved record
     */
    getDraftData(): Observable<any> {
        console.log("Getting draft");
        //Need to append ediid to the base API URL
        var url = this.customizationApi + "draft/" + this.ediid;
        var token = this.authService.getToken();
        console.log("Token:", this.authService.getToken());
        // return this.http.get(url);

        return this.http.get(url, {
            headers: {
                "Authorization": "Bearer " + token
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
        if (this.inBrowser) {
            console.log("Setting update date:", updateDate);
            if (this.ediid) {
                this.setUpdateDateLocalStorage(updateDate).then(
                    (resolve) => {
                        this.setUpdateDateSub(updateDate);
                    }
                );
            } else {
                console.log("Ediid is not available. Cannot store update date.");
            }
        }
    }

    /**
     * Function to get draft data update date in local storage
     */
    getUpdateDate() {
        if (this.inBrowser)
            return localStorage.getItem(this.ediid);
        else
            return "";
    }

    /**
 * Function to get draft data update date in local storage
 */
    setUpdateDateLocalStorage(updateDate: string) {
        var promise = new Promise((resolve, reject) => {
            setTimeout(() => {
                if (this.inBrowser){
                    localStorage.setItem(this.ediid, updateDate);
                    resolve();
                };
            }, 1000);
        });

        return promise;
    }

    /**
     * Function to remove draft data status in local storage
     */
    removeUpdateDate() {
        if (this.inBrowser) {
            localStorage.removeItem(this.ediid);
            this.setUpdateDateSub("");
        }
    }

    /*
     *  Set record level edit mode (for the edit button at top)
     */
    checkDataChanges(record: any, originalRecord: any, fieldObject: any, updateDate?: string) {
        console.log("record", record);
        var dataChanged: boolean = false;
        if (record != undefined && originalRecord != undefined) {
            fieldObject.title.edited = this.dataEdited(record['title'], originalRecord['title']);
            fieldObject.authors.edited = this.dataEdited(record['authors'], originalRecord['authors']);
            fieldObject.contactPoint.edited = this.dataEdited(record['contactPoint'], originalRecord['contactPoint']);
            fieldObject.description.edited = this.dataEdited(record['description'], originalRecord['description']);
            fieldObject.topic.edited = this.dataEdited(record['topic'], originalRecord['topic']);
            fieldObject.keyword.edited = this.dataEdited(record['keyword'], originalRecord['keyword']);

            dataChanged = fieldObject.title.edited || fieldObject.authors.edited || fieldObject.contactPoint.edited || fieldObject.description.edited || fieldObject.topic.edited || fieldObject.keyword.edited;
        } else {
            dataChanged = false;
        }

        this.editControlService.setDataChanged(dataChanged);

        if (updateDate) {
            console.log("updateDate", updateDate);
            this.setUpdateDate(updateDate);
            this.setRecordEdited(true);
        }

        if (!dataChanged) {
            this.removeUpdateDate();
            this.setRecordEdited(false);
        }
        // if (dataChanged) {
        //     var updateDate = this.datePipe.transform(new Date(), "MMM d, y, h:mm:ss a");
        //     this.setUpdateDate(updateDate);
        //     this.setRecordEdited(true);
        // } else {
        //     this.removeUpdateDate();
        //     this.setRecordEdited(false);
        // }
    }

    /**
     * Function to check if any difference between current data and original data
     */
    dataEdited(currentData: any, Originaldata: any) {
        if ((currentData == undefined || currentData == "") && (Originaldata == undefined || Originaldata == "")) {
            return false;
        } else {
            return JSON.stringify(currentData) != JSON.stringify(Originaldata);
        }
    }
}
