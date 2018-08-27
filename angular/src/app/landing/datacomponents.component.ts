// /**
//  * Support for resource components from a NERDm record
//  */

// /**
//  * a NERDm resource component description.  This interface is used to recognize
//  * an element in the array value of the NERDm resource property, "components".
//  */
// export interface ComponentDesc {
//     "@type": string[];
//     filepath?: string;
// }

// /**
//  * a NERDm data component description.  This interface is used to recognize
//  * an element in the array value of the NERDm resource property, "components",
//  * as a data item (either a DataFile or Subcollection).
//  */
// export interface DataComponentDesc extends ComponentDesc {
//     filepath: string;
//     size?: number;
// }

// /**
//  * a compare function for ordering DataCompoentDesc objects alphabeticaly
//  * by their "filepath" properties
//  */
// export function compare_by_filepath(a: DataComponentDesc, b: DataComponentDesc) {
//     return a.filepath.localeCompare(b.filepath);
// }

// /**
//  * a compare function for ordering DataHierarchy instances for our display 
//  * preferences
//  */
// export function compare_for_display(a: DataHierarchy, b: DataHierarchy) {
//     let c = prefer_readme(a, b);
//     if (c != 0) return c

//     c = prefer_subcollections(a, b);
//     if (c != 0) return c

//     return a.data.filepath.localeCompare(b.data.filepath)
// }

// export function prefer_readme(a: DataHierarchy, b: DataHierarchy) {
//     let fp = a.data.filepath.split('/');
//     let fna = fp[fp.length-1];
//     fp = b.data.filepath.split('/');
//     let fnb = fp[fp.length-1];

//     if (fna.toUpperCase().startsWith('README')) {
//         if (fnb.toUpperCase().startsWith('README')) 
//             return fna.localeCompare(fnb);
//         return -1;
//     }
//     else if (fnb.toUpperCase().startsWith('README')) 
//         return +1;
//     return 0;
// }

// function type_is_subcol(e: string,i: number,a: string[]) {
//     return e.endsWith(":Subcollection");
// }

// export function prefer_subcollections(a: DataHierarchy, b: DataHierarchy) {
//     let ta = a.data["@type"].filter(type_is_subcol);
//     let tb = b.data["@type"].filter(type_is_subcol);

//     if (ta.length > 0) {
//         if (tb.length > 0)
//             return a.data.filepath.localeCompare(b.data.filepath);
//         return -1;
//     }
//     else if (tb.length > 0)
//         return +1;
//     return 0;
// }

// /**
//  * a hierarchy of NERDm data components
//  */
// export class DataHierarchy {
//     public children: DataHierarchy[];
//     public data: DataComponentDesc;

//     /**
//      * create the hierarchy.  
//      * @param dclist   a list of data component objects 
//      * @param data     the data object that describes this node
//      * @param name     a name for this hierarchy node
//      */  
//     constructor(dclist?: DataComponentDesc[], data?: DataComponentDesc) {

//         if (! dclist)
//             dclist = []
//         let c = dclist
//         if (! data) {
//             // this DataHierarchy will represent the top of a hierarchy.
//             // Note: when data is provided, we assume dclist has been sorted.
//             data = { filepath: "", "@type": ["nrdp:Subcollection"] };
//             c = dclist.slice().sort(compare_by_filepath);
//         }
//         this.data = data
//         let filepath = this.data.filepath
//         if (filepath.length > 0) filepath = filepath+'/'
//         this.children = [];

//         while (c.length > 0 && c[0].filepath.startsWith(filepath)) {
//             // the next element in c is a descendent of this node
//             let rpath = c[0].filepath.substring(filepath.length)
//             if (rpath.includes("/")) {
//                 // there's a missing collection child; create it.
//                 let sub = rpath.split("/")[0]
//                 this.children.push(
//                     new DataHierarchy(c, { filepath: filepath+sub,
//                                            "@type": ["nrdp:Subcollection"]}))
//             } else {
//                 // el is a direct child; any grandchildren will directly
//                 // follow it in the list
//                 let el = c.shift();
//                 this.children.push(new DataHierarchy(c, el))
//             }
//         }

//         this.children.sort(compare_for_display)
//     }

//     is_subcoll() : boolean {
//         return (this.data["@type"].filter(type_is_subcol).length > 0);
//     }
// }

// /**
//  * a list of NERDm resource components.
//  */
// export class ResComponents {
//     constructor(public data: ComponentDesc[]) {
//     }

//     /**
//      * select out the data components from the list of NERDm resource components
//      */
//     dataComponentDescs(): DataComponentDesc[] {
//         return this.data.filter(function(el, i, a) {
//             return (el.hasOwnProperty('filepath'))
//         }).map(function(el, i, a) { return <DataComponentDesc>el; })
//     }

//     /**
//      * select out the data components and return it as a sorted 
//      * DataHierarchy.
//      */
//     dataHierarchy() {
//         return new DataHierarchy(this.dataComponentDescs())
//     }
// };