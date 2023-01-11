import { Component, OnInit } from '@angular/core';
import { AbstractControl, FormControl, FormGroup, ValidationErrors, Validators } from '@angular/forms'
import { MessageService } from 'primeng/api';

import { SelectItem } from 'primeng/api';
import { SelectItemGroup } from 'primeng/api';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { RPAService } from '../services/rpa.service';
import { ConfigurationService } from '../services/config.service';
import { Dataset } from '../models/dataset.model';
import { FormTemplate } from '../models/form-template.model';
import { UserInfo } from '../models/record.model';
import { RequestFormData } from '../models/form-data.model';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'rpd-request-form',
  templateUrl: './request-form.component.html',
  styleUrls: ['./request-form.component.css'],
  providers: [MessageService, ConfigurationService, RPAService]
})
export class RPARequestFormComponent implements OnInit {
  queryId: string = "<EMPTY_EDIID>";
  datasets: Dataset[] = [];
  selectedDataset: Dataset;
  selectedFormTemplate: FormTemplate;
  isFormValid = true;
  errors = [];
  requestForm = new FormGroup({
    fullName: new FormControl('', [Validators.required]),
    email: new FormControl('', [Validators.required, Validators.email]),
    phone: new FormControl(''),
    organization: new FormControl('', [Validators.required]),
    purposeOfUse: new FormControl('', [Validators.required]),
    address1: new FormControl('', [Validators.required]),
    address2: new FormControl('', [Validators.required]),
    address3: new FormControl(''),
    stateOrProvince: new FormControl(''),
    zipCode: new FormControl(''),
    country: new FormControl('', [Validators.required]),
    receiveEmails: new FormControl(false),
    termsAndConditionsAgreenement: new FormControl(false, [Validators.required]),
    disclaimerAgreenement: new FormControl(false, [Validators.required]),
    vettingAgreenement: new FormControl(false, [Validators.required]),
  });

  selectedCountry: string;
  countries: any = [];
  items: SelectItem[];
  item: string;

  domparser = new DOMParser();

  constructor(private route: ActivatedRoute, private messageService: MessageService, private configService: ConfigurationService, private rpaService: RPAService, private router: Router, private httpClient: HttpClient) { }

  ngOnInit() {
    // load list of datasets from the config file
    // this.getDatasets('config.yaml');
    this.route.queryParams.subscribe(params => {
      // this.setSelecetedDataset(params['ediid']);
      if (params['ediid']) {
        this.queryId = params['ediid']
        this.getSelectedDataset(this.queryId).subscribe(dataset => {
          this.selectedDataset = dataset;
          console.log("selectedDataset= ", this.selectedDataset);
          if (this.selectedDataset !== undefined) {
            this.configService.getFormTemplate(this.selectedDataset.formTemplate).subscribe(template => {
              this.selectedFormTemplate = template;
              console.log(template);
            });
          }
        });
      }

    });

    // load the countries list to use with dropdown menu, this list was provided by SF team
    this.httpClient.get("assets/countries.json").subscribe(data => {
      console.log(data);
      this.countries = data;
    })
  }

  getSelectedDataset(id: string): Observable<Dataset> {
    return this.getDatasets('config.yaml').pipe(
      map(datasets => datasets.find(dataset => dataset.ediid == id))
    );
  }

  setSelecetedDataset(ediid: string) {
    this.configService.getDatasets('config.yaml').subscribe(datasets => {
      console.log("Datasets", datasets);
      this.selectedDataset = datasets.find(dataset => {
        return dataset.ediid === ediid;
      });
      console.log("selectedDataset= ", this.selectedDataset);
      // this.selectedDataset = datasets[0];
      this.configService.getFormTemplate(this.selectedDataset.formTemplate).subscribe(template => {
        this.selectedFormTemplate = template;
        console.log(template);
      })
    });
  }

  // method to load datasets from local config file
  getDatasets(filename: string): Observable<Dataset[]> {
    return this.configService.getDatasets(filename);
  }


  // laod the specific form template for the selected dataset
  getFormTemplate() {
    this.configService.getFormTemplate(this.selectedDataset.formTemplate).subscribe(template => {
      this.selectedFormTemplate = template;
      console.log("template", this.selectedDataset);
    });
  }

  // function to be called when user clicks on the submit button
  submitForm() {
    console.log(this.requestForm.value);
    this.messageService.clear();
    if (!this.requestForm.valid) {
      this.isFormValid = false;
      this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Invalid form. Check if any required fields (*) are missing.' });
    } else {
      const requestFormData = {} as RequestFormData;
      requestFormData.fullName = this.requestForm.controls.fullName.value;
      requestFormData.email = this.requestForm.controls.email.value;
      requestFormData.phone = this.requestForm.controls.phone.value;
      requestFormData.organization = this.requestForm.controls.organization.value;
      requestFormData.purposeOfUse = this.requestForm.controls.purposeOfUse.value;
      requestFormData.address1 = this.requestForm.controls.address1.value;
      requestFormData.address2 = this.requestForm.controls.address2.value;
      requestFormData.address3 = this.requestForm.controls.address3.value;
      requestFormData.stateOrProvince = this.requestForm.controls.stateOrProvince.value;
      requestFormData.zipCode = this.requestForm.controls.zipCode.value;
      requestFormData.country = this.requestForm.controls.country.value;
      requestFormData.receiveEmails = this.requestForm.controls.receiveEmails.value;

      let userInfo = this.makeUserInfo(requestFormData);
      // create a new record
      // make a call to the request handler in distribution service
      this.rpaService.createRecord(userInfo).subscribe((data: {}) => {
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Your request was submitted successfully!' });
        this.router.navigate(['/rpa-request']);
      });

    }
  }

  // creates the userInfo that will be used as payload for creating a new record case in SF.
  // TODO: get subject/id from url param
  makeUserInfo(requestFormData: RequestFormData): UserInfo {
    let userInfo = {} as UserInfo;
    userInfo.fullName = requestFormData.fullName;
    userInfo.organization = requestFormData.organization;
    userInfo.email = requestFormData.email;
    userInfo.country = requestFormData.country;
    userInfo.receiveEmails = requestFormData.receiveEmails ? "True" : "False";
    userInfo.approvalStatus = "Pending";
    userInfo.productTitle = this.selectedDataset.name;
    userInfo.subject = "RPA: " + this.selectedDataset.ediid;
    userInfo.description = "Product Title:\n" + this.selectedDataset.name + "\n\n Purpose of Use: \n" + requestFormData.purposeOfUse;
    return userInfo;
  }

  onChangeDataset(event) {
    this.configService.getFormTemplate(this.selectedDataset.formTemplate).subscribe(template => {
      this.selectedFormTemplate = template;
      console.log("selectedDataset:", this.selectedDataset)
    });
  }


  getFormErrors(form: AbstractControl) {
    if (form instanceof FormControl) {
      // Return FormControl errors or null
      return form.errors ?? null;
    }
    if (form instanceof FormGroup) {
      const groupErrors = form.errors;
      // Form group can contain errors itself, in that case add'em
      const formErrors = groupErrors ? [groupErrors] : [];
      Object.keys(form.controls).forEach(key => {
        // Recursive call of the FormGroup fields
        const error = this.getFormErrors(form.get(key));
        if (error !== null) {
          // Only add error if not null
          formErrors.push({
            field: key,
            error: error
          });
        }
      });
      // Return FormGroup errors or null
      return Object.keys(formErrors).length > 0 ? formErrors : null;
    }
  }

}