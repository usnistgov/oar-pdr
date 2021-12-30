import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchTopicsComponent } from './search-topics.component';
import { FormsModule } from '@angular/forms';
import { TreeModule } from 'primeng/tree';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { TreeNode } from 'primeng/api';
import { TestDataService } from '../../../shared/testdata-service/testDataService';
import { AppConfig } from '../../../config/config';
import { AngularEnvironmentConfigService } from '../../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { ToastrModule } from 'ngx-toastr';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { UserMessageService } from '../../../frame/usermessage.service';

describe('SearchTopicsComponent', () => {
    let component: SearchTopicsComponent;
    let fixture: ComponentFixture<SearchTopicsComponent>;
    let tempTopics: any;
    let taxonomyTree: TreeNode[] = [];
    let record: any;
    let compiled: any;
    let outputValue: any;
    let saveButton: any;
    let treeNodeLink: any;
    var tempTaxonomyTree = {};
    let cfg: AppConfig;
    let plid: Object = "browser";
    let ts: TransferState = new TransferState();

    beforeEach(async(() => {
      cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
      cfg.locations.pdrSearch = "https://goob.nist.gov/search";
      cfg.status = "Unit Testing";
      cfg.appVersion = "2.test";

        TestBed.configureTestingModule({
            declarations: [SearchTopicsComponent],
            imports: [FormsModule, TreeModule, HttpClientTestingModule, RouterTestingModule],
            schemas: [NO_ERRORS_SCHEMA],
            providers: [
                NgbActiveModal,
                UserMessageService,
                TestDataService,
                { provide: AppConfig, useValue: cfg }]
        })
            .compileComponents();
    }));

    beforeEach(() => {
        tempTopics = {"topic":["Bioscience: Genomic measurements"]};
        taxonomyTree = [];

        let newPart = null;
        newPart = {
            data: {
                treeId: "Test1",
                name: "Test1",
                researchTopic: "Test1",
                bkcolor: 'white'
            }, children: [],
            expanded: false
        };
        taxonomyTree.push(newPart);

        fixture = TestBed.createComponent(SearchTopicsComponent);
        component = fixture.componentInstance;
        component.field = 'topic';
        component.inputValue = tempTopics;

        saveButton = fixture.nativeElement.getElementsByTagName('button')[1];
        treeNodeLink = fixture.nativeElement.getElementsByTagName('span')[1];
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('saveTopic() should be called', () => {
        component.returnValue.subscribe((value) => {
            outputValue = value;
        });
        spyOn(component, 'saveTopic');
        saveButton.click();
        expect(component.saveTopic).toHaveBeenCalled();
    });

    it('First topic should be Bioscience: Genomic measurements', () => {
        component.returnValue.subscribe((value) => {
            console.log("value", value);
            outputValue = value;
        });

        saveButton.click();
        expect(outputValue.topic[0]).toEqual("Bioscience: Genomic measurements");
    });
});
