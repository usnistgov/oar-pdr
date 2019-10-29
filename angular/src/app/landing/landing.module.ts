import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SharedModule } from '../shared/shared.module';
import { TreeModule, FieldsetModule, DialogModule, OverlayPanelModule,
         ConfirmDialogModule, MenuModule } from 'primeng/primeng';
import { TreeTableModule } from 'primeng/treetable';
import { EditControlBarModule } from './edit-control-bar/edit-control-bar.module';

import { LandingComponent } from './landing.component';
import { DataFilesComponent } from './data-files/data-files.component';
import { TitleComponent } from './title/title.component';
import { AuthorComponent } from './author/author.component';
import { ContactComponent } from './contact/contact.component';
import { DescriptionComponent } from './description/description.component';
import { TopicComponent } from './topic/topic.component';
import { KeywordComponent } from './keyword/keyword.component';
import { MetadataComponent } from './metadata/metadata.component';
import { Collaspe } from './collapseDirective/collapse.directive';
import { NoidComponent } from './noid.component';
import { NerdmComponent } from './nerdm.component';
import { KeyValuePipe } from './keyvalue.pipe';
import { MetadataView } from './metadata/metadataview.component';

@NgModule({
  declarations: [
    LandingComponent,DataFilesComponent,TitleComponent,AuthorComponent,ContactComponent,
    DescriptionComponent, TopicComponent, KeywordComponent,
    MetadataComponent, Collaspe,
    NoidComponent, NerdmComponent,KeyValuePipe,MetadataView
  ],
  imports: [
    CommonModule,SharedModule,TreeModule,FieldsetModule, DialogModule, OverlayPanelModule,
    ConfirmDialogModule, MenuModule,TreeTableModule, EditControlBarModule
  ],
  exports:[
    LandingComponent, DataFilesComponent, TitleComponent, AuthorComponent, ContactComponent,
    DescriptionComponent, TopicComponent, KeywordComponent, MetadataComponent,
    Collaspe, NoidComponent, NerdmComponent,KeyValuePipe,MetadataView
  ]
})
export class LandingModule { }
