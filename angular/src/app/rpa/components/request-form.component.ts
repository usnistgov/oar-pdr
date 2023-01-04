import { Component, OnInit } from '@angular/core';
import { AbstractControl, FormControl, FormGroup, ValidationErrors, Validators } from '@angular/forms'
import { MessageService } from 'primeng/api';
import { ConfigurationService } from './services/config.service';
import { Dataset } from './models/dataset.model';
import { UserInfo } from './form-data.model';
import { FormTemplate } from './form-template.model';
import { RPDService } from './rpd.service';

import { SelectItem } from 'primeng/api';
import { SelectItemGroup } from 'primeng/api';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'rpd-request-form',
  templateUrl: './request-form.component.html',
  styleUrls: ['./request-form.component.css'],
  providers: [MessageService, ConfigurationService, RPDService]
})
export class RPDRequestFormComponent implements OnInit {
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

  constructor(private messageService: MessageService, private configService: ConfigurationService, private rpdService: RPDService, private router: Router, private httpClient: HttpClient) { }

  ngOnInit() {
    this.getDatasets('config.yaml');
    this.httpClient.get("assets/countries.json").subscribe(data =>{
      console.log(data);
      this.countries = data;
    })
  }

  getDatasets(filename: string) {
    this.configService.getDatasets(filename).subscribe(datasets => {
      console.log("Datasets", datasets);
      this.datasets = datasets;
      this.selectedDataset = datasets[0];
      this.configService.getFormTemplate(this.selectedDataset.formTemplate).subscribe(template => {
        this.selectedFormTemplate = template;
        console.log(template);
      })
    });
  }

  getFormTemplate() {
    this.configService.getFormTemplate(this.selectedDataset.formTemplate).subscribe(template => {
      this.selectedFormTemplate = template;
      console.log("template", this.selectedDataset);
    });
  }

  submitForm() {
    console.log(this.requestForm.value);
    this.messageService.clear();
    if (!this.requestForm.valid) {
      this.isFormValid = false;
      this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Invalid form. Check if any required fields (*) are missing.' });
    } else {
      const userInfo = {} as UserInfo;
      userInfo.fullName = this.requestForm.controls.fullName.value;
      // userInfo.lastname = this.requestForm.controls.lastname.value;
      userInfo.email = this.requestForm.controls.email.value;
      userInfo.phone = this.requestForm.controls.phone.value;
      userInfo.organization = this.requestForm.controls.organization.value;
      userInfo.purposeOfUse = this.requestForm.controls.purposeOfUse.value;
      userInfo.address1 = this.requestForm.controls.address1.value;
      userInfo.address2 = this.requestForm.controls.address2.value;
      userInfo.address3 = this.requestForm.controls.address3.value;
      userInfo.stateOrProvince = this.requestForm.controls.stateOrProvince.value;
      userInfo.zipCode = this.requestForm.controls.zipCode.value;
      userInfo.country = this.requestForm.controls.country.value;
      userInfo.receiveEmails = this.requestForm.controls.receiveEmails.value;
      this.rpdService.createRecord(userInfo).subscribe((data: {}) => {
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Your request was submitted successfully!' });
        this.router.navigate(['/rpd-request']);
      });

    }
  }

  onChangeDataset(event) {
    this.configService.getFormTemplate(this.selectedDataset.formTemplate).subscribe(template => {
      this.selectedFormTemplate = template;
      console.log("disclaimers", this.selectedFormTemplate.disclaimers)
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