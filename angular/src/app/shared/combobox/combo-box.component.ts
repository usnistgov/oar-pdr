// This combo-box has few features: 
// 1. Allows user to select data from a dropdown datalist
// 2. Auto filter the dropdown list when user starts typing in the input box
// 3. User can type in new value that is not in the dropdown list 

import { Component, Input, Output, OnInit, EventEmitter, HostListener, SimpleChanges } from '@angular/core'
import { ComboBoxPipe } from './combo-box.pipe';
import { BrowserModule } from '@angular/platform-browser'
import { FormsModule } from '@angular/forms'

export enum KEY_CODE {
  UP_ARROW = 38,
  DOWN_ARROW = 40,
  TAB_KEY = 9,
  ENTER = 13
}
@Component({
  selector: 'combo-box',
  templateUrl: './combo-box.component.html',
  styleUrls: ['./combo-box.component.css'],
  providers: [ComboBoxPipe]
})
export class ComboBoxComponent implements OnInit {

  // Data list for the dropdown
  @Input()
  dataList: any[];

  // Data list column to be used
  @Input()
  columnName: string;

  // Data bind field
  @Input()
  controlField: any;

  // Tell parent component that data has been changed
  @Output()
  controlFieldChange: EventEmitter<string> = new EventEmitter();

  dummyDataList: any[];
  showDropDown: boolean;
  counter: number;


  constructor(private ComboBoxPipe: ComboBoxPipe) {
    this.reset();
  }

  ngOnInit() {
    this.reset();
  }

  ngOnChanges(changes: SimpleChanges){
    if(changes.dataList){
      this.dummyDataList = this.dataList;
    }
  }

  /*
  *   When text input box on focus, reset the dropdown item indicator
  */
  onFocusEventAction(): void {
    this.counter = -1;
  }

  /*
  *    When text input box on blur, set the value and hide the dropdown
  */
  onBlurEventAction(): void {
    if (this.counter > -1) this.controlField = this.dummyDataList[this.counter][this.columnName];
    this.showDropDown = false;
  }

  /*
  *    Detect keyboard activity
  */
  onKeyDownAction(event: KeyboardEvent): void {
    this.showDropDown = true;
    if (event.keyCode === KEY_CODE.UP_ARROW) {
      this.counter = (this.counter === 0) ? this.counter : --this.counter;
      this.checkHighlight(this.counter);
      this.controlField = this.dataList[this.counter]["columnName"];
    }

    if (event.keyCode === KEY_CODE.DOWN_ARROW) {
      this.counter = (this.counter === this.dataList.length - 1) ? this.counter : ++this.counter;
      this.checkHighlight(this.counter);
      this.controlField = this.dataList[this.counter]["columnName"];
    }

    if (event.keyCode === KEY_CODE.ENTER) {
      // Hide dropdown if user hit enter
      this.showDropDown = false;
    }

    this.controlFieldChange.emit(this.controlField);
  }

  /*
  *   highlight current item
  */
  checkHighlight(currentItem): boolean {
    if (this.counter === currentItem) return true;
    else return false;
  }

  /*
  *   Toogle dropDown menu
  */
  toogleDropDown(): void {
    this.showDropDown = !this.showDropDown;
  }

  /*
  *   Reset dropDown menu
  */
  reset(): void {
    this.showDropDown = false;
    this.dummyDataList = this.dataList;
  }

  /*
  *   On text change
  */
  textChange(value) {
    this.dummyDataList = [];
    if (value.length > 0) {
      this.dummyDataList = this.ComboBoxPipe.transform(this.dataList, this.columnName, value);
      this.dummyDataList.sort((a, b) => a.name.localeCompare(b.name));
      if (this.dummyDataList) { this.showDropDown = true; }
    } else {
      this.reset();
    }

    this.controlFieldChange.emit(value);
  }

  /*
  *   Update text box
  */
  updateTextBox(valueSelected) {
    this.controlField = valueSelected;
    this.controlFieldChange.emit(this.controlField);
    this.showDropDown = false;
  }

  /*
  *   Following two functions handle click outside dropdown
  */
  @HostListener('document:click', ['$event']) clickout(event) {
    // Click outside of the menu was detected
    this.showDropDown = false;
  }

  handleAsideClick(event: Event) {
    event.stopPropagation(); // Stop the propagation to prevent reaching document
  }

  arrowClass(){
    if(this.showDropDown){
      return "faa faa-angle-up";
    } else{
      return "faa faa-angle-down";
    }
  }
}