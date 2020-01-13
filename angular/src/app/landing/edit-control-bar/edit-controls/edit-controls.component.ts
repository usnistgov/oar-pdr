import { Component, OnInit, Input } from '@angular/core';
import { ConfirmationDialogService } from '../../../shared/confirmation-dialog/confirmation-dialog.service';
import { CustomizationService } from '../../../shared/customization-service/customization-service.service';
import { NotificationService } from '../../../shared/notification-service/notification.service';
import { ErrorHandlingService } from '../../../shared/error-handling-service/error-handling.service';
import { EditControlService } from '../edit-control.service';
import { errMessage } from '../../../shared/error-handling-service/error-handling.service';

@Component({
    selector: 'edit-controls',
    templateUrl: './edit-controls.component.html',
    styleUrls: ['./edit-controls.component.css']
})
export class EditControlsComponent implements OnInit {
    ediid: string;
    recordEditmode: boolean;
    dataChanged: boolean = false;
    errorMessage: errMessage;

    constructor(
        private customizationService: CustomizationService,
        private confirmationDialogService: ConfirmationDialogService,
        private notificationService: NotificationService,
        private errorHandlingService: ErrorHandlingService,
        private editControlService: EditControlService
    ) {
        this.editControlService.watchEditMode().subscribe(value => {
            this.recordEditmode = value;
        });

        this.editControlService.watchEdiid().subscribe(value => {
            this.ediid = value;
        });

        this.editControlService.watchDataChanged().subscribe(value => {
            this.dataChanged = value;
        });
    }

    ngOnInit() {
        this.setErrorMessage("", "", "", false);
    }

    setRecordEditmode(mode: boolean) {
        this.setErrorMessage("", "", "", false);
        this.editControlService.setEditButtonClick(mode);
    }

    /*
    *  Save record (for the save button at top)
    */
    saveRecord() {
        this.setErrorMessage("", "", "", false);
        // Send save request to back end
        this.customizationService.saveRecord("").subscribe(
            (res) => {
                this.customizationService.removeUpdateDate();
                this.notificationService.showSuccessWithTimeout("Record saved.", "", 3000);
                this.setRecordEditmode(false);
                this.editControlService.setEditMode(false);
                this.customizationService.setRecordEdited(false);
                this.editControlService.reloadPdrPage();
                console.log("Record saved");
            },
            (err) => {
                this.setErrorMessage(
                    "There was an error while saving the record.",
                    err.message,
                    "Submit record",
                    true
                );
            }
        );
    }

    /*
     *  Cancel the whole edited record
     */
    cancelRecord() {
        this.setErrorMessage("", "", "", false);
        this.confirmationDialogService.confirm('Edited data will be lost', 'Do you want to erase changes?', true)
            .then((confirmed) => {
                if (confirmed) {
                    this.customizationService.delete().subscribe(
                        (res) => {
                            this.notificationService.showSuccessWithTimeout("All changes have been erased.", "", 3000);
                            this.editControlService.setEditMode(false);
                            console.log("Removing update date...");
                            this.customizationService.removeUpdateDate();
                            this.editControlService.reloadPdrPage();
                        },
                        (err) => {
                            this.setErrorMessage(
                                "There was an error deleting current changes.",
                                err.message,
                                "Cancel record",
                                true
                            );
                        }
                    );
                }
            })
            .catch(() => console.log('User dismissed the dialog (e.g., by using ESC, clicking the cross icon, or clicking outside the dialog)'));
    }

    setErrorMessage(message: string, messageDetail: string, action: string, display: boolean) {
        this.errorMessage = { message: message, messageDetail: messageDetail, action: action, display: display };
        this.errorHandlingService.setErrMessage(this.errorMessage);
    }
}
