import { Component, OnInit, Input, Output, HostListener, Inject, PLATFORM_ID } from '@angular/core';
import { TreeNode } from 'primeng/primeng';
import { AppConfig } from '../../config/config';
import { CartService } from '../cart.service';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-cartcontrol',
  templateUrl: './cartcontrol.component.html',
  styleUrls: ['./cartcontrol.component.css', '../datacart.component.css']
})
export class CartcontrolComponent implements OnInit {
    imageURL: string = 'assets/images/sdp-background.jpg';
    selectedFileCount: number = 0;
    screenWidth: number = 1080;
    screenSizeBreakPoint: number;
    totalDownloaded: number = 0; 
    inBrowser: boolean = false;
    noFileDownloaded: boolean = true; // will be true if any item in data cart is downloaded
    // dataFiles: TreeNode[] = [];

    @Input() dataFiles: TreeNode[] = [];

    constructor(
        private cfg: AppConfig,
        private downloadService: DownloadService,
        public cartService: CartService,
        @Inject(PLATFORM_ID) private platformId: Object
    ) { 
        this.inBrowser = isPlatformBrowser(platformId);
        this.screenSizeBreakPoint = +this.cfg.get("screenSizeBreakPoint", "1060");

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
                if(this.inBrowser){
                    this.noFileDownloaded = !value;
                    if (value) {
                        this.downloadService.setTotalFileDownloaded(this.downloadService.getTotalDownloadedFiles(this.dataFiles));
                    }
                }
            }
        );
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
        if (this.noFileDownloaded) {
            return "#1E6BA1";
        } else {
            return "#307F38";
        }
    }

    /**
     * Return text color for Remove Downloaded badge
     */
    getDownloadedColor() {
        if (this.noFileDownloaded) {
            return "rgb(82, 82, 82)";
        } else {
            return "white";
        }
    }

    /**
     * Return background color for Remove Downloaded badge
     */
    getDownloadedBkColor() {
        if (this.noFileDownloaded) {
            return "white";
        } else {
            return "green";
        }
    }

    /**
     * Issue a command (from control buttons)
     *      - Download selected
     *      - Remove selected
     *      - Remove downloaded
     * @param command 
     */
    executeCommand(command: string){
        this.cartService.executeCommand(command);
    }
}
