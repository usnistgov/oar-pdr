import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MetricsComponent } from './metrics.component';
import { MetricsModule } from './metrics.module';
import { ActivatedRoute, Router, Routes } from '@angular/router';
import * as mock from '../testing/mock.services';
import { AppConfig } from '../config/config'
import { TransferState } from '@angular/platform-browser';
import { AngularEnvironmentConfigService } from '../config/config.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { DatePipe } from '@angular/common';
import { SearchService } from '../shared/search-service/search-service.service';

let fileLevelData = {
    "FilesMetricsCount": 3,
    "PageSize": 0,
    "FilesMetrics": [
        {
            "ediid": "3A1EE2F169DD3B8CE0531A570681DB5D1491",
            "filepath": "3A1EE2F169DD3B8CE0531A570681DB5D1491/1491_optSortSph20160701.m",
            "success_head": 0,
            "success_get": 103,
            "failure_head": 0,
            "failure_get": 0,
            "request_id": 0,
            "timestamp": "2021-02-06T22:46:07.000+0000",
            "download_size": 19121388,
            "number_users":1
        },
        {
            "ediid": "3A1EE2F169DD3B8CE0531A570681DB5D1491",
            "filepath": "3A1EE2F169DD3B8CE0531A570681DB5D1491/sub1/1491_optSortSphEvaluated20160701.cdf",
            "success_head": 0,
            "success_get": 73,
            "failure_head": 0,
            "failure_get": 0,
            "request_id": 0,
            "timestamp": "2021-02-06T22:46:07.000+0000",
            "download_size": 7616080,
            "number_users":1
        },
        {
            "ediid": "3A1EE2F169DD3B8CE0531A570681DB5D1491",
            "filepath": "3A1EE2F169DD3B8CE0531A570681DB5D1491/1491_optSortSphEvaluated20160701.cdf",
            "success_head": 0,
            "success_get": 206,
            "failure_head": 0,
            "failure_get": 0,
            "request_id": 0,
            "timestamp": "2021-02-06T22:46:07.000+0000",
            "download_size": 2558,
            "number_users":1
        },
        {
            "ediid": "3A1EE2F169DD3B8CE0531A570681DB5D1491",
            "filepath": "3A1EE2F169DD3B8CE0531A570681DB5D1491/sub2/1491_optSortSphEvaluated20160701.cdf",
            "success_head": 0,
            "success_get": 207,
            "failure_head": 0,
            "failure_get": 0,
            "request_id": 0,
            "timestamp": "2021-02-06T22:46:07.000+0000",
            "download_size": 2558,
            "number_users":1
        }
    ]
}

describe('MetricsComponent', () => {
    let component: MetricsComponent;
    let fixture: ComponentFixture<MetricsComponent>;
    let route : ActivatedRoute;
    let cfg : AppConfig;
    let plid : Object = "browser";
    let ts : TransferState = new TransferState();

    beforeEach(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";
        cfg.editEnabled = false;

        let path = "/metrics";
        let params = {};
        let id = "goober";

        path = path + "/" + id;
        params['id'] = id;

        let r : unknown = new mock.MockActivatedRoute(path, params);
        route = r as ActivatedRoute;

        TestBed.configureTestingModule({
            declarations: [  ],
            imports: [FormsModule, MetricsModule, HttpClientTestingModule],
            providers: [
                { provide: ActivatedRoute,  useValue: route },
                { provide: AppConfig,       useValue: cfg }, DatePipe, SearchService, TransferState
            ]
        })
        .compileComponents();

        fixture = TestBed.createComponent(MetricsComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('createChartData()', () => {
        component.fileLevelData = fileLevelData;
        component.createChartData();
        console.log('component.chartData', component.chartData);
        expect(component.chartData[0][0]).toEqual('1491_optSortSph20160701.m');
        expect(component.chartData[0][1]).toEqual(103);
        expect(component.chartData[1][0]).toEqual('sub1/1491_optSortSphEvaluated20160701.cdf');
        expect(component.chartData[1][1]).toEqual(73);
        expect(component.chartData[2][0]).toEqual('1491_optSortSphEvaluated20160701.cdf');
        expect(component.chartData[2][1]).toEqual(206);
        expect(component.chartData[3][0]).toEqual('sub2/1491_optSortSphEvaluated20160701.cdf');
        expect(component.chartData[3][1]).toEqual(207);
    });

    it('createTreeFromPaths()', () => {
        component.fileLevelData = fileLevelData;
        let tree = component.createTreeFromPaths(component.fileLevelData.FilesMetrics);
        console.log('tree[2]', tree[2]);
        expect(tree[0].data.name).toEqual('1491_optSortSph20160701.m');
        expect(tree[0].data.filePath).toEqual('1491_optSortSph20160701.m');
        expect(tree[0].data.isLeaf).toBeTruthy();

        expect(tree[1].data.name).toEqual('sub1');
        expect(tree[1].data.filePath).toEqual('1491_optSortSphEvaluated20160701.cdf');
        expect(tree[1].data.isLeaf).toBeFalsy();
        expect(tree[1].children[0].data.name).toEqual('1491_optSortSphEvaluated20160701.cdf');
        expect(tree[1].children[0].data.filePath).toEqual('1491_optSortSphEvaluated20160701.cdf');
        expect(tree[1].children[0].data.isLeaf).toBeTruthy();

        expect(tree[2].data.name).toEqual('1491_optSortSphEvaluated20160701.cdf');
        expect(tree[2].data.filePath).toEqual('1491_optSortSphEvaluated20160701.cdf');
        expect(tree[2].data.isLeaf).toBeTruthy();

        expect(tree[3].data.name).toEqual('sub2');
        expect(tree[3].data.filePath).toEqual('1491_optSortSphEvaluated20160701.cdf');
        expect(tree[3].data.isLeaf).toBeFalsy();
        expect(tree[3].children[0].data.name).toEqual('1491_optSortSphEvaluated20160701.cdf');
        expect(tree[3].children[0].data.filePath).toEqual('1491_optSortSphEvaluated20160701.cdf');
        expect(tree[3].children[0].data.isLeaf).toBeTruthy();
    });
});
