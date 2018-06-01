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
   
    /**
   * Function to display bytes in appropriate format.
   **/ 
    formatBytes(bytes,numAfterDecimal){
        if(0==bytes)return"0 Bytes";
        var base=1000,
        d=numAfterDecimal||2,
         e=["Bytes","kB","MB","GB","TB","PB","EB","ZB","YB"],
         f=Math.floor(Math.log(bytes)/Math.log(base));
        return (bytes/Math.pow(base,f)).toFixed(d)+" "+e[f]
    }
   addtoCart(){
      alert("Coming soon");
   }
 }
