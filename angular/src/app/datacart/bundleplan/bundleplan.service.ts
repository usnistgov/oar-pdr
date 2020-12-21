import { Injectable } from '@angular/core';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { ZipData } from '../../shared/download-service/zipData';
import { DownloadData } from '../../shared/download-service/downloadData';
import { Bundleplan } from './bundleplan';
import { DownloadService } from '../../shared/download-service/download-service.service';

@Injectable({
  providedIn: 'root'
})
export class BundleplanService {
    zipData: ZipData[] = [];
    downloadData: DownloadData[];
    allDownloadCancelled: boolean = false;

    constructor(
        public gaService: GoogleAnalyticsService,
        private downloadService: DownloadService
    ) { }

}
