import { CartService } from '../../datacart/cart.service';
import { CartEntity } from '../../datacart/cart.entity';
import { Component, ElementRef } from '@angular/core';
import { AppConfig } from '../config-service/config.service';
import { AuthService } from '../../shared/auth-service/auth.service';
import { CommonVarService } from '../../shared/common-var';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
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
  SDPAPI: string = "";
  landingService: string = "";
  internalBadge: boolean = false;
  cartEntities: CartEntity[];
  loginuser = false;
  cartLength: number;
  ediid: any;
  isAuthenticated: boolean = false;
  navbarOpen: boolean = false;
  isEditMode: boolean = false;

  constructor(private el: ElementRef,
    private cartService: CartService,
    private appConfig: AppConfig,
    private router: Router,
    private commonVarService: CommonVarService,
    private authService: AuthService) {
    this.SDPAPI = this.appConfig.getConfig().SDPAPI;
    this.landingService = this.appConfig.getConfig().LANDING;
    this.cartService.watchStorage().subscribe(value => {
      this.cartLength = value;
    });
    this.commonVarService.watchEditMode().subscribe(
      value => {
        this.isEditMode = value;
      }
    );
  }

  ngOnInit() {
    this.ediid = this.commonVarService.getEdiid();
    this.authService.watchAuthenticateStatus().subscribe(
      value => {
        this.isAuthenticated = value;
      }
    );
  }

  checkinternal() {
    if (!this.landingService.includes('rmm'))
      this.internalBadge = true;

    //For testing, always return true
    this.internalBadge = true;
    return this.internalBadge;
  }

  getDataCartList() {
    this.cartService.getAllCartEntities().then(function (result) {
      this.cartEntities = result;
      this.cartLength = this.cartEntities.length;
      return this.cartLength;
    }.bind(this), function (err) {
      alert("something went wrong while fetching the products");
    });
    return null;
  }

  updateCartStatus() {
    this.cartService.updateCartDisplayStatus(true);
  }

  goHome() {
    this.router.navigate(['/od/id/', this.ediid], { fragment: '' });
  }

  logout() {
    this.authService.setAuthenticateStatus(false);
    this.goHome();
  }

  toggleNavbar() {
    this.navbarOpen = !this.navbarOpen;
  }

  private isOpen = '';

  toggled(event) {
    if (event) {
      console.log('is open');
      this.isOpen = 'is open'
    } else {
      console.log('is closed');
      this.isOpen = 'is closed'
    }
  }

  login() {
    this.router.navigate(['/login']);
  }
}