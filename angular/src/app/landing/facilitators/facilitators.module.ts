import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FacilitatorsComponent } from './facilitators.component';


@NgModule({
  declarations: [FacilitatorsComponent],
  imports: [
    CommonModule
  ],
  exports: [
    FacilitatorsComponent
  ]
})
export class FacilitatorsModule { }

export {
    FacilitatorsComponent
};