import { Routes } from '@angular/router';
import { RPARequestFormComponent } from './components/request-form.component';
import { RPASMEComponent } from './components/rpa-sme.component';

export const RPARoutes: Routes = [
  {
    path: 'rpa',
    children: [
        {   path: 'request',             
            component: RPARequestFormComponent},
        {   path: 'sme',  
            component: RPASMEComponent}
    ]
  }
];
