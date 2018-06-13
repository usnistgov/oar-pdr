import {Component, OnInit, OnDestroy, AfterViewInit, ElementRef, ViewChildren, Input} from '@angular/core';
//import {Headers, RequestOptions, Response, ResponseContentType, URLSearchParams} from '@angular/common/http';
import { HttpClientModule, HttpClient, HttpParams } from '@angular/common/http';
import { Http, HttpModule } from '@angular/http';
import 'rxjs/add/operator/map';
import { Subscription } from 'rxjs/Subscription';
import { Message } from 'primeng/components/common/api';
import { TreeTableModule,TreeNode, MenuItem,OverlayPanelModule,
  FieldsetModule,PanelModule,ContextMenuModule,
  MenuModule } from 'primeng/primeng';
import { CartService } from './cart.service';
import { CartEntity } from './cart.entity';
import { Observable } from 'rxjs/Observable';
import {ProgressSpinnerModule, DialogModule} from 'primeng/primeng';
import * as _ from 'lodash';
import * as __ from 'underscore';
import { environment } from '../../environments/environment';


declare var Ultima: any;
declare var saveAs: any;
declare var $: any;

@Component ({
  moduleId: module.id,
  selector: 'data-cart',
  templateUrl: 'datacart.component.html',
  styleUrls: ['datacart.component.css'],
})

export class DatacartComponent implements OnInit, OnDestroy {
  layoutCompact: boolean = true;
  layoutMode: string = 'horizontal';
  profileMode: string = 'inline';
  msgs: Message[] = [];
  exception: string;
  errorMsg: string;
  status: string;
  errorMessage: string;
  errorMessageArray: string[];
  //searchResults: any[] = [];
  searchValue: string;
  recordDisplay: any[] = [];
  keyword: string;
  downloadZIPURL: string;
  summaryCandidate: any[];
  showSpinner: boolean = false;
  findId: string;
  leftmenu: MenuItem[];
  rightmenu: MenuItem[];
  similarResources: boolean = false;
  similarResourcesResults: any[] = [];
  qcriteria: string = '';
  selectedFile: TreeNode;
  isDOI = false;
  isEmail = false;
  citeString: string = '';
  type: string = '';
  process: any[];
  requestedId: string = '';
  isCopied: boolean = false;
  distdownload: string = '';
  serviceApi: string = '';
  metadata: boolean = false;
  cartEntities: CartEntity[];
  cols: any[];
  selectedData: TreeNode[] = [];
  dataFiles: TreeNode[] = [];
  childNode: TreeNode = {};
  display: boolean = true;
  minimum: number = 1;
  maximum: number = 100000;
  displayFiles:any = [];
  index:any = {};
  selectedNode: TreeNode[] = [];
  selectedFileCount: number = 0;
  private distApi : string = environment.DISTAPI;
  //private distApi:string = "http://localhost:8083/oar-dist-service";


  /**
   * Creates an instance of the SearchPanel
   *
   */
  constructor(private http: HttpClient, private cartService: CartService) {
    this.getDataCartList();
    this.display = true;

  }

  /**
   * If Search is successful populate list of keywords themes and authors
   */

  getDataCartList() {
    this.cartService.getAllCartEntities().then(function (result) {
      //console.log("result" + result.length);
      this.cartEntities = result;
      console.log("cart entities inside datacartlist" + JSON.stringify(this.cartEntities));
    }.bind(this), function (err) {
      alert("something went wrong while fetching the products");
    });
  }

  downloadZIP() {
    let downloadURL: string[];
    let fileName: string[];
    let params = new HttpParams();
    let folderName: string;
    this.showSpinner = true;
    for (let selData of this.selectedData) {
      if (selData.data['filePath'] != null) {
        if (selData.data['filePath'].split(".").length > 1) {
          console.log("resId" + selData.data['resId']);
          console.log("filepath" + selData.data['filePath'])
          //folderName = selData.data['resId'].split("/")[2] + "-" + selData.data['resTitle'].substring(0, 20);
          params = params.append('folderName', folderName);
          params = params.append('downloadURL', selData.data['downloadURL']);
          params = params.append('fileName', selData.data['id'] + selData.data['fileName']);
          params = params.append('filePath', selData.data['filePath']);
          params = params.append('resFilePath', selData.data['resFilePath']);
          this.cartService.updateCartItemDownloadStatus(selData.data['id'],true);
        }
      }
    }
      var randomnumber = Math.floor(Math.random() * (this.maximum - this.minimum + 1)) + this.minimum;

      var downloadFileName = "download" + randomnumber + ".zip";
      this["showDownloadFileSpinner"+randomnumber] = true;
      this.displayFiles.push({key: downloadFileName, value: this["showDownloadFileSpinner"+randomnumber]});
      this.downloadFile(params).subscribe(blob => {
          saveAs(blob, downloadFileName);
          this.showSpinner = false;
          this["showDownloadFileSpinner"+randomnumber] = false;
          this.displayFiles.forEach(function(item) {
              if (item.key === downloadFileName) {
                  item.value = this["showDownloadFileSpinner"+randomnumber];
              }
          },1000);
      });

      for (let selData of this.selectedData) {
          if (selData.data['filePath'] != null) {
              if (selData.data['filePath'].split(".").length > 1) {
                  console.log("resId" + selData.data['resId']);
                  console.log("filepath" + selData.data['filePath'])
                  this.cartService.updateCartItemDownloadStatus(selData.data['id'],'downloaded');
              }
          }
      }

      this.cartService.getAllCartEntities().then(function (result) {
          //console.log("result" + result.length);

          this.cartEntities = result;
          console.log("hello" + JSON.stringify(this.cartEntities));
          this.createDataCartHierarchy();
          this.dataFiles[0].expanded = true;
      }.bind(this), function (err) {
          alert("something went wrong while fetching the products");
      });

      this.selectedData.length = 0;

  }

  dataFileCount() {
      this.selectedFileCount = 0;
      console.log("selected data length" + this.selectedData.length)
      for (let selData of this.selectedData) {
          if (selData.data['filePath'] != null) {
              if (selData.data['filePath'].split(".").length > 1) {
                  this.selectedFileCount++;
              }
          }
      }
  }

  updateCartEntries(row:any,downloadedStatus:any) {
        console.log("id" + JSON.stringify(row.data));
        this.cartService.updateCartItemDownloadStatus(row.data['id'],downloadedStatus);
        this.cartService.getAllCartEntities().then(function (result) {
            //console.log("result" + result.length);
            this.cartEntities = result;
                this.createDataCartHierarchy();

        }.bind(this), function (err) {
            alert("something went wrong while fetching the products");
        });

    }

  showLoadingSpinner() {
    this.showSpinner = true;
  }

  hideLoadingSpinner() {
    this.showSpinner = false;
  }

  downloadFile(params): Observable<Blob> {
    //let options = new RequestOptions({responseType: ResponseContentType.Blob});
    return this.http.get(this.distApi + "/cart?" , {responseType: 'blob', params: params});
  }

    /**
     * Removes all cartInstances that are bound to the productId given.
     **/
    removeByDataId() {

        let dataId: any;
        // convert the map to an array
        for (let selData of this.selectedData) {
            dataId = selData.data['id'];
            // Filter out all cartEntities with given productId,  finally the new stuff from es6 can be used.
            this.cartEntities = this.cartEntities.filter(entry => entry.data.id != dataId);

            //save to localStorage
            this.cartService.saveListOfCartEntities(this.cartEntities);
        }

        this.getDataCartList();
        this.createDataCartHierarchy();
        console.log("selected node remove" + JSON.stringify(this.selectedNode) );
        this.dataFiles[0].expanded = true;
        this.cartService.setCartLength(this.dataFiles.length);
        this.selectedData.length = 0;
    }

    /**
     * Removes all cartInstances that are bound to the productId given.
     **/
    removeByDownloadStatus() {

        let dataId: any;
        // convert the map to an array
        this.cartService.removeDownloadStatus();
        this.cartService.getAllCartEntities().then(function (result) {
            //console.log("result" + result.length);
            this.cartEntities = result;
            console.log("cart entities inside datacartlist" + JSON.stringify(this.cartEntities));
            this.createDataCartHierarchy();
            console.log("selectednode" + this.selectedNode);
            this.dataFiles[0].expanded = true;
        }.bind(this), function (err) {
            alert("something went wrong while fetching the products");
        });
        this.cartService.setCartLength(this.dataFiles.length);
    }

  /**
   * Removes all cartInstances that are bound to the productId given.
   **/
  clearDownloadStatus() {

    let dataId: any;
    // convert the map to an array
    this.cartService.updateCartDownloadStatus(false);
    this.cartService.getAllCartEntities().then(function (result) {
      //console.log("result" + result.length);
      this.cartEntities = result;
      console.log("cart entities inside datacartlist" + JSON.stringify(this.cartEntities));
      this.createDataCartHierarchy();
    }.bind(this), function (err) {
      alert("something went wrong while fetching the products");
    });
    this.cartService.setCartLength(this.dataFiles.length);
  }
  /**
   * Removes all cartInstances that are bound to the productId given.
   **/
  removeItem(row:any) {

    let dataId: any;
    // convert the map to an array
    let delRow = this.cartEntities.indexOf(row);
    this.cartEntities.splice(delRow,1);
    this.cartService.saveListOfCartEntities(this.cartEntities);
    this.getDataCartList();
    this.createDataCartHierarchy();
    //console.log("datafiles" + this.dataFiles.length);

  }

  /**
   * Get the params OnInit
   */
  ngOnInit() {
    console.log("test" + this.cartEntities.length);
    this.createDataCartHierarchy();
    this.display = true;
  }


  ngOnDestroy() {
  }

  createDataCartHierarchy() {

        console.log("cart ent" + JSON.stringify(this.cartEntities));

        let arrayList = this.cartEntities.reduce(function (result, current) {
            result[current.data.resTitle] = result[current.data.resTitle] || [];
            result[current.data.resTitle].push(current);
            return result;
        }, {});
        //console.log("list" + JSON.stringify(arrayList));
        this.dataFiles = [];
        //let arrayList = this.cartEntities;
        //console.log("arraylist" + JSON.stringify(arrayList));
        let parentObj: TreeNode = {};
        for (var key in arrayList) {
            let resId = key;
            if (arrayList.hasOwnProperty(key)) {
                parentObj = {
                    data: {
                        'resTitle': key,
                    }
                };
                parentObj.children = [];
                for (let fields of arrayList[key]) {
                    //console.log("file path" + fields.data.filePath);
                    let fpath = fields.data.filePath.split("/");
                    if (fpath.length > 0) {
                        let child2: TreeNode = {};
                        child2.children = [];
                        let parent = parentObj;
                        let folderExists:boolean = false;
                        let folder = null;
                        for (let path in fpath) {
                            //let array = JSON.stringify(parent);
                            //console.log("path" + fpath[path]);
                            child2 = this.createDataCartChildrenTree(fpath[path],fields.data.id,resId,key,fields.data.downloadURL,fields.data.filePath,fields.data.downloadedStatus);
                            parent.children.push(child2);
                            parent = child2;
                        }
                    }
                }

                console.log("final output" + JSON.stringify(parentObj));

                /*
                let tmp:any ={};
                parentObj.children.forEach((o) => {
                  const path = o.data.filePath;
                  if (tmp[path]) {
                    tmp[path].children = tmp[path].children || [];// in case no children property or array exists
                    tmp[path].children.push(...o.children);
                  } else {
                    tmp[path] = o;
                  }

                });

        */

                //this.walkData(parentObj[0], parentObj,0);

                //let values = Object.keys(tmp).map(key => tmp[key]);
                //parentObj.children = values;
                this.walkData(parentObj, parentObj, 0);
                //parentObj = tmp;
                this.dataFiles.push(parentObj);
                this.index = {};
                //this.dataFiles.push(parentObj);
            }
        }
    }

    walkData(inputArray, parent, level){
        level = level || '';
        if (inputArray.children) {
            let copy = inputArray.children.filter((item) => { return true});
            copy.forEach((item) => {
                var path = inputArray.data && inputArray.data.filePath ?
                    inputArray.data.filePath : 'root';
                this.walkData(item, inputArray, level + '/' + path);
            });
        }
        if(inputArray.data && inputArray.data.filePath) {
            var key = level + inputArray.data.filePath;
            if (!(key in this.index)) {
                this.index[key] = inputArray;
            } else {
                //debugger;
                inputArray.children.forEach((item) => {
                    this.index[key].children.push(item);
                })
                var indx = 0;
                var found = false;
                parent.children.forEach((item) => {
                    if (!found &&
                        item.data.filePath === inputArray.data.filePath &&
                        item.data.id === inputArray.data.id
                    ){
                        found = true;
                    }
                    else if(!found) {
                        indx++;
                    }
                });
                parent.children.splice(indx, 1);
            }
        }
    }

    createDataCartChildrenTree(path: string,id:string,resId:string,resTitle:string,downloadURL:string,resFilePath:string,downloadedStatus:string){
        let child1:TreeNode = {};
        child1 = {
            data: {
                'filePath': path,
                'id' : id,
                'resId' : resId,
                'resTitle': path,
                'downloadURL' : downloadURL,
                'resFilePath' : resFilePath,
                'downloadedStatus' : downloadedStatus
            }
        };
        child1.children = [];
        return child1;
    }
}
