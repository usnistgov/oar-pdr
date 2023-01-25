import { HttpClient, HttpHeaders } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { parse } from 'yaml';
import { readFileSync } from 'fs';
import { Dataset } from "../models/dataset.model";
import { Observable, Subject, throwError } from "rxjs";
import { FormTemplate } from "../models/form-template.model";
import { catchError } from "rxjs/operators";
import { Country } from "../models/country.model";


@Injectable()
export class ConfigurationService {


    constructor(private http: HttpClient) {
    }

    configUrl = 'assets/config.yaml';

    getConfig() {
      return this.http.get<any>(this.configUrl);
    }

    public getDatasets(filename: string) : Observable<Dataset[]>{
        const subject = new Subject<Dataset[]>();

        const headers = new HttpHeaders({
            'Access-Control-Allow-Origin': '*',
        })

        this.http.get(`assets/${filename}`, { responseType: 'text', headers: headers}).subscribe(response => {
            let config = parse(response);
            subject.next(config.datasets);
        });
        return subject.asObservable();

    }

    public getFormTemplate(formName: string): Observable<FormTemplate>{
        const subject = new Subject<FormTemplate>();

        const headers = new HttpHeaders({
            'Access-Control-Allow-Origin': '*',
        })

        this.http.get(this.configUrl, { responseType: 'text', headers: headers}).subscribe(response => {
            let config = parse(response);
            let matchingTemplate;
            config.formTemplates.forEach(template=> {
                if (template.id === formName) {
                    matchingTemplate = template;
                }
            })
            subject.next(matchingTemplate);
        });
        return subject.asObservable();
    }

    public getCountries(): Observable<Country[]> {
        return this.http.get<Country[]>('assets/countries.json').pipe(catchError(this.handleError));
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




