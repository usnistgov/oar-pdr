import { Component, Input } from '@angular/core';
import {LandingComponent} from '../landing.component'; 

@Component({
   moduleId: module.id,  
  selector: 'filedetails-resources',
  styleUrls: ['filedetails.component.css'],
 templateUrl: 'filedetails.component.html',
})

export class FileDetailsComponent {
   @Input() fileDetails: any[];

   download(){
       window.open(this.fileDetails["downloadURL"]);
       //alert("download here");
   }

   addtoCart(){
      alert("Coming soon");
   }
 }
