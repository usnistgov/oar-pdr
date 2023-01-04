import { Component, OnInit} from '@angular/core';
import {MessageService} from 'primeng/api';

import { ActivatedRoute } from '@angular/router';
import { ConfigurationService } from '../services/config.service';
import { RPAService } from '../services/rpa.service';
import { Record } from '../models/record.model';

@Component({
    selector:    'rpa-sme',
    templateUrl: './rpa-sme.component.html',
    styleUrls: ['./request-form.component.css'],
    providers:  [MessageService, ConfigurationService, RPAService]
  })
export class RPASMEComponent implements OnInit {

    recordId: string;
    status: string;
    record: Record;

    constructor(private route: ActivatedRoute, private rpaService: RPAService) {     }

    ngOnInit(): void {
        this.status = "pending";
        this.route.queryParams.subscribe(params => {
            this.recordId = params['id'];
            if (!params['status']) {
                this.status = "pending";
                this.rpaService.getRecord(this.recordId).subscribe(data => {
                    this.record = data.record;
                    console.log(this.record)
                })
            } else {
                this.status = params['status'];
            }
        });
    }

    onApprove(): void {
        
    }



}