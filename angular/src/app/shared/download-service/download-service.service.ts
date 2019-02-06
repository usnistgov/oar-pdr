import { Injectable } from '@angular/core';
import { HttpClientModule, HttpClient, HttpHeaders, HttpRequest, HttpEventType, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { CommonVarService } from '../../shared/common-var';
import { ZipData } from './zipData';
import { DownloadData } from './downloadData';
import { CartService } from '../../datacart/cart.service';
import { TestDataService } from '../../shared/testdata-service/testDataService';
import * as FileSaver from 'file-saver';

declare var saveAs: any;

@Injectable()
export class DownloadService {
  zipFilesDownloadingSub = new BehaviorSubject<number>(0);
  zipFilesProcessedSub = new BehaviorSubject<boolean>(false);

  zipFilesDownloadingDataCardSub = new BehaviorSubject<number>(0);
  zipFilesProcessedDataCardSub = new BehaviorSubject<boolean>(false);

  anyFileDownloadedFlagSub = new BehaviorSubject<boolean>(false);
  fireDownloadAllFlagSub = new BehaviorSubject<boolean>(false);
  // Determine if the download manager is a popup
  isPopupSub = new BehaviorSubject<boolean>(false);

  constructor(
    private http: HttpClient,
    private cartService: CartService,
    private testDataService: TestDataService,
    private commonVarService: CommonVarService,
  ) { }

  getFile(url, params): Observable<Blob> {
    return this.http.get(url, { responseType: 'blob', params: params });
    // return this.http.get(url, {responseType: 'arraybuffer'}).map(res => res);
  }

  /**
   * Calling end point 1 to get the bundle plan
   **/
  getBundlePlan(url:string, body:any): Observable<any> {
    const httpOptions = {
      headers: new HttpHeaders({
        'Content-Type':  'application/json'
      })
    };

    return this.http.post(url, body, httpOptions);
  }

  /**
  * Calling end point 2 to get the bundle
  **/
  getBundle(url, body): Observable<any> {
    const httpOptions = {
      headers: new HttpHeaders({
        'Content-Type':  'application/json'
      })
    };
    const req = new HttpRequest('POST', url, {
      reportProgress: true, body: body, responseType: 'blob'
    });

    return this.http.request(req);
    // console.log("Bundle url: " + url);
    // return this.http.post(url, {responseType: 'blob', params: params});
    // return this.http.post<Blob>(url, {responseType: 'blob', params: params});
    // for testing
    // return this.testDataService.getBundle('https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip', params);
  }

  /**
   * Save file
   **/
  saveToFileSystem(data, filename) {
    // var json = JSON.stringify(data);
    let blob = new Blob([data], { type: "octet/stream" });
    let blobUrl = window.URL.createObjectURL(blob);

    let a = document.createElement('a');
    document.body.appendChild(a);
    a.setAttribute('style', 'display: none');
    a.href = blobUrl;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(blobUrl);
    a.remove();
  }

  /**
   * Download zip
   **/
  download(nextZip: ZipData, zipdata: ZipData[], treeNode: any, whichPage: any) {
    // const req = new HttpRequest('GET', nextZip.downloadUrl, {
    //     reportProgress: true, responseType: 'blob'
    // });

    let sub = this.zipFilesDownloadingSub;
    if (whichPage == "datacard") {
      sub = this.zipFilesDownloadingDataCardSub;
    }

    nextZip.downloadStatus = 'downloading';

    this.setDownloadingNumber(sub.getValue() + 1, whichPage);

    // this.testSave();

    //     nextZip.downloadInstance = this.downloadService.postFile(this.distApi + "_bundle", JSON.stringify(zipdata.bundle)).subscribe(event => {

    // nextZip.downloadInstance = this.http.request(req).subscribe(
    nextZip.downloadInstance = this.getBundle(nextZip.downloadUrl, nextZip.bundle).subscribe(
      event => {
        // const blob = new Blob([event.body], { type: 'octet/stream' });
        // console.log("event.body");
        // console.log(event.body);
        // var data = event.data;
        // FileSaver.saveAs(event, nextZip.fileName);

        switch (event.type) {
          case HttpEventType.Response:
            // this.saveToFileSystem(event.body, nextZip.fileName);
            nextZip.downloadProgress = 0;
            nextZip.downloadStatus = 'downloaded';
            this.setDownloadingNumber(this.zipFilesDownloadingSub.getValue() - 1, whichPage);
            this.setDownloadProcessStatus(this.allDownloadFinished(zipdata), whichPage);
            this.setDownloadStatus(nextZip, treeNode, "downloaded");
            this.setFileDownloadedFlag(true);
            break;
          case HttpEventType.DownloadProgress:
            nextZip.downloadProgress = Math.round(100 * event.loaded / event.total);
            break;
        }

      },
      err => {
        nextZip.downloadStatus = 'downloadError';
        nextZip.downloadErrorMessage = err.message;
        this.setDownloadingNumber(this.zipFilesDownloadingSub.getValue() - 1, whichPage);
      }
    );
  }

  /**
   * Download next available zip in the queue
   **/
  downloadNextZip(zipData: ZipData[], treeNode: any, whichPage: any) {
    let sub = this.zipFilesDownloadingSub;
    if (whichPage == "datacard") {
      sub = this.zipFilesDownloadingDataCardSub;
    }

    if (sub.getValue() < this.commonVarService.getDownloadMaximum()) {
      let nextZip = this.getNextZipInQueue(zipData);
      if (nextZip != null) {
        this.download(nextZip, zipData, treeNode, whichPage);
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
    if (whichPage == "datacard") {
      sub = this.zipFilesDownloadingDataCardSub;
    }

    return sub.asObservable();
  }

  /**
   * Set the number of downloading zip files
   **/
  setDownloadingNumber(value: number, whichPage: any) {
    let sub = this.zipFilesDownloadingSub;
    if (whichPage == "datacard") {
      sub = this.zipFilesDownloadingDataCardSub;
    }

    sub.next(value);
  }

  /**
  * Watch overall process status
  **/
  watchDownloadProcessStatus(whichPage: any): Observable<any> {
    let sub = this.zipFilesProcessedSub;
    if (whichPage == "datacard") {
      sub = this.zipFilesProcessedDataCardSub;
    }

    return sub.asObservable();
  }

  /**
   * Set overall process status
   **/
  setDownloadProcessStatus(value: boolean, whichPage: any) {
    let sub = this.zipFilesProcessedSub;
    if (whichPage == "datacard") {
      sub = this.zipFilesProcessedDataCardSub;
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
    // console.log("totalDownloaded");
    // console.log(totalDownloaded);
    return totalDownloaded;
  }
}