import { Injectable, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/operator/map';
import 'rxjs/operator/catch';
import { AppConfig } from '../../config/config';

/**
 * This class provides the TaxonomyList service with methods to read taxonomies and add names.
 */
@Injectable({
  providedIn: 'root'
})
export class TaxonomyListService {
  private landingBackend : string = "";

  /**
   * Creates a new TaxonomyListService with the injected Http.
   * @param {HttpClient} http - The injected Http.
   * @constructor
   */
  constructor(private http: HttpClient,
    private cfg: AppConfig) {
      console.log("AppConfig", cfg);
      this.landingBackend = cfg.get("locations.mdService", "/unconfigured");
      if (this.landingBackend == "/unconfigured")
          throw new Error("mdService endpoint not configured!");
  }

  /**
   * Returns an Observable for the HTTP GET request for the JSON resource.
   * @return {string[]} The Observable for the HTTP request.
   */
  get(level: number): Observable<any> {
    if (level == 0)
      return this.http.get(this.landingBackend + 'taxonomy?');
    else
      return this.http.get(this.landingBackend + 'taxonomy?level=' + level.toString());
  }

  /**
    * Handle HTTP error
    */
  private handleError(error: any) {
    // In a real world app, we might use a remote logging infrastructure
    // We'd also dig deeper into the error to get a better message
    let errMsg = (error.message) ? error.message :
      error.status ? `${error.status} - ${error.statusText}` : 'Server error';
    console.error(errMsg); // log to console instead
    return Observable.throw(errMsg);
  }
}

