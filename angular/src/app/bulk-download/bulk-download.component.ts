import { Component, OnInit, Inject, PLATFORM_ID } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { trigger, state, style, animate, transition } from '@angular/animations';

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
    previewCommand: string;
    previewCopied: boolean = false;
    startDownloadCommand: string;
    startDownloadCopied: boolean = false;
    helpCommand: string;
    helpCopied: boolean = false;

    constructor(private route: ActivatedRoute,
                @Inject(PLATFORM_ID) private platformId: Object)
    {
        this.inBrowser = isPlatformBrowser(platformId);
    }

    ngOnInit(): void {
        if (this.inBrowser) {
            this.route.params.subscribe(queryParams => {
                if (queryParams.id) {
                    this.ediid = queryParams.id;
                    this.previewCommand = "python pdrdownload.py -I " + this.ediid;
                    this.startDownloadCommand = "python pdrdownload.py -I " + this.ediid + " -D";
                    this.helpCommand = "python pdrdownload.py --help";
                }
            });
        }
    }

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
}
