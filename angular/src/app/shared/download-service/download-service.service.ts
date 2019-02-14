import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { CommonVarService } from '../../shared/common-var';
import { ZipData } from './zipData';
import { DownloadData } from './downloadData';
import { CartService } from '../../datacart/cart.service';
import { TestDataService } from '../../shared/testdata-service/testDataService';
import { FileSaverService } from 'ngx-filesaver';

declare var saveAs: any;

@Injectable()
export class DownloadService {
  zipFilesDownloadingSub = new BehaviorSubject<number>(0);
  zipFilesProcessedSub = new BehaviorSubject<boolean>(false);

  zipFilesDownloadingDataCartSub = new BehaviorSubject<number>(0);
  zipFilesProcessedDataCartSub = new BehaviorSubject<boolean>(false);

  anyFileDownloadedFlagSub = new BehaviorSubject<boolean>(false);
  fireDownloadAllFlagSub = new BehaviorSubject<boolean>(false);
  // Determine if the download manager is a popup
  isPopupSub = new BehaviorSubject<boolean>(false);
  isLocalTesting: boolean = false;

  constructor(
    private http: HttpClient,
    private cartService: CartService,
    private _FileSaverService: FileSaverService,
    private testDataService: TestDataService,
    private commonVarService: CommonVarService
  ) {
    this.isLocalTesting = this.commonVarService.getLocalTestingFlag();
  }

  getFile(url, params): Observable<Blob> {
    return this.http.get(url, { responseType: 'blob', params: params });
    // return this.http.get(url, {responseType: 'arraybuffer'}).map(res => res);
  }

  /**
   * Calling end point 1 to get the bundle plan
   **/
  getBundlePlan(url: string, body: any): Observable<any> {
    const httpOptions = {
      headers: new HttpHeaders({
        'Content-Type': 'application/json'
      })
    };

    return this.http.post(url, body, httpOptions);
  }

  /**
  * Calling end point 2 to get the bundle
  **/
  getBundle(url, body): Observable<any> {
    // console.log("Get bundle - body:");
    // console.log(body);

    const request = new HttpRequest(
      "POST", url, body,
      { headers: new HttpHeaders({ 'Content-Type': 'application/json', 'responseType': 'blob' }), reportProgress: true, responseType: 'blob' });

    if (!this.isLocalTesting)
      return this.http.request(request);
    else
      return this.testDataService.getBundle('https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip', body);
  }

  /**
   * Download zip
   **/
  download(nextZip: ZipData, zipdata: ZipData[], treeNode: any, whichPage: any) {
    // const req = new HttpRequest('GET', nextZip.downloadUrl, {
    //     reportProgress: true, responseType: 'blob'
    // });

    let sub = this.zipFilesDownloadingSub;
    if (whichPage == "datacart") {
      sub = this.zipFilesDownloadingDataCartSub;
    }

    nextZip.downloadStatus = 'downloading';
    this.setDownloadingNumber(sub.getValue() + 1, whichPage);

    nextZip.downloadInstance = this.getBundle(nextZip.downloadUrl, JSON.stringify(nextZip.bundle)).subscribe(
      event => {
        switch (event.type) {
          case HttpEventType.Response:
            nextZip.downloadStatus = 'Writing data to destination';
            this._FileSaverService.save(<any>event.body, nextZip.fileName);
            nextZip.downloadProgress = 0;
            nextZip.downloadStatus = 'downloaded';
            this.setDownloadingNumber(sub.getValue() - 1, whichPage);
            this.setDownloadProcessStatus(this.allDownloadFinished(zipdata), whichPage);
            this.setDownloadStatus(nextZip, treeNode, "downloaded");
            this.setFileDownloadedFlag(true);
            break;
          case HttpEventType.DownloadProgress:
            if (event.total > 0) {
              nextZip.downloadProgress = Math.round(100 * event.loaded / event.total);
            }
            break;
          default:
            break;
        }

      },
      err => {
        nextZip.downloadStatus = 'Error';
        nextZip.downloadErrorMessage = err.message;
        nextZip.downloadProgress = 0;
        this.setDownloadingNumber(this.zipFilesDownloadingSub.getValue() - 1, whichPage);
      }
    );
  }

  /**
   * Download next available zip in the queue
   **/
  downloadNextZip(zipData: ZipData[], treeNode: any, whichPage: any) {
    let sub = this.zipFilesDownloadingSub;
    if (whichPage == "datacart") {
      sub = this.zipFilesDownloadingDataCartSub;
    }
    if (sub.getValue() < this.commonVarService.getDownloadMaximum()) {
      let nextZip = this.getNextZipInQueue(zipData);
      if (nextZip != null) {
        this.download(nextZip, zipData, treeNode, whichPage);
      }
      else{
        this.setDownloadingNumber(-1, whichPage);
      }
    }
  }

  /**
   * Return next available zip in the queue
   **/
  getNextZipInQueue(zipData: ZipData[]) {
    let zipQueue = zipData.filter(item => item.downloadStatus == null);

    if (zipQueue.length > 0) {
      return zipQueue[0];
    } else {
      return null;
    }
  }

  getDownloadData(files: any, downloadData: any) {
    let existItem: any;
    for (let comp of files) {
      if (comp.children.length > 0) {
        this.getDownloadData(comp.children, downloadData);
      } else {
        if (comp.data['filePath'] != null && comp.data['filePath'] != undefined) {
          if (comp.data['filePath'].split(".").length > 1) {
            existItem = downloadData.filter(item => item.filePath === comp.data['ediid'] + comp.data['filePath']
              && item.downloadUrl === comp.data['downloadUrl']);

            if (existItem.length == 0) {
              downloadData.push({ "filePath": comp.data['ediid'] + comp.data['filePath'], 'downloadUrl': comp.data['downloadUrl'] });
            }
          }
        }
      }
    }
  }

  /**
  * Set the number of downloading zip files
  **/
  watchDownloadingNumber(whichPage: any): Observable<any> {
    let sub = this.zipFilesDownloadingSub;
    if (whichPage == "datacart") {
      sub = this.zipFilesDownloadingDataCartSub;
    }

    return sub.asObservable();
  }

  /**
   * Set the number of downloading zip files
   **/
  setDownloadingNumber(value: number, whichPage: any) {
    let sub = this.zipFilesDownloadingSub;
    if (whichPage == "datacart") {
      sub = this.zipFilesDownloadingDataCartSub;
    }

    sub.next(value);
  }

  /**
  * Watch overall process status
  **/
  watchDownloadProcessStatus(whichPage: any): Observable<any> {
    let sub = this.zipFilesProcessedSub;
    if (whichPage == "datacart") {
      sub = this.zipFilesProcessedDataCartSub;
    }

    return sub.asObservable();
  }

  /**
   * Set overall process status
   **/
  setDownloadProcessStatus(value: boolean, whichPage: any) {
    let sub = this.zipFilesProcessedSub;
    if (whichPage == "datacart") {
      sub = this.zipFilesProcessedDataCartSub;
    }

    sub.next(value);
  }

  /**
   * Set download status of given tree node
   **/
  setDownloadStatus(zip: any, treeNode: any, status: any) {
    for (let includeFile of zip.bundle.includeFiles) {
      let filePath = includeFile.filePath.substring(includeFile.filePath.indexOf('/'));
      let node = this.searchTreeByfilePath(treeNode, filePath);
      if (node != null) {
        node.data.downloadStatus = status;
        this.cartService.updateCartItemDownloadStatus(node.data['cartId'], status);
      }
    }
  }

  /**
   * Check if all zip files are downloaded
   **/
  allDownloaded(zipData: any) {
    for (let zip of zipData) {
      if (zip.downloadStatus != 'downloaded') {
        return false;
      }
    }
    return true;
  }

  /**
   * Check if all doanload processes have finished
   **/
  allDownloadFinished(zipData: any) {
    for (let zip of zipData) {
      if (zip.downloadStatus == null || zip.downloadStatus == 'downloading') {
        return false;
      }
    }
    return true;
  }

  /**
   * Search tree by given full path
   **/
  searchTreeByfilePath(element, filePath) {
    if (element.data.filePath == filePath) {
      return element;
    } else if (element.children.length > 0) {
      var i;
      var result = null;
      for (i = 0; result == null && i < element.children.length; i++) {
        result = this.searchTreeByfilePath(element.children[i], filePath);
      }
      return result;
    }
    return null;
  }

  getDownloadedNumber(zipData: any) {
    let totalDownloadedZip: number = 0;
    for (let zip of zipData) {
      if (zip.downloadStatus == 'downloaded') {
        totalDownloadedZip += 1;
      }
    }
    return totalDownloadedZip;
  }

  resetZipName(element) {
    if (element.data != undefined) {
      element.data.zipFile = null;
    }
    if (element.children.length > 0) {
      for (let i = 0; i < element.children.length; i++) {
        this.resetZipName(element.children[i]);
      }
    }
  }

  /**
   * Set general download flag
   **/
  setFileDownloadedFlag(value: boolean) {
    this.anyFileDownloadedFlagSub.next(value);
  }

  /**
   * Watch general download flag
   **/
  watchAnyFileDownloaded(): Observable<any> {
    return this.anyFileDownloadedFlagSub.asObservable();
  }

  /**
   * Set flag to fire download all function
   **/
  setFireDownloadAllFlag(value: boolean) {
    this.fireDownloadAllFlagSub.next(value);
  }

  /**
   * Watch fire download all flag
   **/
  watchFireDownloadAllFlag(): Observable<any> {
    return this.fireDownloadAllFlagSub.asObservable();
  }

  /**
   * Set the flag if download manager is a popup
   **/
  setIsPopupFlag(value: boolean) {
    this.isPopupSub.next(value);
  }

  /**
   * Watch popup flag
   **/
  watchIsPopupFlag(): Observable<any> {
    return this.isPopupSub.asObservable();
  }

  getTotalDownloaded(dataFiles: any) {
    let totalDownloaded: number = 0;
    for (let comp of dataFiles) {
      if (comp.children.length > 0) {
        totalDownloaded += this.getTotalDownloaded(comp.children);
      } else {
        if (comp.data.downloadStatus == 'downloaded') {
          totalDownloaded += 1;
        }
      }
    }
    return totalDownloaded;
  }
}