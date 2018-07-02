import {Data} from './data';
import {Injectable} from '@angular/core';
import {CartEntity} from './cart.entity';
import { HttpClientModule, HttpClient } from '@angular/common/http';
//import { Response,URLSearchParams } from '@angular/http';
import { Subject} from 'rxjs/Subject';
import {BehaviorSubject } from 'rxjs/BehaviorSubject';
import {Observable } from 'rxjs';
import * as _ from 'lodash';
import { SelectItem, TreeNode, TreeModule } from 'primeng/primeng';
import 'rxjs/add/operator/toPromise';




/**
 * The cart service provides an way to store the cart in local store.
 **/
@Injectable()
export class CartService {

  public cartEntities : CartEntity[];
  storageSub= new BehaviorSubject<number>(0);
  addCartSpinnerSub = new BehaviorSubject<boolean>(false);
  addAllCartSpinnerSub = new BehaviorSubject<boolean>(false);
  displayCartSub = new BehaviorSubject<boolean>(false);
  cartSize: number ;
  showAddCartSpinner : boolean = false;
  showAddAllCartSpinner : boolean = false;
  displayCart : boolean = false;
  private _storage = localStorage;




  constructor(private http: HttpClient) {
    this.initCart();
    this.getAllCartEntities();
    this.setCartLength (this.cartSize);
  }

  watchStorage(): Observable<any> {
    return this.storageSub.asObservable();
  }

  watchAddFileCart(): Observable<any> {
    return this.addCartSpinnerSub.asObservable();
  }

  watchAddAllFilesCart(): Observable<any> {
    return this.addAllCartSpinnerSub.asObservable();
  }

  watchCart(): Observable<any> {
    return this.displayCartSub.asObservable();
  }


  initCart () {

    // if we dont have  any cart history, create a empty cart
    if(!this._storage.getItem('cart')) {

      let emptyMap : { [key:string]:number; } = {};
      this.setCart(emptyMap);

    }
  }

  saveListOfCartEntities(listOfCartEntries : CartEntity[]) {
    // reduce all the entities to a map
    let cartMap = listOfCartEntries.reduce(function(map, cartEntry, i) {
      map[cartEntry.data.id] = cartEntry;
      return map;
    }, {});

    // persist the map
    this.setCart(cartMap);
    let cart  = this.getAllCartEntities();
    console.log("cart length" + this.cartSize);
    this.setCartLength (this.cartSize);
  }

  /**
   * Returns all the products in the cart form the local storage
   *
   **/
  getAllCartEntities()  {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities : CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      console.log("value" + JSON.stringify(value.data.resId));
      cartEntities.push(value);
    }

    this.cartSize = cartEntities.length;
    // return the array
    return Promise.resolve(cartEntities);

  }

  /**
   * Returns all the products in the cart form the local storage
   *
   **/
  updateCartItemDownloadStatus(id:string, status:any)  {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities : CartEntity[] = [];
    console.log("id in cart update" + id);
    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      if (value.data.id == id) {
        console.log("id in cart match update" + id);
        console.log("status before" + JSON.stringify(value.data.downloadedStatus));
        value.data.downloadedStatus = status;
        console.log("status after" + JSON.stringify(value.data.downloadedStatus));
      }
      console.log("value" + JSON.stringify(value.data.resId));
      cartEntities.push(value);
    }
    console.log("cart" + JSON.stringify(cartEntities));
    let cartMap = cartEntities.reduce(function(map, cartEntry, i) {
      map[cartEntry.data.id] = cartEntry;
      return map;
    }, {});

    // persist the map
    this.setCart(cartMap);
    this.getCart();
    this.cartSize = cartEntities.length;
    // return the array
    return Promise.resolve(cartEntities);

  }

  /**
   * Returns all the products in the cart form the local storage
   *
   **/
  updateCartDownloadStatus(status:boolean)  {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities : CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
        console.log("status before" + JSON.stringify(value.data.downloadStatus));
        value.data.downloadedStatus = status;
        console.log("status after" + JSON.stringify(value.data.downloadStatus));
      console.log("value" + JSON.stringify(value.data.resId));
      cartEntities.push(value);
    }
    console.log("cart" + JSON.stringify(cartEntities));
    let cartMap = cartEntities.reduce(function(map, cartEntry, i) {
      map[cartEntry.data.id] = cartEntry;
      return map;
    }, {});
    // persist the map
    this.setCart(cartMap);
    this.getCart();
    this.cartSize = cartEntities.length;
    // return the array
    return Promise.resolve(cartEntities);

  }

  /**
   * Returns all the products in the cart form the local storage
   *
   **/
  removeDownloadStatus()  {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities : CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      console.log("status before" + JSON.stringify(value.data.downloadStatus));
      if (value.data.downloadedStatus == null ) {
        console.log("status after" + JSON.stringify(value.data.downloadStatus));
        console.log("value" + JSON.stringify(value.data.resId));
        cartEntities.push(value);
      }
    }
    console.log("cart" + JSON.stringify(cartEntities));
    let cartMap = cartEntities.reduce(function(map, cartEntry, i) {
      map[cartEntry.data.id] = cartEntry;
      return map;
    }, {});
    this.clearTheCart();
    // persist the map
    this.setCart(cartMap);
    this.getCart();
    this.cartSize = cartEntities.length;
    // return the array
    return Promise.resolve(cartEntities);

  }

  clearTheCart() {
    this._storage.clear();
    //this.storageSub.next(true);
  }

  /**
   * Returns a specific cart entry from the cartEntry map
   **/
  getCartEntryByDataId(dataId) {

    let myCartMap = this.getCart();
    return Promise.resolve(myCartMap[dataId]);

  }

  setCartLength(value: number) {
    this.storageSub.next(value);
    console.log("cart size inside method" + this.storageSub.getValue());
  }
  /**
   * Will persist the product to local storage
   *
   **/
  addDataToCart(data: Data) : void {
    // product id , quantity
    let cartMap = this.getCart();

    // if we dont have  any cart history, create a empty cart
    if (!this._storage.getItem('cart')) {
      let emptyMap: { [key: string]: number; } = {};
      this.setCart(emptyMap);
      let cartMap = this.getCart();
      // if not, set default value
      cartMap[data.id] = {
        'data': data,
      }
      // save the map
      this.setCart(cartMap);
    }

    cartMap = this.getCart();

    // if the current key exists in the map , append value
      if (cartMap[data.id] != undefined) {

        console.log("key exists");
        console.log("data id - " + data.id);
      } else {
        // if not, set default value
        cartMap[data.id] = {
          'data': data,
        }
      }
    // save the map
    this.setCart(cartMap);
    let cart  = this.getAllCartEntities();
    this.setCartLength (this.cartSize);
    //this.updateFileSpinnerStatus(false);

  }

  updateFileSpinnerStatus(addFileSpinner:boolean)
  {
    this.addCartSpinnerSub.next(addFileSpinner);
  }

  updateAllFilesSpinnerStatus(addAllFilesSpinner:boolean)
  {
    this.addAllCartSpinnerSub.next(addAllFilesSpinner);
  }

  updateCartDisplayStatus(displayCart:boolean)
  {
    this.displayCartSub.next(displayCart);
  }
/**
   * Retrive the cart from local storage
   **/
  private getCart() {

    let cartAsString = this._storage.getItem('cart');
    //console.log("cartasstring" + JSON.stringify(cartAsString));
    return JSON.parse(cartAsString);

  }
  /**
   * Persists the cart to local storage
   **/
  private setCart(cartMap) : void{
    this._storage.setItem('cart',JSON.stringify(cartMap));
    //this.storageSub.next(true);
  }

}
