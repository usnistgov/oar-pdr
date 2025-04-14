import { Component, OnInit, Inject, PLATFORM_ID, ViewChild, ElementRef } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { AppConfig } from '../config/config';

@Component({
    selector: 'app-bulk-download',
    templateUrl: './bulk-download.component.html',
    styleUrls: ['./bulk-download.component.css'],
    animations: [
        trigger(
        'enterAnimation', [
            transition(':enter', [
            style({height: '0px', opacity: 0}),
            animate('700ms', style({height: '100%', opacity: 1}))
            ]),
            transition(':leave', [
            style({height: '100%', opacity: 1}),
            animate('700ms', style({height: 0, opacity: 0}))
            //   animate('500ms', style({transform: 'translateY(0)', opacity: 1}))
            ])
        ]
        )
    ]
})
export class BulkDownloadComponent implements OnInit {
    inBrowser: boolean = false;
    ediid: string = "dataset-id";
    previewCommand: string = "python pdrdownload.py -I " + this.ediid;
    previewCopied: boolean = false;
    startDownloadCommand: string = "python pdrdownload.py -I " + this.ediid + " -D";
    startDownloadCopied: boolean = false;
    helpCommand: string = "python pdrdownload.py --help";
    helpCopied: boolean = false;
    pdrbase: string;
    downloadscriptCopied: boolean = false;

    @ViewChild('downloadall') downloadAll: ElementRef;
    @ViewChild('pyscript') pyscript: ElementRef;
    @ViewChild('addtocart') addToCart: ElementRef;
    @ViewChild('downloadAPI') downloadAPI: ElementRef;
    

    constructor(private route: ActivatedRoute,
                @Inject(PLATFORM_ID) private platformId: Object,
                private cfg : AppConfig)
    {
        this.inBrowser = isPlatformBrowser(platformId);
        this.pdrbase = cfg.get<string>("locations.portalBase", "/");
        if (! this.pdrbase.endsWith('/'))
            this.pdrbase += '/';
    }

    ngOnInit(): void {
        if (this.inBrowser) {
            this.route.params.subscribe(queryParams => {
                if (queryParams.id) {
                    this.ediid = queryParams.id;
                    this.previewCommand = "python pdrdownload.py -I " + this.ediid;
                    this.startDownloadCommand = "python pdrdownload.py -I " + this.ediid + " -D";
                }
            });
        }
    }

    /**
     * Copy the given string to clipboard
     * @param val - input string to be copied to clipboard
     * @param command - indicate which command was copied so the command will be highlighted.
     */
    copyToClipboard(val: string, command: string){
        const selBox = document.createElement('textarea');
        selBox.style.position = 'fixed';
        selBox.style.left = '0';
        selBox.style.top = '0';
        selBox.style.opacity = '0';
        selBox.value = val;
        document.body.appendChild(selBox);
        selBox.focus();
        selBox.select();
        document.execCommand('copy');
        document.body.removeChild(selBox);

        switch (command) {
            case ("preview"): 
                this.previewCopied = true;
                setTimeout(() => {
                    this.previewCopied = false;
                }, 2000);
                break;
            case ('startDownload'):
                this.startDownloadCopied = true;
                setTimeout(() => {
                    this.startDownloadCopied = false;
                }, 2000);
                break;
            default:
                this.helpCopied = true;
                setTimeout(() => {
                    this.helpCopied = false;
                }, 2000);
                break;
        }
    }

    /**
     * Scroll to a specific section of the page
     * @param sectionId - the section the page will scroll to.
     */
    goToSection(sectionId) {
        if(sectionId == null) sectionId = "top";

        switch(sectionId) { 
            case "downloadAll": { 
                this.downloadAll.nativeElement.scrollIntoView({behavior: 'smooth'}); 
                break; 
            } 
            case "pyscript": { 
                this.pyscript.nativeElement.scrollIntoView({behavior: 'smooth'}); 
                this.downloadscriptCopied = true;
                setTimeout(() => {
                    this.downloadscriptCopied = false;
                }, 2000);
                break; 
            } 
            case "addToCart": {
                this.addToCart.nativeElement.scrollIntoView({behavior: 'smooth'}); 
                break;
            }
            case "downloadAPI": {
                this.downloadAPI.nativeElement.scrollIntoView({behavior: 'smooth'}); 
                break;
            }
            default: { // GO TOP
                window.scrollTo({
                    top: 0,
                    left: 0,
                    behavior: 'smooth'
                  });
                break; 
            } 
        } 
    }
}
