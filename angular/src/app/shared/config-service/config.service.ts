import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http'; 
import * as data_json   from '../../../assets/environment.json';
import * as process from 'process';
import {  PLATFORM_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { config } from 'rxjs';
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
private confValues={} as Config;

constructor(private http: HttpClient, @Inject(PLATFORM_ID) 
            private platformId: Object) { }
  
loadAppConfig() {
    if(isPlatformBrowser(this.platformId)){
        console.log(" ****** HERE : in browser ::"+this.envVariables);
        this.confCall =  this.http.get(this.envVariables,  {responseType: 'text'}) 
                        .toPromise()
                        .then(
                            resp =>{
                                //resp as Config;
                                var respValues = JSON.parse(resp);
                                this.confValues.RMMAPI =  respValues['RMMAPI'];
                                this.confValues.DISTAPI = respValues['DISTAPI'];
                                this.confValues.LANDING = respValues['LANDING'];
                                this.confValues.METAPI =  respValues['METAPI'];
                                this.confValues.SDPAPI =  respValues['SDPAPI'];
                                this.confValues.PDRAPI =   respValues['PDRAPI'];
                                console.log("In Browser read environment variables: "+ JSON.stringify(this.confValues));
                            },
                            err => {
                                console.log("ERROR IN CONFIG :"+JSON.stringify(err));
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
        console.log(" ****** In server: "+ JSON.stringify(this.confValues));
    }    
}

 getConfig() {
    // console.log(" ****** In Browser 3: "+ JSON.stringify(this.confValues));
    return this.confValues;
 }
}