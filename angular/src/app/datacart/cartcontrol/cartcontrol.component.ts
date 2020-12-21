import { Component, OnInit, Input, Output, HostListener, SimpleChanges, EventEmitter } from '@angular/core';
import { TreeNode } from 'primeng/primeng';
import { AppConfig } from '../../config/config';
import { CartService } from '../cart.service';
import { DownloadService } from '../../shared/download-service/download-service.service';

@Component({
  selector: 'app-cartcontrol',
  templateUrl: './cartcontrol.component.html',
  styleUrls: ['./cartcontrol.component.css', '../datacart.component.css']
})
export class CartcontrolComponent implements OnInit {
    imageURL: string = 'assets/images/sdp-background.jpg';
    selectedFileCount: number = 0;
    screenWidth: number;
    screenSizeBreakPoint: number;
    totalDownloaded: number = 0; 
    noFileDownloaded: boolean = true; // will be true if any item in data cart is downloaded
    
    @Input() dataFiles: TreeNode[] = [];

    constructor(
        private cfg: AppConfig,
        private downloadService: DownloadService,
        public cartService: CartService
    ) { 
        this.screenSizeBreakPoint = +this.cfg.get("screenSizeBreakPoint", "1060");

        // this.cartService._watchRemoteCommand((command) => {
        //     switch(command.command) { 
        //         case 'resetDownloadParams': {
        //             break;
        //         }
        //         default: { 
        //            //statements; 
        //            break; 
        //         } 
        //      } 
        // });

        this.cartService.watchSelectedFileCount((value) => {
            this.selectedFileCount = value;
        });

        this.downloadService.watchTotalFileDownloaded((value) => {
            this.totalDownloaded = value;
        });
    }

    ngOnInit() {
        this.downloadService.watchAnyFileDownloaded().subscribe(
            value => {
                this.noFileDownloaded = !value;
                if (value) {
                    this.downloadService.setTotalFileDownloaded(this.downloadService.getTotalDownloadedFiles(this.dataFiles));
                }
            }
        );
    }

    getDownloadStatusColor(downloadStatus: string){
        return this.cartService.getDownloadStatusColor(downloadStatus);
    }

    getStatusForDisplay(downloadStatus: string){
        return this.cartService.getStatusForDisplay(downloadStatus);
    }

    getIconClass(downloadStatus: string){
        return this.cartService.getIconClass(downloadStatus);
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
        this.screenWidth = window.innerWidth;
    }

    /*
        Return button color based on Downloaded status
    */
    getButtonColor() {
        if (this.noFileDownloaded) {
            return "#1E6BA1";
        } else {
            return "#307F38";
        }
    }

    /*
        Return text color for Remove Downloaded badge
    */
    getDownloadedColor() {
        if (this.noFileDownloaded) {
            return "rgb(82, 82, 82)";
        } else {
            return "white";
        }
    }

    /*
        Return background color for Remove Downloaded badge
    */
    getDownloadedBkColor() {
        if (this.noFileDownloaded) {
            return "white";
        } else {
            return "green";
        }
    }

    /**
     *  Download selected files
     */
    executeCommand(command: string){
        this.cartService.executeCommand(command);
    }
}
