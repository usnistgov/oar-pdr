import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http'; 
import { Observable } from 'rxjs/Observable';
import * as data_json   from '../../../assets/environment.json';
import * as process from 'process';

@Injectable()
export class AppConfig {
    private appConfig;
    private rmmapi;
    private distapi;
    private metaapi;
    private landingbackend;
    private sdpapi;

    constructor(private http: HttpClient) { }
    loadAppConfig() {
        this.appConfig = <any>data_json;
        // console.log(" this test process api ::"+ process.env.RMMAPI);
        this.rmmapi = process.env.RMMAPI || this.appConfig.RMMAPI;
        this.distapi =  process.env.DISTAPI || this.appConfig.DISTAPI;
        this.landingbackend = process.env.LANDING || this.appConfig.LANDING;
        this.metaapi = process.env.METAPI || this.appConfig.METAPI;
        this.sdpapi  = process.env.SDPAPI || this.appConfig.SDPAPI;
    }
   

    getConfig() {
        return this.appConfig;
    }
    getRMMapi(){
        return this.rmmapi;
    }
    getDistApi(){
        return this.distapi;
    }
    getMetaApi(){
        return this.metaapi;
    }
    getLandingBackend(){
        return this.landingbackend;
    }
    getSDPApi(){
        return this.sdpapi;
    }


     // public getJSON(): Observable<any> {
    //     return this.http.get("../../../assets/environment.json")
    // }
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
}