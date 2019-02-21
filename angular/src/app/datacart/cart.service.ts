import { Data } from './data';
import { Injectable } from '@angular/core';
import { CartEntity } from './cart.entity';
import { HttpClientModule, HttpClient } from '@angular/common/http';
//import { Response,URLSearchParams } from '@angular/http';
import { Subject } from 'rxjs/Subject';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { Observable } from 'rxjs';
import * as _ from 'lodash';
import { SelectItem, TreeNode, TreeModule } from 'primeng/primeng';
import 'rxjs/add/operator/toPromise';




/**
 * The cart service provides an way to store the cart in local store.
 **/
@Injectable()
export class CartService {

  public cartEntities: CartEntity[];
  storageSub = new BehaviorSubject<number>(0);
  addCartSpinnerSub = new BehaviorSubject<boolean>(false);
  addAllCartSpinnerSub = new BehaviorSubject<boolean>(false);
  displayCartSub = new BehaviorSubject<boolean>(false);
  cartEntitesReadySub = new BehaviorSubject<boolean>(false);
  forceDatacartReloadSub = new BehaviorSubject<boolean>(false);
  cartSize: number;
  showAddCartSpinner: boolean = false;
  showAddAllCartSpinner: boolean = false;
  displayCart: boolean = false;
  private _storage = localStorage;
  currentCart: string = 'cart';

  constructor(private http: HttpClient) {
    this.initCart();
    this.getAllCartEntities();
    this.setCartLength(this.cartSize);
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

  /**
   * Initialize cart
   * **/
  initCart() {

    // if we dont have  any cart history, create a empty cart
    if (!this._storage.getItem(this.currentCart)) {

      let emptyMap: { [key: string]: number; } = {};
      this.setCart(emptyMap);

    }
  }

  /**
   * Save cart entries
   * **/
  saveListOfCartEntities(listOfCartEntries: CartEntity[]) {
    let cartMap = listOfCartEntries.reduce(function (map, cartEntry, i) {
      map[cartEntry.data.cartId] = cartEntry;
      return map;
    }, {});

    // persist the map
    this.setCart(cartMap);
    let cart = this.getAllCartEntities();
    this.setCartLength(this.cartSize);
  }

  /**
   * Returns all the items in the cart from the local storage
   **/
  getAllCartEntities() {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities: CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      cartEntities.push(value);
    }
    this.cartSize = cartEntities.length;
    // return the array
    return Promise.resolve(cartEntities);

  }

  /**
   * Update cart item download status
   **/
  updateCartItemDownloadStatus(cartId: string, status: any) {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities: CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      if (value.data.cartId == cartId) {
        value.data.downloadStatus = status;
      }
      cartEntities.push(value);
    }

    let cartMap = cartEntities.reduce(function (map, cartEntry, i) {
      map[cartEntry.data.cartId] = cartEntry;
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
   * Update cart download status
   **/
  updateCartDownloadStatus(status: boolean) {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities: CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      value.data.downloadStatus = status;
      cartEntities.push(value);
    }
    // console.log("cart" + JSON.stringify(cartEntities));
    let cartMap = cartEntities.reduce(function (map, cartEntry, i) {
      map[cartEntry.data.cartId] = cartEntry;
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
   * Remove cart items with download status
   **/
  removeByDownloadStatus() {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities: CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      if (value.data.downloadStatus == null) {
        cartEntities.push(value);
      }
    }
    let cartMap = cartEntities.reduce(function (map, cartEntry, i) {
      map[cartEntry.data.cartId] = cartEntry;
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

  /**
 * Remove cart items with cartId
 **/
  removeCartId(cartId: string) {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities: CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      if (value.data.cartId != cartId) {
        cartEntities.push(value);
      }
    }

    let cartMap = cartEntities.reduce(function (map, cartEntry, i) {
      map[cartEntry.data.cartId] = cartEntry;
      return map;
    }, {});
    this.clearTheCart();
    // persist the map
    this.setCart(cartMap);
    let cart = this.getAllCartEntities();
    this.setCartLength(this.cartSize);
  }


  clearTheCart() {
    this._storage.removeItem(this.currentCart);
  }

  /**
   * Returns a specific cart entry from the cartEntry map
   **/
  getCartEntryByDataId(dataId) {

    let myCartMap = this.getCart();
    return Promise.resolve(myCartMap[dataId]);

  }

  /**
   * Set the number of cart items
   **/
  setCartLength(value: number) {
    this.storageSub.next(value);
  }

  /**
   * Will persist the product to local storage
   **/
  deselectAll() {
    if (!this._storage.getItem(this.currentCart)) {
      let emptyMap: { [key: string]: number; } = {};

      this.setCart(emptyMap);
      let cartMap = this.getCart();

      // save the map
      this.setCart(cartMap);
    }

    let cartMap = this.getCart();
    for (let key in cartMap) {
      let value = cartMap[key];
      value.data.isSelected = false;
    }

    // save the map
    this.setCart(cartMap);
    return Promise.resolve(cartMap);
  }

  /**
   * Will persist the product to local storage
   **/
  addDataToCart(data: Data) {
    // product id , quantity
    let cartMap = this.getCart();
    // if we dont have  any cart history, create a empty cart
    if (!this._storage.getItem(this.currentCart)) {
      let emptyMap: { [key: string]: number; } = {};

      this.setCart(emptyMap);
      let cartMap = this.getCart();
      // if not, set default value
      cartMap[data.cartId] = {
        'data': data,
      }
      // save the map
      this.setCart(cartMap);
    }

    cartMap = this.getCart();
    cartMap[data.cartId] = {
      'data': data,
    }

    // save the map
    this.setCart(cartMap);
    let cart = this.getAllCartEntities();
    this.setCartLength(this.cartSize);
    return Promise.resolve(cartMap);
  }

  /**
   * Update File spinner status
   **/
  updateFileSpinnerStatus(addFileSpinner: boolean) {
    this.addCartSpinnerSub.next(addFileSpinner);
  }

  /**
   * Update All File spinner status
   **/
  updateAllFilesSpinnerStatus(addAllFilesSpinner: boolean) {
    this.addAllCartSpinnerSub.next(addAllFilesSpinner);
  }

  /**
   * Update cart display status
   **/

  updateCartDisplayStatus(displayCart: boolean) {
    this.displayCartSub.next(displayCart);
  }

  /**
   * Retrieve the cart from local storage
   **/
  getCart() {
    let cartAsString = this._storage.getItem(this.currentCart);

    return JSON.parse(cartAsString);
  }

  /**
   * Persists the cart to local storage
   **/
  private setCart(cartMap): void {
    this._storage.setItem(this.currentCart, JSON.stringify(cartMap));
    //this.storageSub.next(true);
  }

  /**
  * Update cart entites ready flag
  **/
  setCartEntitesReady(ready: boolean) {
    this.cartEntitesReadySub.next(ready);
  }

  /**
  * Watch update cart entites ready flag
  **/
  watchCartEntitesReady(): Observable<boolean> {
    return this.cartEntitesReadySub.asObservable();
  }

  /**
  * Update cart entites ready flag
  **/
  setForceDatacartReload(ready: boolean) {
    this.forceDatacartReloadSub.next(ready);
  }

  /**
  * Watch update cart entites ready flag
  **/
  watchForceDatacartReload(): Observable<boolean> {
    return this.forceDatacartReloadSub.asObservable();
  }


  /**
  * Function to check if cartId is in the data cart.
  **/
  isInDataCart(cartId: string) {
    let cartMap = this.getCart();

    for (let key in cartMap) {
      let value = cartMap[key];
      if (value.data.cartId == cartId) {
        return true;
      }
    }
    return false;
  }

  /**
  * Function to set current data cart.
  **/
  setCurrentCart(cart: string){
    this.currentCart = cart;
  }
}
