import { Component, OnInit, AfterViewInit, ElementRef } from '@angular/core';
import { Location } from '@angular/common';
import { TreeModule,TreeNode, Tree, OverlayPanelModule,
  FieldsetModule,PanelModule,ContextMenuModule,
  MenuModule,MenuItem } from 'primeng/primeng';

  import { CommonVarService } from "../common-var/index";  
// import { environment } from '../../environment';

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
  SDPAPI : string = "environment.SDPAPI";
  landingService : string = "environment.LANDING";
  internalBadge: boolean = false;
  topmenu: MenuItem[];
  loginuser = false;

  constructor( private el: ElementRef, private commonVar : CommonVarService) {
    this.createTopMenu();
  }
  
  checkinternal() {
    if(!this.landingService.includes('rmm'))
      this.internalBadge = true;
    return this.internalBadge;
  }

  createTopMenu(){
    this.topmenu = [
      {label:"About"},
      {label:"Search"},
      {label:"Login"}  ];
  }
  
  login(){
    //alert(this.loginuser);
    // this.commonVar.setLogin(!this.loginuser);
    this.commonVar.userConfig(!this.loginuser);
    //this.loginuser = this.commonVar.getLogin();
    this.commonVar.userObservable.subscribe(value => {
      this.loginuser = value;
      console.log(this.loginuser);
    })
  }
}