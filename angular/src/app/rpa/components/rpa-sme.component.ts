import { Component, OnInit } from '@angular/core';
import { MessageService } from 'primeng/api';

import { ActivatedRoute, Router } from '@angular/router';
import { ConfigurationService } from '../services/config.service';
import { RPAService } from '../services/rpa.service';
import { Record } from '../models/record.model';

@Component({
    selector: 'rpa-sme',
    templateUrl: './rpa-sme.component.html',
    styleUrls: ['./request-form.component.css'],
    providers: [MessageService, ConfigurationService, RPAService]
})
export class RPASMEComponent implements OnInit {

    recordId: string;
    status: string;
    statusDate: string;
    record: Record;
    loaded: boolean = false;
    displayProgressSpinner: boolean = false;

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private rpaService: RPAService,
        private messageService: MessageService
    ) { }

    ngOnInit(): void {
        // get the recordId from the url
        // fetch the record using the recordId
        // check the approval status
        // use appropriate template based on status
        this.status = "pending";
        this.route.queryParams.subscribe(params => {
            this.displayProgressSpinner = false;
            this.recordId = params['id'];
            this.rpaService.getRecord(this.recordId).subscribe(data => {
                this.record = data.record;
                this.status = this.record.userInfo.approvalStatus;
                this.statusDate = this.status.replace("Approved_", "");
                this.loaded = true;
                console.log(this.record)
            });
        });
    }

    /**
     * Approve rpa request and display success message
     */
    onApprove(): void {
        this.displayProgressSpinner = true;
        this.rpaService.approveRequest(this.recordId).subscribe(data => {
            this.displayProgressSpinner = false;
            console.log("Approved!\n", data)
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'This request was approved successfully!' });
            location.reload();
        });
    }

    /**
     * Decline rpa request and display success message
     */
    onDecline(): void {
        this.displayProgressSpinner = true;
        this.rpaService.declineRequest(this.recordId).subscribe(data => {
            this.displayProgressSpinner = false;
            console.log("Declined!\n", data)
            this.statusDate = data.approvalStatus.replace("Approved_", "");
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'This request was declined successfully!' });
            location.reload();
        });
    }



}