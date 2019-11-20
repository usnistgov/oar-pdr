import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LandingAboutComponent } from './landingAbout/landingAbout.component';
import { LandingComponent } from './landing/landing.component';
import { LandingPageComponent } from './landing/landingpage.component';
import { NoidComponent } from './landing/noid.component';
import { NerdmComponent } from './landing/nerdm.component';
// import { SearchResolve } from './landing/search-service.resolve';
import { NotFoundComponent, InternalErrorComponent } from './errors/errors.module';
import { DatacartComponent } from './datacart/datacart.component';

const routes: Routes = [
    { path: '', redirectTo: 'pdr/about', pathMatch: 'full' },

    // app paths
    { path: 'pdr/about',         component: LandingAboutComponent },
    { path: 'od/id',
      children: [
          { path: '',                component: NoidComponent          },
          { path: ':id',             component: LandingPageComponent   },
          { path: 'ark:/88434/:id',  component: LandingPageComponent   }
      ]
    },
    { path: 'nerdm',                 component: NerdmComponent         },
    { path: 'datacart/:mode',        component: DatacartComponent      },

    // error paths
    { path: 'not-found', 
      children: [
          { path: '',                component: NotFoundComponent      },
          { path: ':id',             component: NotFoundComponent      }
      ]
    },
    { path: 'int-error', 
      children: [
          { path: '',                component: InternalErrorComponent },
          { path: ':id',             component: InternalErrorComponent }
      ]
    },

    { path: '**',                    component: NotFoundComponent      }
];

@NgModule({
  imports: [RouterModule.forRoot(routes, { initialNavigation: 'enabled' })],
  exports: [RouterModule],
  // providers: [ SearchResolve ]
})
export class AppRoutingModule { }
