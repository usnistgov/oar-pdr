import { CartConstants } from './cartconstants';
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Observable } from 'rxjs';
import { DataCart } from '../datacart/cart';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { AppConfig } from '../config/config';

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
            return this._getRpaCart(backend).subscribe(
                (result) => {
                    let data = {};
                    result.metadata.forEach((d) =>{
                        let key = cartName+'/'+d.filePath;
                        d['key'] = key;
                        d["isSelected"] = true;
                        data[key] = d;
                    })
                    let out: DataCart = new DataCart(cartName, data, null, 0);
                    subscriber.next(out);
                    subscriber.complete();
                }, (err) =>{
                    console.log("err", err);
                    subscriber.next(null);
                    subscriber.complete();
                }
            )
        })
    }

    public _getRpaCart(url: string) : Observable<any> {
        return this.http.get(url);
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

