import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http'; 
import { Observable } from 'rxjs/Observable';
import * as data_json   from '../../../assets/environment.json';
import * as process from 'process';
import {  PLATFORM_ID, APP_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
export interface Config {
    RMMAPI: string ;
    DISTAPI: string;
    LANDING: string
    SDPAPI: string;
    PDRAPI: string;
    METAPI: string; 
 }

@Injectable()
export class AppConfig {
    private appConfig;
    public rmmapi;
    private distapi;
    private metaapi;
    private landingbackend;
    private sdpapi;
    private pdrapi;
private confCall;
private envVariables = "./assets/environment.json";
private confValues={} as Config;

    constructor(private http: HttpClient, @Inject(PLATFORM_ID) private platformId: Object) { }
    loadAppConfig() {
        if(isPlatformBrowser(this.platformId)){
        this.confCall =  this.http.get(this.envVariables) 
                        .toPromise()
                        .then(
                            resp =>{
                                resp as Config;
                                console.log("TEST 0 in promise then"+ resp);
                                this.rmmapi = process.env.RMMAPI || resp['RMMAPI'];
        this.distapi =  process.env.DISTAPI || resp['DISTAPI'];
        this.landingbackend = process.env.LANDING || resp['LANDING'];
        this.metaapi = process.env.METAPI || resp['METAPI'];
        this.sdpapi  = process.env.SDPAPI || resp['SDPAPI'];
        this.pdrapi =  process.env.PDRAPI || resp['PDRAPI'];
        this.confValues = resp as Config;
                            },
                            err => {
                                console.log("ERROR IN CONFIG :"+err);
                            }
                        );
        
       return this.confCall; 
        }else{
            
        this.appConfig = <any>data_json;
        this.rmmapi = process.env.RMMAPI || this.appConfig.RMMAPI;
        
        this.distapi =  process.env.DISTAPI || this.appConfig.DISTAPI;
        this.landingbackend = process.env.LANDING || this.appConfig.LANDING;
        this.metaapi = process.env.METAPI || this.appConfig.METAPI;
        this.sdpapi  = process.env.SDPAPI || this.appConfig.SDPAPI;
        this.pdrapi =  process.env.PDRAPI || this.appConfig.PDRAPI;
        console.log(" SERVER side rendering values ::"+ this.rmmapi);
        }
        this.confValues.RMMAPI = this.rmmapi;
        console.log("rmmapi:"+this.rmmapi);
    }

    getConfig() {
        // return this.appConfig;
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
    getPDRApi(){
        return this.pdrapi;
    }
    createConfObject(){
        var temp: any = {
            RMMAPi: process.env.RMMAPI,
            DISPAPI: process.env.DISPAPI,
            LANDING: process.env.LANDING,
            SDPAPI: process.env.SDPAPI,
            PDRAPI: process.env.PDRAPI,
            METAPI: process.env.METAPI
        }
        this.confValues = <Config> temp;
        console.log("Create conf object");
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