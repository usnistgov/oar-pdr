import { Component, OnInit, Inject, PLATFORM_ID } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';

@Component({
    selector: 'app-bulk-download',
    templateUrl: './bulk-download.component.html',
    styleUrls: ['./bulk-download.component.css']
})
export class BulkDownloadComponent implements OnInit {
    inBrowser: boolean = false;
    ediid: string = "dataset-id";

    constructor(private route: ActivatedRoute,
                @Inject(PLATFORM_ID) private platformId: Object)
    {
        this.inBrowser = isPlatformBrowser(platformId);
    }

    ngOnInit(): void {
        if (this.inBrowser) {
            this.route.params.subscribe(queryParams => {
                if (queryParams.id)
                    this.ediid = queryParams.id;
            });
        }
    }

}
