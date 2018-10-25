import { CartService } from '../../datacart/cart.service';
import { CartEntity } from '../../datacart/cart.entity';
import { Component, ElementRef } from '@angular/core';
import { AppConfig } from '../config-service/config.service';

/**
 * This class represents the headbar component.
 */
declare var Ultima: any;

@Component({
  moduleId: module.id,
  selector: 'pdr-headbar',
  templateUrl: 'headbar.component.html',
  styleUrls: ['headbar.component.css']
})

export class HeadbarComponent {

  layoutCompact: boolean = true;
  layoutMode: string = 'horizontal';
  darkMenu: boolean = false;
  profileMode: string = 'inline';
  SDPAPI : string = "";
  landingService : string = "";
  internalBadge: boolean = false;
  cartEntities: CartEntity[];
  loginuser = false;
  cartLength : number;

  constructor( private el: ElementRef,  private cartService: CartService, private appConfig : AppConfig) {
    this.SDPAPI = this.appConfig.getSDPApi();
    this.landingService = this.appConfig.getLandingBackend();
      this.cartService.watchStorage().subscribe(value => {
          this.cartLength = value;
      });
  }
  
  checkinternal() {
    if(!this.landingService.includes('rmm'))
      this.internalBadge = true;
    return this.internalBadge;
  }

  getDataCartList () {
    this.cartService.getAllCartEntities().then(function (result) {
    this.cartEntities = result;
    this.cartLength = this.cartEntities.length;
    return this.cartLength;
    }.bind(this), function (err) {
      alert("something went wrong while fetching the products");
    });
    return null;
  }

  updateCartStatus()
  {
    this.cartService.updateCartDisplayStatus(true);
  }

}