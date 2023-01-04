import { HttpClient, HttpHeaders } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable, throwError } from "rxjs";
import { catchError, retry } from "rxjs/operators";
import { UserInfo } from "../models/form-data.model";
import { Record, RecordWrapper } from "../models/record.model";

@Injectable()
export class RPAService {

    apiURL = 'http://localhost:9090';

    constructor(private http: HttpClient) { }

    // Http Options
    httpOptions = {
        headers: new HttpHeaders({
            'Content-Type': 'application/json',
        }),
    };


    public createRecord(userInfo: UserInfo): Observable<Record> {
        console.log("User Info", userInfo);
        return this.http
            .post<Record>(
                this.apiURL + '/new',
                JSON.stringify({ "userInfo": userInfo }),
                this.httpOptions
            )
            .pipe(retry(1), catchError(this.handleError));
    }

    public getRecord(recordId: string): Observable<RecordWrapper> {
        return this.http
        .get<RecordWrapper>(
            this.apiURL + "/" + recordId, 
            this.httpOptions)
            .pipe(retry(1), catchError(this.handleError));
    }

    // Error handling
    handleError(error: any) {
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