import { Component, OnInit, AfterViewInit, ElementRef } from '@angular/core';
import { Location } from '@angular/common';
import { TreeModule,TreeNode, Tree, OverlayPanelModule,
  FieldsetModule,PanelModule,ContextMenuModule } from 'primeng/primeng';
  import {MenuModule} from 'primeng/menu';
  import { CommonVarService } from "../common-var/index";  
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
  SDPAPI : string ;
  landingService : string ;
  internalBadge: boolean = false;


  constructor( private el: ElementRef, private commonVar : CommonVarService,private appConfig : AppConfig,) {
    
    this.SDPAPI = this.appConfig.getConfig().SDPAPI;
    this.landingService = this.appConfig.getConfig().LANDING;
  
  }
  
  checkinternal() {
    if(!this.landingService.includes('rmm'))
      this.internalBadge = true;
    return this.internalBadge;
  }

}