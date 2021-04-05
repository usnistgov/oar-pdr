import { Component, OnInit, Input } from '@angular/core';
import { DataCartStatus } from '../../datacart/cartstatus';
import { CartConstants } from '../../datacart/cartconstants';

@Component({
  selector: 'app-downloadstatus',
  templateUrl: './downloadstatus.component.html',
  styleUrls: ['./downloadstatus.component.css']
})
export class DownloadstatusComponent implements OnInit {
    dataCartStatus: DataCartStatus;
    public CART_CONSTANTS: any = CartConstants.cartConst;
    inited: boolean = false;

    @Input() inBrowser: boolean;

    constructor() { 

    }

    ngOnInit() {
        if(this.inBrowser){
            this.dataCartStatus = DataCartStatus.openCartStatus();

            window.addEventListener("storage", this.cartChanged.bind(this));
        }
    }

    ngAfterViewInit(): void {
        //Called after ngAfterContentInit when the component's view has been initialized. Applies to components only.
        //Add 'implements AfterViewInit' to the class.
        this.inited = true;
    }

    /**
     * When storage changed, if it's dataCartStatus, loop through each cart and restore dataCartStatus object.
     * The display will automatically pick up the data.
     * @param ev Event - storage
     */
    cartChanged(ev){
        if(this.inited){
            if(ev.key == this.dataCartStatus.getName()){
                this.dataCartStatus.restore();
            }
        }
    }

    /**
     * Get keys of dataCartStatus. The UI uses it to display download progress
     */
    get getKeys(){
        return Object.keys(this.dataCartStatus.dataCartStatusItems)
    }

    /**
     * Check if we want to display the title bar of the download status. 
     * If no status to display, we will not display the title bar.
     */
    get showDownloadStatus(){
        let hasStatusToDisplay: boolean = false;
        for(let key in this.dataCartStatus.dataCartStatusItems){
            if(this.dataCartStatus.dataCartStatusItems[key].downloadPercentage > 0){
                hasStatusToDisplay = true;
                break;
            }
        }

        return hasStatusToDisplay;
    }

    /**
     * Remove the status item from the object
     * @param key the status item to be removed
     */
    removeStatusItem(key: string){
        this.dataCartStatus.restore();
        delete this.dataCartStatus.dataCartStatusItems[key];
        this.dataCartStatus.save();
    }

    /**
     * Return the display name of a dataCartStatusItem. For global data cart, display "Global Datacart". 
     * Otherwise, display property displayName as it is.
     * @param key the key of dataCartStatusItems
     */
    cartName(key: string){
        if(this.dataCartStatus.dataCartStatusItems[key].displayName == this.CART_CONSTANTS.GLOBAL_CART_NAME)
            return "Global Datacart";
        else
            return this.dataCartStatus.dataCartStatusItems[key].displayName;
        
    }
}
