import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DownloadConfirmComponent } from './download-confirm/download-confirm.component';
import { CartcontrolComponent } from './cartcontrol/cartcontrol.component';
import { BundleplanComponent } from './bundleplan/bundleplan.component';
import { CartService } from "./cart.service";
import { DatacartComponent } from './datacart.component';
import { SharedModule } from '../shared/shared.module';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { TreeModule, FieldsetModule, DialogModule, OverlayPanelModule } from 'primeng/primeng';
import { TreeTableModule } from 'primeng/treetable';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { TreetableComponent } from './treetable/treetable.component';
import { CanDeactivateGuard } from '../can-deactivate/can-deactivate.guard';


@NgModule({
  declarations: [ 
      DatacartComponent, 
      DownloadConfirmComponent, 
      CartcontrolComponent, 
      BundleplanComponent, TreetableComponent
  ],
  imports: [
    CommonModule, SharedModule, ProgressSpinnerModule, NgbModule, TreeModule, FieldsetModule, DialogModule, OverlayPanelModule, TreeTableModule, ButtonModule, TooltipModule
  ],
  exports: [
    DatacartComponent
  ],
  entryComponents: [
    DownloadConfirmComponent
  ],
  providers: [
    CartService,
    CanDeactivateGuard
  ]
})
export class DatacartModule {

 }
