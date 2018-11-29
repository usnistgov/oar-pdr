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
private envVariables = "/assets/environment.json";
private envVariables2 = "./assets/environment.json";

private confValues={} as Config;

constructor(private http: HttpClient, @Inject(PLATFORM_ID) 
            private platformId: Object) { }
  
loadAppConfig() {
    if(isPlatformBrowser(this.platformId)){
        console.log(" ****** HERE : in browser ::"+this.envVariables);
        var test =  this.http.get(this.envVariables) 
        .toPromise()
        .then(
            resp =>{
                resp as Config;
                console.log(" %%%%%%% TEST 1  in promise then"+ JSON.stringify(resp));
            },
            err => {
                console.log("%%%%%%% ERROR IN CONFIG :"+err);
            }
        );

        var test =  this.http.get("https://localhost/pdr/assets/environment.json") 
        .toPromise()
        .then(
            resp =>{
                resp as Config;
                console.log(" $$$$$$$ TEST 1  in promise then"+ JSON.stringify(resp));
            },
            err => {
                console.log(" $$$$$$$ ERROR IN CONFIG :"+err);
            }
        );

        this.confCall =  this.http.get(this.envVariables2) 
                        .toPromise()
                        .then(
                            resp =>{
                                resp as Config;
                                console.log("TEST 0 in promise then"+ JSON.stringify(resp));
                                this.confValues.RMMAPI =  resp['RMMAPI'];
                                this.confValues.DISTAPI = resp['DISTAPI'];
                                this.confValues.LANDING = resp['LANDING'];
                                this.confValues.METAPI =  resp['METAPI'];
                                this.confValues.SDPAPI =  resp['SDPAPI'];
                                this.confValues.PDRAPI =  resp['PDRAPI'];
                                console.log(" ****** In Browser 1: "+ JSON.stringify(this.confValues));
                            },
                            err => {
                                console.log("ERROR IN CONFIG :"+err);
                            }
                        );
                        console.log(" ****** In Browser 2: "+ JSON.stringify(this.confValues));
       return this.confCall; 
    }else{
        console.log(" ****** HERE : in server");
            
        this.appConfig = <any>data_json;
        this.confValues.RMMAPI = process.env.RMMAPI || this.appConfig.RMMAPI;
        this.confValues.DISTAPI =  process.env.DISTAPI || this.appConfig.DISTAPI;
        this.confValues.LANDING = process.env.LANDING || this.appConfig.LANDING;
        this.confValues.METAPI = process.env.METAPI || this.appConfig.METAPI;
        this.confValues.SDPAPI   = process.env.SDPAPI || this.appConfig.SDPAPI;
        this.confValues.PDRAPI =  process.env.PDRAPI || this.appConfig.PDRAPI;
        console.log(" ****** In server: "+ JSON.stringify(this.confValues));
    }    
}

 getConfig() {
    console.log(" ****** In Browser 3: "+ JSON.stringify(this.confValues));
    return this.confValues;
 }
}