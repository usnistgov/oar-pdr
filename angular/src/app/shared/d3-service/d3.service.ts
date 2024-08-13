import { Injectable } from '@angular/core';
import * as d3 from 'd3';

@Injectable({
  providedIn: 'root'
})
export class D3Service {
    constructor() { }

    drawSectionHeaderBackground(svg: any, title: string, sectionWidth: number, backColor: string, width: number = 170, sectionID: string = "#sectionHeader"){
        // if(svg){
            // d3.select("svg").remove();
            // d3.select(sectionID).remove();
        // }

        // var width = 170;
        var height = 25;
        console.log("width", width)
        console.log("height", height)
        var data = [{x: 0, y: 0}, {x: width-30, y: 0}, {x: width, y: height}, {x: 0, y: height}]

        var curveFunc = d3.area()
            .x(function(d) { return d.x })      // Position of both line breaks on the X axis
            .y1(function(d) { return d.y })     // Y position of top line breaks
            .y0(200) 

        svg = d3.select(sectionID)
            .append("svg")
            .attr("width", sectionWidth)//the width value goes here
            .attr("height", height)//the height value goes here
        
        // Add the path using this helper function
        svg
            .append('path')
            .attr('d', curveFunc(data))
            .attr('stroke', backColor)
            .attr('fill', backColor);

        svg.append('text')
            .attr('x', '10')
            .attr('y', '20')
            .attr('text-anchor', 'right')
            .style("font-family", "Roboto,'Helvetica Neue',sans-serif")
            .style("font-size", "20px")
            .style("font-weight", "bold")
            .style('fill', '#fff')
            .text(title);

        // svg.append('line')
        //     .style("stroke", "#d3d3d3")
        //     .style("stroke-width", 2)
        //     .attr("x1", 0)
        //     .attr("y1", height)
        //     .attr("x2", sectionWidth)
        //     .attr("y2", height);
    }
}
