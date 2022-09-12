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

    getFileLevelMetrics(ediid: string): Observable<any> {
        let url = this.metricsBackend + "files?exclude=_id&include=ediid,filepath,success_get,download_size&ediid=" + ediid;
        console.log("metrics url", url)
        const request = new HttpRequest(
            "GET", url, 
            { headers: new HttpHeaders({ 'Content-Type': 'application/json', 'responseType': 'blob' }), reportProgress: true, responseType: 'blob' });

        return this.http.request(request);
    }

    getRecordLevelMetrics(ediid: string): Observable<any> {
        let url = this.metricsBackend + "records/" + ediid;

        const request = new HttpRequest(
            "GET", url, 
            { headers: new HttpHeaders({ 'Content-Type': 'application/json', 'responseType': 'blob' }), reportProgress: true, responseType: 'blob' });

        return this.http.request(request);
    }
}
