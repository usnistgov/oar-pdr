import { CartConstants } from './cartconstants';
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Observable } from 'rxjs';
import { DataCart } from '../datacart/cart';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { AppConfig } from '../config/config';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

interface CartLookup {
    /**
     * a lookup for remembered carts based on name.  
     */
    [propName: string]: DataCart;
}

/**
 * The cart service provides access to data carts.  It ensures that there is only one 
 * cart instance with a given name shared across a single javascript execution context.
 */
@Injectable()
export class CartService {
    public CART_CONSTANTS: any = CartConstants.cartConst;
    carts : CartLookup = {};
    rpaBackend: string;
    portalBase: string;

    constructor(
        private http: HttpClient,
        private cfg: AppConfig,) { 
            this.rpaBackend = cfg.get("APIs.rpaBackend", "/unconfigured");
            if (this.rpaBackend == "/unconfigured")
                throw new Error("APIs.rpaBackend endpoint not configured!");
    
            if (! this.rpaBackend.endsWith("/")) this.rpaBackend += "/"
            this.portalBase = cfg.get("locations.portalBase", "/unconfigured");
        }

    /**
     * return the cart instance with the given name.  This is normally an EDIID for a 
     * cart specific to a dataset.  See also getGlobalCart().  
     */
    public getCart(name : string) : DataCart {
        if (! this.carts[name])
            this.carts[name] = DataCart.openCart(name);
        return this.carts[name];
    }

    public getRpaCart(id: string, cartName: string) : Observable<any> {
        let backend: string = this.rpaBackend + id;

        return new Observable<any>(subscriber => {
            return this._getRpaCart(backend).pipe(
                catchError(err => {
                    // Check if the error is a 404 and has the specific message
                    if (err.status === 404 && err.error?.message === "metadata not found: metadata list is empty") {
                        // Propagate a user-friendly error message
                        return throwError(() => new Error("Dataset no longer available for download"));
                    }
                    // Propagate other errors as they are
                    return throwError(() => err);
                })
            ).subscribe(
                (result) => {
                    let data = {};
                    // Extract the dataset ID to use as the display name
                    const datasetId = result.metadata[0]?.aipid || cartName;
                    result.metadata.forEach((d) => {
                        let key = cartName + '/' + d.filePath;
                        d['key'] = key;
                        d["isSelected"] = true;
                        data[key] = d;
                    });
                    let out: DataCart = new DataCart(cartName, data, null, 0);
                    // Set the display name to the dataset ID
                    out.setDisplayName(datasetId);

                    // Save the cart
                    out.save();
                    subscriber.next(out);
                    subscriber.complete();
                }, 
                (err) => {
                    // Log the error or handle it if needed
                    const errorMessage = this.getErrorMessage(err);
                    console.error("Error in getRpaCart:", errorMessage);
                    subscriber.error(errorMessage); // Propagate the error to the component
                    subscriber.complete();
                }
            );
        });
    }

    
    public _getRpaCart(url: string) : Observable<any> {
        return this.http.get(url);
    }

    /**
     * Utility function to get the error message
     * @param error The error object or a function returning an error object
     * @returns The extracted error message
     */  
    private getErrorMessage(error: any): string {
        // Check if the error is a function and call it to get the Error object
        const errorObj = typeof error === 'function' ? error() : error;
        
        // Return the error message
        return errorObj.message;
    }

    /**
     * return the instance of the global cart which can contain data files from many datasets
     */
    public getGlobalCart() : DataCart {
        return this.getCart(this.CART_CONSTANTS.GLOBAL_CART_NAME);
    }

    /**
     * shut down the given DataCart and throw away its contents.  This is intended for cleaning up
     * a dataset-specific data cart after it has been used to download all its data.  
     * 
     * It is an error to pass a DataCart that was not returned by this service via getCart(): an 
     * error message will be recorded with the console and the request will be ignored.  It is 
     * also not possible to forget the global DataCart.  
     */
    public dropCart(cart : DataCart) : void {
        let name : string = cart.getName();
        if (name == this.CART_CONSTANTS.GLOBAL_CART_NAME) {
            console.warn("Attempt to drop the global cart; Ignoring.");
            return;
        }

        if (this.carts[name] !== cart) {
            console.error("Attempt to drop outlaw data cart by the name of '"+name+"'!");
            return;
        }
        cart._forget();
        delete this.carts[name];
    }
}

