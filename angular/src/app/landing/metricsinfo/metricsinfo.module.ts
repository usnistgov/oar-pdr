import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetricsinfoComponent } from './metricsinfo.component';


@NgModule({
  declarations: [MetricsinfoComponent],
  imports: [
    CommonModule
  ],
  exports: [ MetricsinfoComponent ]
})
export class MetricsinfoModule { }
