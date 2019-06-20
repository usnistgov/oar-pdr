import { Component, ElementRef } from '@angular/core';
import { AppConfig } from '../config/config';
import { CartService } from '../datacart/cart.service';
import { CartEntity } from '../datacart/cart.entity';
import { AuthService } from '../shared/auth-service/auth.service';
import { Router } from '@angular/router';
import { CommonVarService } from '../shared/common-var';

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

  layoutCompact: boolean = true;
  layoutMode: string = 'horizontal';
  searchLink: string = "";
  status: string = "";
  appVersion: string = "";
  cartLength: number = 0;
  editEnabled: any;
  isAuthenticated: boolean = false;
  isEditMode: boolean = false;
  ediid: any;
  cartEntities: CartEntity[] = [] as CartEntity[];  // is this needed here?

  constructor(
    private el: ElementRef,
    private cfg: AppConfig,
    public cartService: CartService,
    private router: Router,
    private commonVarService: CommonVarService,
    private authService: AuthService) {
    if (!(cfg instanceof AppConfig))
      throw new Error("HeadbarComponent: Wrong config type provided: " + cfg);
    this.searchLink = cfg.get("locations.pdrSearch", "/sdp/");
    this.status = cfg.get("status", "");
    this.appVersion = cfg.get("appVersion", "");
    this.editEnabled = cfg.get("editEnabled", "");

    this.cartService.watchStorage().subscribe(value => {
      this.cartLength = value;
    });

    this.authService.watchAuthenticateStatus().subscribe(
      value => {
        this.isAuthenticated = value;
      }
    );

    this.commonVarService.watchEditMode().subscribe(
      value => {
        this.isEditMode = value;
      }
    );
  }

  /*
  *   init
  */
  ngOnInit() {
    this.cartLength = this.cartService.getCartSize();
  }

  /**
   * ensure that the data cart display is up to date
   */
  updateCartStatus() {
    this.cartService.updateCartDisplayStatus(true);
    this.cartService.setCurrentCart('cart');
  }

  /*
  *   Go to original landing page
  */
  goHome() {
    this.ediid = this.commonVarService.getEdiid();
    this.router.navigate(['/od/id/', this.ediid], { fragment: '' });
  }

  /*
  *   Open login window
  */
  login() {
    this.router.navigate(['/login']);
  }

  /*
  *   Logout
  */
  logout() {
    this.authService.setAuthenticateStatus(false);
    this.goHome();
  }

  /*
  *   Open about window if not in edit mode. Otherwise do nothing.
  */
  openRootPage() {
    if (!this.isEditMode)
      window.open('/', '_self');
  }

  /*
  *   Open about window if not in edit mode. Otherwise do nothing.
  */
  openAboutPage() {
    if (!this.isEditMode)
      window.open('/pdr/about', '_blank');
  }

  /*
  *   Open search window if not in edit mode. Otherwise do nothing.
  */
  openSearchPage() {
    if (!this.isEditMode)
      window.open(this.searchLink, '_blank');
  }

  /*
  *   In edit mode, top menu will be disabled - text color set to grey
  */
  getMenuTextColor() {
    if (this.isEditMode)
      return 'grey';
    else
      return 'white';
  }

  /*
  *   In edit mode, mouse cursor set to normal
  */
  getCursor() {
    if (this.isEditMode)
      return 'default';
    else
      return 'pointer';
  }
}
