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

  /**
   * Initialize cart
   * **/
  initCart () {

    // if we dont have  any cart history, create a empty cart
    if(!this._storage.getItem('cart')) {

      let emptyMap : { [key:string]:number; } = {};
      this.setCart(emptyMap);

    }
  }

  /**
   * Save cart entries
   * **/
  saveListOfCartEntities(listOfCartEntries : CartEntity[]) {
    // reduce all the entities to a map
    // let cartMap = listOfCartEntries.reduce(function(map, cartEntry, i) {
    //   map[cartEntry.data.id] = cartEntry;
    //   return map;
    // }, {});

    let cartMap = listOfCartEntries.reduce(function(map, cartEntry, i) {
      map[cartEntry.data.cartId] = cartEntry;
      return map;
    }, {});

    // persist the map
    this.setCart(cartMap);
    let cart  = this.getAllCartEntities();
    this.setCartLength (this.cartSize);
  }

  /**
   * Returns all the items in the cart from the local storage
   **/
  getAllCartEntities()  {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities : CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      // console.log("value" + JSON.stringify(value.data.cartId));
      cartEntities.push(value);
    }

    this.cartSize = cartEntities.length;
    // return the array
    return Promise.resolve(cartEntities);

  }

  /**
   * Update cart item download status
   **/
  updateCartItemDownloadStatus(cartId:string, status:any)  {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities : CartEntity[] = [];
    console.log("myCartMap:");
    console.log(myCartMap);

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      if (value.data.cartId == cartId) {
        // console.log("cartId in cart match update" + cartId);
        // console.log("status before" + JSON.stringify(value.data.downloadStatus));
        value.data.downloadStatus = status;
        // console.log("status after" + JSON.stringify(value.data.downloadStatus));
      }
      // console.log("value" + JSON.stringify(value.data.cartId));
      cartEntities.push(value);
    }
    // console.log("cart" + JSON.stringify(cartEntities));
    let cartMap = cartEntities.reduce(function(map, cartEntry, i) {
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
  updateCartDownloadStatus(status:boolean)  {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities : CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
        // console.log("status before" + JSON.stringify(value.data.downloadStatus));
        value.data.downloadStatus = status;
        // console.log("status after" + JSON.stringify(value.data.downloadStatus));
      // console.log("value" + JSON.stringify(value.data.cartId));
      cartEntities.push(value);
    }
    // console.log("cart" + JSON.stringify(cartEntities));
    let cartMap = cartEntities.reduce(function(map, cartEntry, i) {
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
  removeDownloadStatus()  {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities : CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      // console.log("status before" + JSON.stringify(value.data.downloadStatus));
      if (value.data.downloadStatus == null ) {
        // console.log("status after" + JSON.stringify(value.data.downloadStatus));
        // console.log("value" + JSON.stringify(value.data.cartId));
        cartEntities.push(value);
      }
    }
    // console.log("cart" + JSON.stringify(cartEntities));
    let cartMap = cartEntities.reduce(function(map, cartEntry, i) {
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
  removeCartId(cartId: string)  {
    // get the cart
    let myCartMap = this.getCart();
    let cartEntities : CartEntity[] = [];

    // convert the map to an array
    for (let key in myCartMap) {
      let value = myCartMap[key];
      // console.log("status before" + JSON.stringify(value.data.downloadStatus));
      if (value.data.cartId != cartId ) {
        // console.log("status after" + JSON.stringify(value.data.downloadStatus));
        // console.log("value" + JSON.stringify(value.data.cartId));
        cartEntities.push(value);
      }
    }
    // console.log("cart" + JSON.stringify(cartEntities));
    let cartMap = cartEntities.reduce(function(map, cartEntry, i) {
      map[cartEntry.data.cartId] = cartEntry;
      return map;
    }, {});
    this.clearTheCart();
    // persist the map
    this.setCart(cartMap);
    let cart  = this.getAllCartEntities();
    this.setCartLength (this.cartSize);
    // this.getCart();
    // this.cartSize = cartEntities.length;
    // // return the array
    // return Promise.resolve(cartEntities);

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

  /**
   * Set the number of cart items
   **/
  setCartLength(value: number) {
    this.storageSub.next(value);
  }

  /**
   * Will persist the product to local storage
   **/
  addDataToCart(data: Data) : void {
    console.log(data);
    // product id , quantity
    let cartMap = this.getCart();
    // if we dont have  any cart history, create a empty cart
    if (!this._storage.getItem('cart')) {
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

    // if the current key exists in the map , append value
    if (cartMap[data.cartId] != undefined) {
    } else {
      // if not, set default value
      cartMap[data.cartId] = {
        'data': data,
      }
    }

    // save the map
    this.setCart(cartMap);
    let cart  = this.getAllCartEntities();
    this.setCartLength (this.cartSize);
    //this.updateFileSpinnerStatus(false);

  }

  /**
   * Update File spinner status
   **/
  updateFileSpinnerStatus(addFileSpinner:boolean)
  {
    this.addCartSpinnerSub.next(addFileSpinner);
  }

  /**
   * Update All File spinner status
   **/
  updateAllFilesSpinnerStatus(addAllFilesSpinner:boolean)
  {
    this.addAllCartSpinnerSub.next(addAllFilesSpinner);
  }

  /**
   * Update cart display status
   **/

  updateCartDisplayStatus(displayCart:boolean)
  {
    this.displayCartSub.next(displayCart);
  }

  /**
   * Retrieve the cart from local storage
   **/
  getCart() {
    let cartAsString = this._storage.getItem('cart');
    // console.log("cartAsString:");
    // console.log(cartAsString);

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
