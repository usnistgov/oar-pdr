import { Component, OnInit, Input, EventEmitter, Output, ElementRef, ViewChild } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ZipData } from '../../shared/download-service/zipData';
import { formatBytes } from '../../utils';
import { AppConfig } from '../../config/config';

@Component({
    selector: 'app-download-confirm',
    templateUrl: './download-confirm.component.html',
    styleUrls: ['./download-confirm.component.css','../datacart.component.css']
})
export class DownloadConfirmComponent implements OnInit {
    @Input() bundle_plan_size: number;
    @Input() zipData: ZipData[];
    @Input() totalFiles: number;
    @Output() returnValue: EventEmitter<boolean> = new EventEmitter();

    bundleSizeAlert: number;

    constructor(public activeModal: NgbActiveModal,
                private cfg: AppConfig) 
    { }

    ngOnInit() 
    {
        this.bundleSizeAlert = +this.cfg.get("bundleSizeAlert", "1000000000");
    }

    /**
     * When user clicks on Continue Download, close the pop up dialog and continue downloading.
     */
    ContinueDownload() 
    {
        this.returnValue.emit(true);
        this.activeModal.close('Close click');
    }

    /** 
     * When user click on Cancel, close the pop up dialog and do nothing.
     */
    CancelDownload() 
    {
        this.returnValue.emit(false);
        this.activeModal.close('Close click');
    }

    /**
     * Return row background color
     * @param i - row number
     */
    getBackColor(i: number) : string {
        if (i % 2 != 0) return 'rgb(231, 231, 231)';
        else return 'white';
    }

    getSizeForDisplay(size: number) : string {
        return formatBytes(size);
    }
}
