import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';

import { ButtonModule } from 'primeng/button';

import { NerdmModule } from '../../nerdm/nerdm.module';
import { TitleModule } from '../title/title.module';
import { AuthorModule } from '../author/author.module';
import { ContactModule } from '../contact/contact.module';
import { VersionModule } from '../version/version.module';
import { DescriptionModule } from '../description/description.module';
import { TopicModule } from '../topic/topic.module';
import { KeywordModule } from '../keyword/keyword.module';
import { CollapseModule } from '../collapseDirective/collapse.module';
import { DataFilesModule } from '../data-files/data-files.module';
import { AboutdatasetModule } from '../aboutdataset/aboutdataset.module';
import { ResourceIdentityComponent } from './resourceidentity.component';
import { ResourceDescriptionComponent } from './resourcedescription.component';
import { ResourceDataComponent } from './resourcedata.component';
import { ResourceRefsComponent } from './resourcerefs.component';
import { ResourceMetadataComponent } from './resourcemetadata.component';
import { FacilitatorsModule } from '../facilitators/facilitators.module';
import { SearchresultModule } from '../searchresult/searchresult.module';
import { D3Service } from '../../shared/d3-service/d3.service';

/**
 * A module for components that lay out the content of a resource landing page into sections.
 * Each section is handled by a different component (<tt>resource*.component</tt>), and the 
 * <tt>LandingBody</tt> (<tt>../landingbody.component</tt>) brings the sections together into 
 * the body of the landing page.  
 * <p>
 * The section components are:
 * <dl>
 *   <dt> <tt>ResourceIdentityComponent</tt> </dt>
 *   <dd> "Front matter" that identifies the resource (by title and PID), its type, authors and 
 *        contact, and the primary literature article associated with the resource. </dd>
 * 
 *   <dt> <tt>ResourceDescriptionComponent</tt> </dt>
 *   <dd> Summarizing information about the resource, including the deescription/abstract, additional
 *        discussion, subject keywords and applicable research topics.  </dd>
 * 
 *   <dt> <tt>ResourceDataComponent</tt> </dt>
 *   <dd> Information and links for accessing the data associated with this resource.  </dd>
 * 
 *   <dt> <tt>ResourceRefsComponent</tt> </dt>
 *   <dd> The reference list  </dd>
 * 
 *   <dt> <tt>ResourceMetadataComponent</tt> </dt>
 *   <dd> Access and visualization of the resource metadata, including links for exporting the 
 *        metadata in various formats and schemas.</dd>
 * </dl>
 */
@NgModule({
    imports: [
        CommonModule,
        NerdmModule,
        TitleModule, AuthorModule, ContactModule, CollapseModule, VersionModule,
        DescriptionModule, DataFilesModule, TopicModule, KeywordModule, AboutdatasetModule, 
        FacilitatorsModule, SearchresultModule
    ],
    declarations: [
        ResourceIdentityComponent, ResourceDescriptionComponent, ResourceDataComponent,
        ResourceRefsComponent, ResourceMetadataComponent
    ],
    providers: [
        D3Service
    ],
    exports: [
        ResourceIdentityComponent, ResourceDescriptionComponent, ResourceDataComponent,
        ResourceRefsComponent, ResourceMetadataComponent
    ]
})
export class SectionsModule { }

export {
    ResourceIdentityComponent, ResourceDescriptionComponent, ResourceDataComponent,
    ResourceRefsComponent, ResourceMetadataComponent
};
    
