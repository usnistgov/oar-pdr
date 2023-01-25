import { HttpClient, HttpHeaders } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable, throwError } from "rxjs";
import { catchError, retry } from "rxjs/operators";
import { ApprovalResponse, Record, RecordWrapper, UserInfo } from "../models/record.model";
import { formatDate } from '@angular/common';

@Injectable()
export class RPAService {

    baseUrl = 'http://localhost:9090/rpa';

    constructor(private http: HttpClient) { }

    // Http Options
    httpOptions = {
        headers: new HttpHeaders({
            'Content-Type': 'application/json',
        }),
    };

    public getRecord(recordId: string): Observable<RecordWrapper> {
        return this.http
        .get<RecordWrapper>(
            this.baseUrl + "/" + recordId, 
            this.httpOptions)
            .pipe(retry(1), catchError(this.handleError));
    }

    public createRecord(userInfo: UserInfo): Observable<Record> {
        console.log("User Info", userInfo);
        return this.http
            .post<Record>(
                this.baseUrl,
                JSON.stringify({ "userInfo": userInfo }),
                this.httpOptions
            )
            .pipe(catchError(this.handleError));
    }

    public approveRequest(recordId: string): Observable<ApprovalResponse> {
        return this.http
                .patch<ApprovalResponse>(this.baseUrl + "/" + recordId, 
                {"Approval_Status__c":`Approved_${formatDate(Date.now(),'yyyy-MM-dd h:mm a','en-US')}`}, 
                this.httpOptions)
                .pipe(catchError(this.handleError));
    }

    public declineRequest(recordId: string): Observable<ApprovalResponse> {
        return this.http
                .patch<ApprovalResponse>(this.baseUrl + "/" + recordId, 
                {"Approval_Status__c":`Declined_${formatDate(Date.now(),'yyyy-MM-dd h:mm a','en-US')}`}, 
                this.httpOptions)
                .pipe(catchError(this.handleError));
    }

    // Error handling
    private handleError(error: any) {
        let errorMessage = '';
        if (error.error instanceof ErrorEvent) {
            // Get client-side error
            errorMessage = error.error.message;
        } else {
            // Get server-side error
            errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
        }
        window.alert(errorMessage);
        return throwError(() => {
            return errorMessage;
        });
    }
}