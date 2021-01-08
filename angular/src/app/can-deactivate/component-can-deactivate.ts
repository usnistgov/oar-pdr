import {HostListener} from "@angular/core";
import { CartService } from '../datacart/cart.service';

export abstract class ComponentCanDeactivate {
 
    abstract  canDeactivate(): boolean;

    constructor(public cartService: CartService){

    }

    @HostListener('window:beforeunload', ['$event'])
    unloadNotification($event: any) {
        $event.preventDefault();
        if (!this.canDeactivate()) {
            this.cartService.executeCommand("cancelDownloadAll");
            $event.returnValue = true;
        }
    }
}