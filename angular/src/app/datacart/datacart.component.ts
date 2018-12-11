import {Component, OnInit, OnDestroy, AfterViewInit, ElementRef, ViewChildren, Input} from '@angular/core';
//import {Headers, RequestOptions, Response, ResponseContentType, URLSearchParams} from '@angular/common/http';
import { HttpClientModule, HttpClient, HttpParams, HttpRequest, HttpEventType } from '@angular/common/http';
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
import { DownloadData } from './downloadData';
import { CommonVarService } from '../shared/common-var'
import { DownloadService } from '../shared/download-service/download-service.service';

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
  selectedParentIndex:number = 0;
  ediid:any;
  downloadInstance: any;
  downloadStatus: any;
  downloadProgress: any;
  displayDownloadFile: boolean = true;

  private distApi : string = environment.DISTAPI;
  //private distApi:string = "http://localhost:8083/oar-dist-service";


  /**
   * Creates an instance of the SearchPanel
   *
   */
  constructor(private http: HttpClient, 
    private cartService: CartService,
    private downloadService: DownloadService,
    private commonVarService:CommonVarService) {
    this.getDataCartList();
    this.display = true;
    // console.log("this.cartEntities:");
    // console.log(this.cartEntities); 
  }

  /**
   * Get the params OnInit
   */
  ngOnInit() {
    this.ediid = this.commonVarService.getEdiid();
    this.createDataCartHierarchy();
    this.display = true;
      if (this.cartEntities.length > 0) {
         // var element = <HTMLInputElement> document.getElementById("downloadStatus");
         // element.disabled = false;
      } else {
          //var element = <HTMLInputElement> document.getElementById("downloadStatus");
          //element.disabled = true;
      }
  }


  ngOnDestroy() {
  }

  /**
   * If Search is successful populate list of keywords themes and authors
   */

  getDataCartList() {
    this.cartService.getAllCartEntities().then(function (result) {
      this.cartEntities = result;
      console.log("this.cartEntities:");
      console.log(this.cartEntities);
      
    //   console.log("cart entities inside datacartlist" + JSON.stringify(this.cartEntities));
    }.bind(this), function (err) {
      alert("something went wrong while fetching the products");
    });
  }

  /**
   *  download zip file
   */
  downloadZIP() {
    let downloadURL: string[];
    let fileName: string[];
    let params = new HttpParams();
    let folderName: string;
    this.showSpinner = true;
    let downloadData: DownloadData[] = [];
    let existItem: any;
    var i:number;
    for ( i=0; i < this.dataFiles.length;i++) {
        if (this.dataFiles[i].expanded == true) {
            this.selectedParentIndex = i;
        }
    }

    for (let selData of this.selectedData) {
        if (selData.data['resFilePath'] != null && selData.data['resFilePath'] != undefined) {
            if (selData.data['resFilePath'].split(".").length > 1) {
                existItem = downloadData.filter(item => item.filePath === this.ediid+selData.data['resFilePath'] 
                    && item.downloadUrl === selData.data['downloadURL']);

                if (existItem.length == 0) {
                    downloadData.push({"filePath":this.ediid+selData.data['resFilePath'], 'downloadUrl':selData.data['downloadURL']});
                }
            }
        }
    }

    // for (let selData of this.selectedData) {
    //   if (selData.data['filePath'] != null) {
    //     if (selData.data['filePath'].split(".").length > 1) {
    //       //folderName = selData.data['resId'].split("/")[2] + "-" + selData.data['resTitle'].substring(0, 20);
    //       params = params.append('folderName', folderName);
    //       params = params.append('downloadURL', selData.data['downloadURL']);
    //       params = params.append('fileName', selData.data['resId'] + selData.data['fileName']);
    //       params = params.append('filePath', selData.data['filePath']);
    //       params = params.append('resFilePath', selData.data['resFilePath']);
    //       this.cartService.updateCartItemDownloadStatus(selData.data['resId'],true);
    //     }
    //   }
    // }


    // if(params.keys.length !== 0){
    var randomnumber = Math.floor(Math.random() * (this.maximum - this.minimum + 1)) + this.minimum;

    var downloadFileName = "download" + randomnumber + ".zip";
    this["showDownloadFileSpinner"+randomnumber] = true;
    this.displayFiles.push({key: downloadFileName, value: this["showDownloadFileSpinner"+randomnumber]});

    const req = new HttpRequest('GET', 'https://s3.amazonaws.com/nist-midas/1858/RawCameraData.zip', {
    reportProgress: true, responseType: 'blob'
    });

    this.downloadStatus = 'downloading';
    this.downloadInstance = this.http.request(req).subscribe(event => {
        switch (event.type) {
            case HttpEventType.Response:
                this.downloadStatus = 'downloaded';
                this.downloadProgress = 0;
                this.downloadService.saveToFileSystem(event.body, downloadFileName);
                this.showSpinner = false;
                this["showDownloadFileSpinner"+randomnumber] = false;
                this.displayFiles.forEach(function(item) {
                    if (item.key === downloadFileName) {
                        item.value = this["showDownloadFileSpinner"+randomnumber];
                    }
                },1000);

                for (let selData of this.selectedData) {
                    if (selData.data['filePath'] != null) {
                        //   if (selData.data['filePath'].split(".").length > 1) {
                        if (selData.data.children == undefined) {
                              this.cartService.updateCartItemDownloadStatus(selData.data['resId'],'downloaded');
                        }
                      }
                  }
            
                  this.cartService.getAllCartEntities().then(function (result) {
                      this.cartEntities = result;
                      this.createDataCartHierarchy();
                      if (this.cartEntities.length > 0) {
                          this.dataFiles[this.selectedParentIndex].expanded = true;
                      }
                  }.bind(this), function (err) {
                      alert("something went wrong while creating the zip file");
                  });
            
                  this.selectedData.length = 0;
                  this.dataFileCount();

                break;
            case HttpEventType.DownloadProgress:
                this.downloadProgress = Math.round(100*event.loaded / event.total);
                break;
        }
    });
    //   this.downloadService.postFile(this.distApi + "downloadall", JSON.stringify(downloadData)).subscribe(blob => {
    //     this.downloadService.saveToFileSystem(blob, downloadFileName);
    //       this.showSpinner = false;
    //       this["showDownloadFileSpinner"+randomnumber] = false;
    //       this.displayFiles.forEach(function(item) {
    //           if (item.key === downloadFileName) {
    //               item.value = this["showDownloadFileSpinner"+randomnumber];
    //           }
    //       },1000);
    //   });

    //   for (let selData of this.selectedData) {
    //     if (selData.data['filePath'] != null) {
    //         //   if (selData.data['filePath'].split(".").length > 1) {
    //         if (selData.data.children == undefined) {
    //               this.cartService.updateCartItemDownloadStatus(selData.data['resId'],'downloaded');
    //         }
    //       }
    //   }

    //   this.cartService.getAllCartEntities().then(function (result) {
    //       this.cartEntities = result;
    //       this.createDataCartHierarchy();
    //       if (this.cartEntities.length > 0) {
    //           this.dataFiles[this.selectedParentIndex].expanded = true;
    //       }
    //   }.bind(this), function (err) {
    //       alert("something went wrong while creating the zip file");
    //   });

    //   this.selectedData.length = 0;
    //   this.dataFileCount();
    // }
  }

  cancelDownload(key){
    this.downloadInstance.unsubscribe();
    this.downloadInstance = null;
    this.downloadProgress = 0;
    this.downloadStatus = null;
    this.showSpinner = false;
    this.displayFiles = this.displayFiles.filter(obj => obj.key != key);
}

  /**
   * count the selected files
   */

  dataFileCount() {
      this.selectedFileCount = 0;
      for (let selData of this.selectedData) {
          if (selData.data['filePath'] != null) {
              if (selData.data['filePath'].split(".").length > 1) {
                  this.selectedFileCount++;
              }
          }
      }

      if (this.selectedFileCount > 0) {
         // var element = <HTMLInputElement> document.getElementById("download");
         // element.disabled = false;
         // element = <HTMLInputElement> document.getElementById("removeData");
         // element.disabled = false;
      } else {
          //var element = <HTMLInputElement> document.getElementById("download");
          //element.disabled = true;
          //element = <HTMLInputElement> document.getElementById("removeData");
          //element.disabled = true;
      }

  }

  /**
   * Update cart entries
   */
  updateCartEntries(row:any,downloadedStatus:any) {
        // console.log("id" + JSON.stringify(row.data));
        this.cartService.updateCartItemDownloadStatus(row.data['resId'],downloadedStatus);
        this.cartService.getAllCartEntities().then(function (result) {
            this.cartEntities = result;
                this.createDataCartHierarchy();

        }.bind(this), function (err) {
            alert("something went wrong while fetching the products");
        });

    }

  /**
   * display spinner
   */
  showLoadingSpinner() {
    this.showSpinner = true;
  }

  /**
   * hide spinner
   */
  hideLoadingSpinner() {
    this.showSpinner = false;
  }

  /**
   * Removes all cart Instances that are bound to the given id.
   **/
  removeByDataId() {

      let dataId: any;
      // convert the map to an array
      var i:number;
      for ( i=0; i < this.dataFiles.length;i++) {
          if (this.dataFiles[i].expanded == true) {
              this.selectedParentIndex = i;
          }
      }
      for (let selData of this.selectedData) {
          dataId = selData.data['resId'];
          // Filter out all cartEntities with given productId,  finally the new stuff from es6 can be used.
          this.cartEntities = this.cartEntities.filter(entry => entry.data.resId != dataId);
            //save to localStorage
          this.cartService.saveListOfCartEntities(this.cartEntities);
      }
      this.getDataCartList();
      this.createDataCartHierarchy();

      if (this.cartEntities.length > 0) {
          this.dataFiles[this.selectedParentIndex].expanded = true;
      }

      this.cartService.setCartLength(this.cartEntities.length);
      this.selectedData.length = 0;
      this.dataFileCount();

  }

  /**
   * Removes all cart Instances that are bound to the download status.
   **/
  removeByDownloadStatus() {

      let dataId: any;
      // convert the map to an array
      var i:number;
      for ( i=0; i < this.dataFiles.length;i++) {
          if (this.dataFiles[i].expanded == true) {
              this.selectedParentIndex = i;
          }
      }
      this.cartService.removeDownloadStatus();
      this.cartService.getAllCartEntities().then(function (result) {
          this.cartEntities = result;
          this.createDataCartHierarchy();
          if (this.cartEntities.length > 0) {
              this.dataFiles[this.selectedParentIndex].expanded = true;
          }
          this.cartService.setCartLength(this.cartEntities.length);
        }.bind(this), function (err) {
            alert("something went wrong while removing item");
        });
    }

  /**
   * clears the item download status
   **/
  clearDownloadStatus() {

    let dataId: any;
    // convert the map to an array
    this.cartService.updateCartDownloadStatus(false);
    this.cartService.getAllCartEntities().then(function (result) {
      //console.log("result" + result.length);
      this.cartEntities = result;
    //   console.log("cart entities inside datacartlist" + JSON.stringify(this.cartEntities));
      this.createDataCartHierarchy();
    }.bind(this), function (err) {
      alert("something went wrong while fetching the products");
    });
    this.cartService.setCartLength(this.dataFiles.length);
  }

  /**
   * Removes all cart Instances that are bound to the given id.
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
   * Create Data hierarchy for the tree
   */
  createDataCartHierarchy() {
    let arrayList = this.cartEntities.reduce(function (result, current) {
        result[current.data.resTitle] = result[current.data.resTitle] || [];
        result[current.data.resTitle].push(current);
        return result;
        }, {});

        this.dataFiles = [];
        let parentObj: TreeNode = {};
        for (var key in arrayList) {
            // let resId = key;

            if (arrayList.hasOwnProperty(key)) {
                parentObj = {
                    data: {
                        'resTitle': key,
                    }
                };

                parentObj.children = [];
                for (let fields of arrayList[key]) {

                    let resId = fields.data.resId;

                    let fpath = fields.data.filePath.split("/");
                    if (fpath.length > 0) {
                        let child2: TreeNode = {};
                        child2.children = [];
                        let parent = parentObj;
                        let folderExists:boolean = false;
                        let folder = null;
                        for (let path in fpath) {
                            // console.log("##$%$%$ path path:" +fpath[path]);
                            /// Added this code to avoid the issue of extra file layers in the datacart
                            if(fpath[path] !== ""){
                            child2 = this.createDataCartChildrenTree(fpath[path],fields.data.id,resId,key,fields.data.downloadURL,fields.data.filePath,fields.data.downloadedStatus);
                            parent.children.push(child2);

                            parent = child2;}
                        }
                    }
                }
                this.walkData(parentObj, parentObj, 0);
                this.dataFiles.push(parentObj);
                this.index = {};
            }
        }
    }
  
  /**
   * Create the hierarchy for the tree
   */
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
                inputArray.children.forEach((item) => {
                    this.index[key].children.push(item);
                })
                var indx = 0;
                var found = false;
                parent.children.forEach((item) => {
                    if (!found &&
                        item.data.filePath === inputArray.data.filePath &&
                        item.data.resId === inputArray.data.resId
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

    /**
     * Create data hierarchy for children
     */
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
