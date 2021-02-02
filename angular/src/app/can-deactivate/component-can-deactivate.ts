  
import {HostListener} from "@angular/core";
import { CartService } from '../datacart/cart.service';

export abstract class ComponentCanDeactivate {
 
    abstract  canDeactivate(): boolean;

    constructor(public cartService: CartService){

    }

    @HostListener('window:beforeunload', ['$event'])
    unloadNotification($event: any) {
        if (!this.canDeactivate()) {
            $event.returnValue = true;
        }
    }
}