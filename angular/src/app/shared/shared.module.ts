import { NgModule, ModuleWithProviders } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { SearchService } from './search-service/index';

import { ComboBoxComponent } from './combobox/combo-box.component';

/**
 * Do not specify providers for modules that might be imported by a lazy loaded module.
 */

@NgModule({
    imports: [
        CommonModule, RouterModule, FormsModule
    ],
    exports: [
        CommonModule, FormsModule, RouterModule,
        ComboBoxComponent
    ],
    declarations: [
        ComboBoxComponent
    ]
})
export class SharedModule {
  static forRoot(): ModuleWithProviders {
    return {
      ngModule: SharedModule,
      providers: [SearchService]
    };
  }
}

export { ComboBoxComponent };

