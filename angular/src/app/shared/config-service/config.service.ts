import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http'; 
// import * as data_json   from '../../../assets/environment.json';
import * as process from 'process';
import {  PLATFORM_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { config } from 'rxjs';
import { Location } from '@angular/common';
export interface Config {
    RMMAPI: string ;
    DISTAPI: string;
    LANDING: string
    SDPAPI: string;
    PDRAPI: string;
    METAPI: string; 
}

const data_json = require('../../../assets/environment.json');

@Injectable()
export class AppConfig {
    private appConfig;
    private confCall;
    private envVariables = "/assets/environment.json";
    private confValues={} as Config;

    constructor(private http: HttpClient, @Inject(PLATFORM_ID) 
                private platformId: Object, location: Location) { }
    
    loadAppConfig() {
        if(isPlatformBrowser(this.platformId)){
            // console.log(" ****** HERE : in browser ::"+this.envVariables+" bsfshfsjd "+location.pathname +" ::"+location.host);
            /**
             * This check is added to avoid errors reading environment variables on server side
             * when docker deployment is used. 
             * Since nginx proxy adds additional context path, http.get
             * does not get proper url for environment by using just relative path so added /pdr 
             * here.
             */
            if(!location.host.includes("localhost:")) 
                this.envVariables = "/pdr"+this.envVariables;
            
            this.confCall =  this.http.get(this.envVariables) 
                            .toPromise()
                            .then(
                                resp =>{
                                    resp as Config;
                                    this.confValues.RMMAPI =  resp['RMMAPI'];
                                    this.confValues.DISTAPI = resp['DISTAPI'];
                                    this.confValues.LANDING = resp['LANDING'];
                                    this.confValues.METAPI =  resp['METAPI'];
                                    this.confValues.SDPAPI =  resp['SDPAPI'];
                                    this.confValues.PDRAPI =   resp['PDRAPI'];
                                    console.log(" *** In Browser read environment variables: "+ JSON.stringify(this.confValues));
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
