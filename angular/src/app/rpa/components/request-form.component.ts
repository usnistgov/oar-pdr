import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
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
import { Country } from '../models/country.model';
import { OverlayPanel } from 'primeng/overlaypanel';


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
  displayProgressSpinner = false;
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


  countries: Country[];
  selectedCountry: string;
  items: SelectItem[];
  item: string;

  domparser = new DOMParser();

  constructor(private route: ActivatedRoute, private messageService: MessageService, private configService: ConfigurationService, private rpaService: RPAService, private router: Router, private httpClient: HttpClient) { }

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      this.displayProgressSpinner = false;
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
    this.configService.getCountries().subscribe(data => {
      this.countries = data;
      console.log(this.countries);
    })
  }

  /**
   * Fetch dataset from config file using the dataset EDIID we extract from the url
   * @param ediid the dataset ID
   */
  getSelectedDataset(ediid: string): Observable<Dataset> {
    return this.getDatasets('config.yaml').pipe(
      map(datasets => datasets.find(dataset => dataset.ediid == ediid))
    );
  }

  /**
   * Choose the selectedDataset, and pick the appropriate form template from the config file
   * @param ediid the dataset ID
   */
  setSelecetedDataset(ediid: string) {
    this.configService.getDatasets('config.yaml').subscribe(datasets => {
      console.log("Datasets", datasets);
      this.selectedDataset = datasets.find(dataset => {
        return dataset.ediid === ediid;
      });
      console.log("selectedDataset= ", this.selectedDataset);
      this.configService.getFormTemplate(this.selectedDataset.formTemplate).subscribe(template => {
        this.selectedFormTemplate = template;
        console.log(template);
      })
    });
  }

  /**
   * Get the list of datasets from the config file
   * @param filename config file name
   */
  getDatasets(filename: string): Observable<Dataset[]> {
    return this.configService.getDatasets(filename);
  }


  /**
   * Get the appropriate form template for a specific dataset
   * @param dataset target dataset
   */
  getFormTemplate(dataset: Dataset) {
    this.configService.getFormTemplate(dataset.formTemplate).subscribe(template => {
      this.selectedFormTemplate = template;
      console.log("template", this.selectedDataset.formTemplate);
    });
  }

  /**
   * Submit the form to the request handler
   */
  submitForm() {
    console.log(this.requestForm.value);
    this.messageService.clear();
    this.displayProgressSpinner = true;
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
      requestFormData.country = this.requestForm.controls.country.value.name;
      requestFormData.receiveEmails = this.requestForm.controls.receiveEmails.value;

      let userInfo = this.makeUserInfo(requestFormData);
      // create a new record
      // make a call to the request handler in distribution service
      this.rpaService.createRecord(userInfo).subscribe((data: {}) => {
        // todo: messages - add a link to return to the landing page of the dataset
        // https://data.nist.gov/od/id/{ediid}
        this.displayProgressSpinner = false;
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Your request was submitted successfully! You will receive a confirmation email shortly.' });
        // this.router.navigate(['/rpa/request']);
      });

    }
  }

  /**
   * Helper method to create the userInfo that will be used as payload for creating a new record case in SF.
   */ 
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

  // onChangeDataset(event) {
  //   this.configService.getFormTemplate(this.selectedDataset.formTemplate).subscribe(template => {
  //     this.selectedFormTemplate = template;
  //     console.log("selectedDataset:", this.selectedDataset)
  //   });
  // }

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