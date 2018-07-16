import { Component, OnInit, AfterViewInit, ElementRef } from '@angular/core';
import { Location } from '@angular/common';
import { TreeModule,TreeNode, Tree, OverlayPanelModule,
  FieldsetModule,PanelModule,ContextMenuModule,
  MenuModule,MenuItem } from 'primeng/primeng';
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
  topmenu: MenuItem[];
  loginuser = false;

  constructor( private el: ElementRef, private appConfig : AppConfig) {
    this.SDPAPI = this.appConfig.getSDPApi();
    this.landingService = this.appConfig.getLandingBackend();
  }
  
  checkinternal() {
    if(!this.landingService.includes('rmm'))
      this.internalBadge = true;
    return this.internalBadge;
  }
}