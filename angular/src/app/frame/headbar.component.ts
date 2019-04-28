import { Component, ElementRef } from '@angular/core';
import { AppConfig } from '../config/config';
import { CartService } from '../datacart/cart.service';
import { CartEntity } from '../datacart/cart.entity';

/**
 * A Component that serves as the header of the landing page.  
 * 
 * Features include:
 * * Set as black bar at the top of the page
 * * NIST PDR logo that links to the PDR home page (currently the SDP)
 * * PDR-wide links:
 *   * About page
 *   * Search page (the SDP)
 *   * User's Datacart
 * * Labels indicating the version and status of the PDR
 *   * this uses the badge style from bootstrap
 */
@Component({
    moduleId: module.id,
    selector: 'pdr-headbar',
    templateUrl: 'headbar.component.html',
    styleUrls: ['headbar.component.css']
})
export class HeadbarComponent {

    layoutCompact : boolean = true;
    layoutMode : string = 'horizontal';
    searchLink : string = "";
    status : string = "";
    appVersion : string = "";
    cartLength : number = 0;
    cartEntities : CartEntity[] = [] as CartEntity[];  // is this needed here?

    constructor(private el: ElementRef, private cfg : AppConfig,
                public cartService : CartService)
    {
        if (! (cfg instanceof AppConfig))
            throw new Error("HeadbarComponent: Wrong config type provided: "+cfg);
        this.searchLink = cfg.get("locations.pdrSearch", "/sdp/");
        this.status = cfg.get("status", "");
        this.appVersion = cfg.get("appVersion","");

        this.cartService.watchStorage().subscribe( value => {
            this.cartLength = value;
        });
    }

    // Is this needed?
    getDataCartList() {
        this.cartService.getAllCartEntities().then(function (result) {
            this.cartEntities = result;
            this.cartLength = this.cartEntities.length;
            return this.cartLength;
        }.bind(this), function (err) {
            console.error("Headbar: failure while fetching data cart size");
            console.error(err);
            // alert("something went wrong while fetching the products");
        });
        return null;
    }

    /**
     * ensure that the data cart display is up to date
     */
    updateCartStatus() {
        this.cartService.updateCartDisplayStatus(true);
        this.cartService.setCurrentCart('cart');
    }

}
