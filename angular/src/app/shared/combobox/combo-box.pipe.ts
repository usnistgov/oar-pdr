import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'combo-box-filter'
})
export class ComboBoxPipe implements PipeTransform{
  transform(dataToSort: string[], columnNameToSort:string, stringToSort: string):any[]{
    let sortedData: string[];
    sortedData = [];
    for(var i =0; i<dataToSort.length; ++i){
      if(dataToSort[i][columnNameToSort].toLowerCase().search(stringToSort.toLowerCase())>-1) sortedData.push(dataToSort[i]);
    }

    return sortedData; 
  }
}