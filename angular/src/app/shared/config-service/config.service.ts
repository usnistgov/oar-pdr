import { Injectable } from '@angular/core';
import { Http,Response } from '@angular/http';
import { HttpClient } from '@angular/common/http'; 
import { Observable } from 'rxjs/Observable';
import * as data_json   from '../../../assets/environment.json';

@Injectable()
export class AppConfig {
    private appConfig;
    constructor(private http: HttpClient) { }
    loadAppConfig() {
        this.appConfig = <any>data_json;
        const rmmapi = (<any>data_json).RMMAPI;
        // this.getJSON().subscribe(data => {
        //     console.log(data)
        // });
    }
    public getJSON(): Observable<any> {
        return this.http.get("../../../assets/environment.json")
    }
//   constructor(private http: Http) { }
//   loadAppConfig() {
//     return this.http.get('http://localhost:4200/assets/environment.json')
//       .toPromise()
//       .then(data => {
//         console.log("Config read:"+ data);
//         this.appConfig = data;
//         console.log("Config read:"+this.appConfig);
//       }).catch(( error ) => {
//         console.log("Error reading config :"+error);
//       }); 
//   }

    getConfig() {
        return this.appConfig;
    }
}