import { Component, OnInit } from '@angular/core';
import { AuthService } from '../shared/auth-service/auth.service'
import { CommonVarService } from '../shared/common-var';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import {ButtonModule} from 'primeng/button';

@Component({
  selector: 'app-login',
  templateUrl: 'login.component.html',
  styles: []
})
export class LoginComponent implements OnInit {
  
  isAuthenticated:boolean = false;
  ediid: any;

  constructor(private authService: AuthService,
              private router: Router,
              private _location: Location,
              private commonVarService: CommonVarService) { }

  ngOnInit() {
    this.ediid = this.commonVarService.getEdiid();

    this.authService.watchAuthenticateStatus().subscribe(
      value => {
          this.isAuthenticated = value;
      }
    );
  }

  login(){
    this.authService.setAuthenticateStatus(true);
    this.router.navigate(['/od/id/', this.ediid],{fragment:''});
  }

  cancel(){
    this._location.back();
  }
}
