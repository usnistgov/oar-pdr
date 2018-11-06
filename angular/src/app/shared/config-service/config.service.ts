import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http'; 
import * as data_json   from '../../../assets/environment.json';
import * as process from 'process';
import {  PLATFORM_ID, Inject } from '@angular/core';
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
private confCall;
private envVariables = "./assets/environment.json";
private confValues={} as Config;

constructor(private http: HttpClient, @Inject(PLATFORM_ID) 
            private platformId: Object) { }
  
loadAppConfig() {
    if(isPlatformBrowser(this.platformId)){
        this.confCall =  this.http.get(this.envVariables) 
                        .toPromise()
                        .then(
                            resp =>{
                                resp as Config;
                                console.log("TEST 0 in promise then"+ resp);
                                this.confValues.RMMAPI = process.env.RMMAPI || resp['RMMAPI'];
                                this.confValues.DISTAPI =  process.env.DISTAPI || resp['DISTAPI'];
                                this.confValues.LANDING = process.env.LANDING || resp['LANDING'];
                                this.confValues.METAPI = process.env.METAPI || resp['METAPI'];
                                this.confValues.SDPAPI = process.env.SDPAPI || resp['SDPAPI'];
                                this.confValues.PDRAPI =  process.env.PDRAPI || resp['PDRAPI'];
                            },
                            err => {
                                console.log("ERROR IN CONFIG :"+err);
                            }
                        );
        
       return this.confCall; 
    }else{
            
        this.appConfig = <any>data_json;
        this.confValues.RMMAPI = process.env.RMMAPI || this.appConfig.RMMAPI;
        this.confValues.DISTAPI =  process.env.DISTAPI || this.appConfig.DISTAPI;
        this.confValues.LANDING = process.env.LANDING || this.appConfig.LANDING;
        this.confValues.METAPI = process.env.METAPI || this.appConfig.METAPI;
        this.confValues.SDPAPI   = process.env.SDPAPI || this.appConfig.SDPAPI;
        this.confValues.PDRAPI =  process.env.PDRAPI || this.appConfig.PDRAPI;
    }    
}

 getConfig() {
    return this.confValues;
 }
}