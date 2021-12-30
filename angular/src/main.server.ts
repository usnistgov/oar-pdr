/***************************************************************************************************
 * Load `$localize` onto the global scope - used if i18n tags appear in Angular templates.
 */
import '@angular/localize/init';
import { enableProdMode } from '@angular/core';
export { AppServerModule } from './app/app.server.module';

enableProdMode();
export { renderModule, renderModuleFactory } from '@angular/platform-server';