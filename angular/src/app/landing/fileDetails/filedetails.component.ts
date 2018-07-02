import { Component, Input } from '@angular/core';
import {LandingComponent} from '../landing.component';
import { CartService} from '../../datacart/cart.service';
import { Data} from '../../datacart/data';

@Component({
   moduleId: module.id,  
  selector: 'filedetails-resources',
  styleUrls: ['filedetails.component.css'],
 templateUrl: 'filedetails.component.html',
})

export class FileDetailsComponent {
   @Input() fileDetails: any[];
   @Input() record: any[];
   addFileSpinner: boolean = false;


   constructor(private cartService : CartService ) {
       this.cartService.watchAddFileCart().subscribe(value => {
       this.addFileSpinner = value;
        });
   }

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

    addtoCart(resId:string,resTitle:string,resFilePath:string,id:string,fileName:string,filePath:string,fileSize:number,downloadURL:string,fileFormat:string,dataset:string,downloadedStatus:boolean){
        this.cartService.updateFileSpinnerStatus(true);
        let data : Data;
        data = {'resId':resId,'resTitle':resTitle,'resFilePath':'resFilePath','id':id,'fileName':fileName,'filePath':filePath,'fileSize':fileSize,'downloadURL':downloadURL,'fileFormat':fileFormat,'downloadedStatus':downloadedStatus
        };
        this.cartService.addDataToCart(data);
        setTimeout(()=> {
            this.cartService.updateFileSpinnerStatus(false);
        }, 3000);
    }
 }
