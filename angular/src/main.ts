import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { AppBrowserModule } from './app/app.browser.module';
import {context} from './environments/environment';

document.addEventListener("DOMContentLoaded", () => {
  platformBrowserDynamic().bootstrapModule(AppBrowserModule)
                          .catch(err => console.error(err));
});
