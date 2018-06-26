import { Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Router, NavigationEnd } from '@angular/router';
// import { FormBuilder, FormGroup } from '@angular/forms';

@Component({
  selector: 'landing-about',
  templateUrl: './landingAbout.component.html',
  styleUrls: ['./landingAbout.component.css']
})
export class LandingAboutComponent implements OnInit {
 
 headerText: string;

  constructor(private router: Router) {
    router.events.subscribe(s => {
      if (s instanceof NavigationEnd) {
        const tree = router.parseUrl(router.url);
        if (tree.fragment) {
          //alert("Test here:"+ tree.fragment);
          // you can use DomAdapter
          const element = document.querySelector("#" + tree.fragment);
          
          if (element) { 
            alert("Test here:"+element)
            element.scrollIntoView(true); 
           }
        }
      }
    });
  }

  ngOnInit() {
    //this.getTodos();
  }

  getTodos() {
    //this.todos = this._todoService.getTodosFromData();
  }
  goToTop(){ 	
   this.router.navigate(['about'],{fragment:'test'}); 
  }
  
}
