import { Component, OnInit, OnChanges, SimpleChanges, Input, Output,
         HostListener, Inject, PLATFORM_ID, EventEmitter } from '@angular/core';
import { TreeNode } from 'primeng/api';
import { AppConfig } from '../../config/config';
import { CartService } from '../cart.service';
import { DataCart } from '../cart';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-cartcontrol',
  templateUrl: './cartcontrol.component.html',
  styleUrls: ['./cartcontrol.component.css', '../datacart.component.css']
})
export class CartcontrolComponent implements OnInit, OnChanges {
    imageURL: string = 'assets/images/sdp-background.jpg';

    inBrowser: boolean = false;
    screenWidth: number = 1080;
    screenSizeBreakPoint: number;
    selectedFileCount: number = 0;
    totalDownloaded: number = 0;
    datacart: DataCart = null;

    @Input() cartName: string;
    @Output() onDownloadSelected = new EventEmitter<boolean>();  
    @Output() onRemoveSelected = new EventEmitter<boolean>();  
    @Output() onRemoveDownloaded = new EventEmitter<boolean>();  

    constructor(
        private cfg: AppConfig,
        public cartService: CartService,
        @Inject(PLATFORM_ID) private platformId: Object
    ) { 
        this.inBrowser = isPlatformBrowser(platformId);
        this.screenSizeBreakPoint = +this.cfg.get("screenSizeBreakPoint", "1060");
    }

    ngOnInit() {
        if (this.cartName) {
            this.datacart = this.cartService.getCart(this.cartName);
            this.updateCounts();

            this.datacart.watchForChanges((ev) => {
                this.updateCounts();
            });
        }
    }
    
    ngOnChanges(changes: SimpleChanges) {
        // cart name should not change
        if (changes.cartName && this.datacart)
            this.cartName = this.datacart.getName();
    }

    updateCounts() : void {
        if (! this.datacart) return;

        this.selectedFileCount = this.datacart.getSelectedFiles().length;
        this.totalDownloaded = this.datacart.getDownloadedFiles().length; 
    }

    /**
     * return true if any files from this cart have been marked as downloaded
     */
    anyDownloaded() : boolean { return this.totalDownloaded > 0; }

    /**
     * react to the "download selected" button: start download planning and processing
     */
    downloadSelected() : void {
        this.onDownloadSelected.emit(true);
    }

    /**
     * react to the "remove downloaded" button: signal that files should be removed from the cart
     */
    removeDownloaded() : void {
        this.onRemoveDownloaded.emit(true);
    }

    /**
     * react to the "remove selected" button: signal that files should be removed from the cart
     */
    removeSelected() : void {
        this.onRemoveSelected.emit(true);
    }

    /**
     *  Following functions detect screen size
     */
    @HostListener("window:resize", [])
    public onResize() {
        this.detectScreenSize();
    }

    public ngAfterViewInit() {
        this.detectScreenSize();
    }

    private detectScreenSize() {
        setTimeout(() => {
            if(this.inBrowser){
                this.screenWidth = window.innerWidth;
            }
        }, 0);
    }

    /**
     * Return button color based on Downloaded status
     */
    getButtonColor() {
        if (! this.anyDownloaded()) {
            return "#1E6BA1";
        } else {
            return "#307F38";
        }
    }

    /**
     * Return text color for Remove Downloaded badge
     */
    getDownloadedColor() {
        if (!this.anyDownloaded()) {
            return "rgb(82, 82, 82)";
        } else {
            return "white";
        }
    }

    /**
     * Return background color for Remove Downloaded badge
     */
    getDownloadedBkColor() {
        if (!this.anyDownloaded()) {
            return "white";
        } else {
            return "green";
        }
    }
}
