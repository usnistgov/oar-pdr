import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SearchresultComponent } from './searchresult.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations'; 
import { FiltersComponent } from '../filters/filters.component';
import { ResultlistComponent } from '../resultlist/resultlist.component';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { AppConfig } from '../../config/config'
import { TransferState } from '@angular/platform-browser';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { SearchService } from '../../shared/search-service/index';
import { DropdownModule } from "primeng/dropdown";
import { TreeModule } from 'primeng/tree';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { FormsModule } from '@angular/forms';
import { testdata } from '../../../environments/environment';

describe('SearchresultComponent', () => {
    let component: SearchresultComponent;
    let fixture: ComponentFixture<SearchresultComponent>;
    let cfg : AppConfig;
    let plid : Object = "browser";
    let ts : TransferState = new TransferState();
    let nrd1 = testdata['test1'];

    beforeEach(async () => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";

        await TestBed.configureTestingModule({
        declarations: [ SearchresultComponent, FiltersComponent, ResultlistComponent ],
        imports: [
            BrowserAnimationsModule, 
            HttpClientTestingModule, 
            DropdownModule, 
            TreeModule, 
            AutoCompleteModule,
            FormsModule],
        providers: [
            { provide: AppConfig,       useValue: cfg },
            SearchService,
            TransferState]
        })
        .compileComponents();
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SearchresultComponent);
        component = fixture.componentInstance;
        component.record = nrd1;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('Should have title', () => {
        expect(fixture.nativeElement.querySelectorAll('#datasetlist-heading').length).toEqual(1);
        expect(fixture.nativeElement.querySelector('#datasetlist-heading').innerText)
            .toEqual('Datasets in this collection');
    });
});
