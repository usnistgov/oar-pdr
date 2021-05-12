import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { AppConfig } from '../../config/config';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class MetricsService {
    metricsBackend: string = "";

    constructor(
        private cfg: AppConfig,
        private http: HttpClient, ) { 

        this.metricsBackend = cfg.get("metricsAPI", "/unconfigured");
    }

    getDatasetMetrics(ediid: string): Observable<any> {
        console.log("Queryng " + this.metricsBackend + "files?exclude=_id&include=ediid,filepath,success_get,download_size&ediid=" + ediid);
        return this.http.get(this.metricsBackend + "files?exclude=_id&include=ediid,filepath,success_get,download_size&ediid=" + ediid, { headers: new HttpHeaders({ timeout: '${10000}' }) });
    }

    getRecordLevelMetrics(ediid: string): Observable<any> {
        console.log("Queryng " + this.metricsBackend + "records/" + ediid);
        return this.http.get(this.metricsBackend + "records/" + ediid, { headers: new HttpHeaders({ timeout: '${10000}' }) });
    }
}
