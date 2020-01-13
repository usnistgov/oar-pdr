import { Component, OnInit, Input } from '@angular/core';
import { CustomizationService } from '../../../shared/customization-service/customization-service.service';
import { EditControlService } from '../edit-control.service';

@Component({
    selector: 'edit-status-bar',
    templateUrl: './edit-status-bar.component.html',
    styleUrls: ['../../landing.component.css']
})
export class EditStatusBarComponent implements OnInit {
    recordEditmode: boolean = false;
    updateDate: string = "";
    isProcessing: boolean = true;
    message: string = "";
    messageColor: string = "black";

    constructor(
        private customizationService: CustomizationService,
        private editControlService: EditControlService
    ) {
        this.editControlService.watchEditMode().subscribe(value => {
            this.recordEditmode = value;
            this.message = "";
            this.updateMessage();
        });

        this.customizationService.watchUpdatedateSub().subscribe(value => {
            this.message = "";
            this.updateDate = value;
            this.updateMessage();
        });

        this.editControlService.watchIsProcessing().subscribe(value => {
            this.isProcessing = value;
            this.updateMessage();
        });

        this.editControlService.watchMessage().subscribe(value => {
            console.log("Message:", value);
            this.message = value;
        });
    }

    ngOnInit() {
    }

    updateMessage() {
        this.messageColor = "black";
        if (this.message == undefined || this.message == null || this.message == "") {
            if (this.recordEditmode) {
                if (this.updateDate) {
                    this.message = "This record was edited on: " + this.updateDate + ".";
                } else {
                    this.message = "Click on Quit Edit button to exit edit mode.";
                }
            } else {
                if (this.updateDate) {
                    this.message = "You have draft data edited on " + this.updateDate + ". Click on edit button to continue editing.";
                    this.messageColor = "rgb(255, 115, 0)";
                } else {
                    this.message = "To see previously edited record or edit current one, click on Edit button.";
                }
            }
        }
    }
}