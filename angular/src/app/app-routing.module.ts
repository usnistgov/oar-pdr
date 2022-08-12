import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LandingAboutComponent } from './landingAbout/landingAbout.component';
import { LandingPageComponent } from './landing/landingpage.component';
import { NoidComponent } from './landing/noid.component';
import { NerdmComponent } from './landing/nerdm.component';
// import { SearchResolve } from './landing/search-service.resolve';
import { NotFoundComponent, InternalErrorComponent } from './errors/errors.module';
import { DatacartComponent } from './datacart/datacart.component';
import { DoneComponent } from './landing/done/done.component';
import { DatacartRoutes } from './datacart/datacart.routes';
import { MetricsComponent } from './metrics/metrics.component';

const routes: Routes = [
    ...DatacartRoutes,
    { path: '', redirectTo: '/about', pathMatch: 'full' },

    // app paths
    { path: 'about',         component: LandingAboutComponent },
    { path: 'lps',
      children: [
          { path: '',                component: NoidComponent          },
          { path: '**',              component: LandingPageComponent   }  // ** = id to display
      ]
    },
    { path: 'nerdm',                 component: NerdmComponent         },
    // If ediid='global', local normal cart. Otherwise, load the cart with key=ediid
    // { path: 'datacart/:ediid',        component: DatacartComponent      },
    { path: 'done',         component: DoneComponent },
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
    { path: 'metrics/:id',         component: MetricsComponent },
    { path: '**',                    component: NotFoundComponent      }
];

@NgModule({
  imports: [RouterModule.forRoot(routes, { initialNavigation: 'enabled', relativeLinkResolution: 'corrected' })],
  exports: [RouterModule],
  // providers: [ SearchResolve ]
})
export class AppRoutingModule { }
