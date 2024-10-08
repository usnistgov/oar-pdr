import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { AppConfig } from '../../config/config';
import { HttpClient, HttpHeaders, HttpRequest } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class MetricsService {
    metricsBackend: string = "";

    constructor(
        private cfg: AppConfig,
        private http: HttpClient, ) { 

        this.metricsBackend = cfg.get("APIs.metrics", "/unconfigured");

        if (this.metricsBackend == "/unconfigured")
        throw new Error("APIs.metrics endpoint not configured!");

        if (! this.metricsBackend.endsWith("/")) this.metricsBackend += "/"

    }

    /**
     * Request file level metrics data based on ediid
     * @param ediid 
     * @returns http response
     */
    getFileLevelMetrics(ediid: string): Observable<any> {
        let url = this.metricsBackend + "files/" + ediid;
        const request = new HttpRequest(
            "GET", url, 
            { headers: new HttpHeaders({ 'Content-Type': 'application/json', 'responseType': 'blob','Connection':'keep-alive','Cache-Control':'max-age=0' }), reportProgress: true, responseType: 'blob' });
            console.log("request", request);
        return this.http.request(request);
    }

    /**
     * Request record level metrics data based on ediid
     * @param ediid 
     * @returns http response
     */
    getRecordLevelMetrics(ediid: string): Observable<any> {
        let url = this.metricsBackend + "records/" + ediid;

        const request = new HttpRequest(
            "GET", url, 
            { headers: new HttpHeaders({ 'Content-Type': 'application/json', 'responseType': 'blob' }), reportProgress: true, responseType: 'blob' });

        return this.http.request(request);
    }

    /**
     * Find a match of metrics data based on given ediid, pdrid and filepath. Ignore sha files.
     * @param fileLevelData File level metrics data returned from getFileLevelMetrics()
     * @param ediid ediid in nerdm record to find a match
     * @param pdrid pdrid in nerdm record to find a match
     * @param filepath filepath in nerdm record to find a match
     * @returns metrics data if a match found. Otherwise return null.
     */
    findFileLevelMatch(fileLevelData: any, ediid: string, pdrid: string, filepath: string) {
        if(!ediid || !pdrid || !filepath) return null;

        // Strip off 'ark:/88434/' if any
        let _ediid = ediid.replace('ark:/88434/', '');
        let _pdrid = pdrid.replace('ark:/88434/', '');
        let _filepath = filepath.trim();
        let ret: any = null;
        if(fileLevelData){
            if(_filepath) {
                if(filepath[0]=="/") _filepath = filepath.slice(1);
                _filepath = _filepath.trim();
            }

            //Check if we have multiple pdrids
            let hasMultiPdrid: boolean = false;
            let prevPdrid: string = null;
            for(let x of fileLevelData) {
                if(x.pdrid && x.pdrid.toLowerCase() != 'nan'){
                    if(!prevPdrid) {
                       prevPdrid = x.pdrid; 
                    } 
                    else if(prevPdrid != x.pdrid) {
                        hasMultiPdrid = true;
                        break;
                    }
                }
            }
            
            for(let x of fileLevelData) {
                if(x.ediid.replace('ark:/88434/', '') == _ediid && (x.filepath? x.filepath.trim()==_filepath : false) && !x.filepath.endsWith('sha256')) {
                    if(hasMultiPdrid){
                        if(x.pdrid.replace('ark:/88434/', '') == _pdrid.replace('ark:/88434/', '')) {
                            ret = x;
                            break;
                        }
                    }else{
                        ret = x;
                        break; 
                    }
                }
            }
        }

        return ret;
    }
}