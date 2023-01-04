import { HttpClient, HttpHeaders } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { parse } from 'yaml';
import { readFileSync } from 'fs';
import { Dataset } from "../models/dataset.model";
import { Observable, Subject } from "rxjs";
import { FormTemplate } from "../models/form-template.model";


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

    public getCountries() {
        return this.http.get('assets/countries.json').subscribe(data =>{
            console.log(data);
          })
    }
}




