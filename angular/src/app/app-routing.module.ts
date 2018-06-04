import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

//import { AboutComponent }   from './about/About.component';
import { LandingAboutComponent } from './landingAbout/landingAbout.component';
import { LandingComponent } from './landing/landing.component';
import { NoidComponent } from './landing/noid.component';
import { NerdmComponent } from './landing/nerdm.component';
import { SearchResolve } from './landing/search-service.resolve';
import { ErrorComponent, UserErrorComponent } from './landing/error.component';
import { DatacartComponent} from './datacart/datacart.component';

const routes: Routes = [
  { path: '', redirectTo: '/aboutlanding', pathMatch: 'full' },
  { path: 'aboutlanding', component: LandingAboutComponent },
 {path: 'id/:id',
   children: [
   {
     path: '',
     component: LandingComponent,
     resolve: {
       searchService: SearchResolve
     }
   }
 ]}, {
  path: 'id/ark:/88434/:id',
  children: [
    {
      path: '',
      component: LandingComponent,
      resolve: {
        searchService: SearchResolve
      }
    }
  ]
},{
  path: 'id',
  children: [
    {
      path: '',
      component: NoidComponent,
      
    }
  ]
}
,{
  path: 'nerdm',
  children: [
    {
      path: '',
      component: NerdmComponent
    }
  ]
},{
  path: 'datacart',
  children: [
      {
        path: '',
        component: DatacartComponent
      }
  ]
},{
  path: 'error/:id',
  children: [
    {
      path: '',
      component: ErrorComponent
    }
  ]
}
,{
  path: 'usererror/:id',
  children: [
    {
      path: '',
      component: UserErrorComponent
    }
  ]
}
];

@NgModule({
  imports: [ RouterModule.forRoot(routes) ],
  exports: [ RouterModule ],
  providers: [ SearchResolve]
})
export class AppRoutingModule {}
