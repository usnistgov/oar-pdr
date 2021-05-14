import { Component, OnInit, Input, ViewChild, ElementRef, ViewEncapsulation } from '@angular/core';
import * as d3 from 'd3';
import { saveSvgAsPng } from 'save-svg-as-png';

const barWidth: number = 30;

@Component({
  selector: 'app-horizontal-barchart',
  templateUrl: './horizontal-barchart.component.html',
  styleUrls: ['./horizontal-barchart.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class HorizontalBarchartComponent implements OnInit {
    @ViewChild('chart') private chartContainer: ElementRef;
    @Input() inputdata: Array<any> = [];
    @Input() chart_title: string = "";
    @Input() xAxisLabel: string = "";
    @Input() yAxisLabel: string = "";
    @Input() inBrowser: boolean = false;

    margin: any = { top: 60, bottom: 20, left: 50, right: 50};
    svg: any;
    chart: any;
    width: number;
    height: number;
    xScale: any;
    yScale: any;
    colors: any;
    xAxis: any;
    yAxis: any;
    data: Array<any>;
    sortitem: string = '3';

    constructor() { }

    ngOnInit() {
        if(this.inBrowser){
            this.initData();
            this.chart.exit().remove();

            this.createChart();
            if (this.data) {
                this.updateChart();
            }
        }
    }

    /**
     * Make a deep copy of input data and sort alphabetically
     * Then calculate the actual height of the chart and the left margin based on the max length of the labels
     */
    initData(){
        this.data = JSON.parse(JSON.stringify(this.inputdata));
        this.data = this.data.sort(function(a, b) {
            return d3.ascending(a[0], b[0]);
        });

        let nbars = this.data.length;
        this.height = (nbars * barWidth);
        this.margin.left = this.calculateMarginForYScaleTicks();
        console.log('this.margin.left', this.margin.left);
    }

    /**
     * Calculate the max length of the y scale ticks
     * @returns the max length of the y scale ticks
     */
    calculateMarginForYScaleTicks() {
        var maxTextWidth = 0;
        let element_chart = this.chartContainer.nativeElement;

        if(this.svg){
            this.svg = d3.select(element_chart).select('svg')
            .attr('width', 0)
            .attr('height', 0);
        }else{
            this.svg = d3.select(element_chart).append('svg')
            .attr('width', 0)
            .attr('height', 0);
        }
    
        // chart plot area
        this.chart = this.svg.append('g')
            .attr('class', 'bars')
            .attr('transform', `translate(0, 0)`);

        let label = this.chart.selectAll(".label").data(this.data);

        label.exit().remove();
        label.enter().append("text").attr("class", "label");

        this.chart.selectAll(".label").data(this.data)
            .attr('x', 0)
            .attr('y', 0)
            .text((d) => `${d[1]}`);

        var maxTextWidth = 0;
        var labels = this.chart.selectAll(".label").data(this.data).text((d) => `${d[0]}`);
        labels.each(function() {
            // console.log(this.getComputedTextLength());
            maxTextWidth = Math.max(maxTextWidth, this.getComputedTextLength());
        }).remove();

        // d3.selectAll("svg").remove();
        // this.svg.remove();

        return maxTextWidth;
    }

    /**
     * On change, update the chart
     */
    ngOnChanges() {
        if (this.chart && this.inBrowser) {
            this.initData();
            this.updateChart();
        }
    }

    /**
     * On screen resize, re-draw the chart
     */
    onResize(){
        if (this.inBrowser) {
            this.svg.remove();
            this.createChart();
            this.updateChart();
        }
    }

    /**
     * Sort the data and update the bar chart
     * @param event Sort option
     */
    sortBarChart(event) {
        if (this.inBrowser) {
            var target = event.target;
            console.log("target", target);

            switch(target.value) { 
                case '1': { 
                    this.data = this.data.sort(function(a, b) {
                        return d3.ascending(a[1], b[1])
                    });

                    this.updateChart();

                    break; 
                } 
                case '2': { 
                    this.data = this.data.sort((a, b) => d3.descending(a[1], b[1]));

                    this.updateChart();

                    break; 
                } 
                default: { 
                    this.data = JSON.parse(JSON.stringify(this.inputdata));
                    this.data = this.data.sort(function(a, b) {
                        return d3.ascending(a[0], b[0]);
                    });

                    this.updateChart();
                    break; 
                } 
            } 
        }
    }

    /**
     * Create the bar chart (without bar yet)
     * We separate the create chart and update chart so that when user changes the order of the data
     * we don't need to re-draw some part of the chart
     */
    createChart() {
        if(this.svg)
            this.svg.exit().remove;

        let element_chart = this.chartContainer.nativeElement;
        this.width = element_chart.offsetWidth - this.margin.left - this.margin.right;

        if(this.svg){
            this.svg = d3.select(element_chart).select('svg')
            .attr('width', element_chart.offsetWidth)
            .attr('height', this.height + this.margin.top + this.margin.bottom);
        }else{
            this.svg = d3.select(element_chart).append('svg')
            .attr('width', element_chart.offsetWidth)
            .attr('height', this.height + this.margin.top + this.margin.bottom);
        }
   
        // chart plot area
        this.chart = this.svg.append('g')
            .attr('class', 'bars')
            .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);
    
        // define X & Y domains
        let xMax = d3.max(this.data, d => d[1]);
        if(xMax == 0) xMax = 1;

        let xDomain = [0, xMax];
        let yDomain = this.data.map(d => d[0]);
    
        // create scales
        this.xScale = d3.scaleLinear();

        this.yScale = d3.scaleBand()
                        .padding(0.1);
    
        // bar colors (use only one color at this time)
        this.colors = d3.scaleLinear().domain([0, this.data.length]).range(<any[]>['#257a2d', '#257a2d']);

        // Draw grid lines
        this.svg.append('g')
            .attr('class', 'x axis-grid')
            .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`)
            .attr("opacity",".1")
            .call(d3.axisTop(this.xScale.domain(xDomain).range([0, this.width]))
                    .tickSize(-this.height)
                    .tickFormat(null)
                    .ticks(5));
            
        // x & y axis
        this.xAxis = this.svg.append('g')
            .attr('class', 'x axis')
            .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`)
            .call(d3.axisTop(this.xScale.domain(xDomain).range([0, this.width])).ticks(5));

        this.yAxis = this.svg.append('g')
            .attr('class', 'y axis')
            .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`)
            .call(d3.axisLeft(this.yScale.domain(yDomain).rangeRound([0, this.height])));

        // x and y axis labels
        this.svg.append('text')
            .attr('x', -(this.height / 2) - this.margin.top)
            .attr('y', this.margin.left / 3.0)
            .attr('transform', 'rotate(-90)')
            .attr('text-anchor', 'middle')
            .text(`${this.yAxisLabel}`);

        this.svg.append('text')
            .attr('x', this.width / 2 + this.margin.left)
            .attr('y', this.margin.top-40)
            .attr('text-anchor', 'middle')
            .text(`${this.xAxisLabel}`);
    }

    /**
     * Update the bar chart and draw the bars
     */
    updateChart() {
        console.log("Updating chart...");
        // update scales & axis
        // If the values of all bars are zero, we will set domain to [0, 1].
        // Otherwise, domain [0,0] will cause the chart unpredictible  
        let xMax = d3.max(this.data, d => d[1]);
        if(xMax == 0) {
            this.xScale.domain([0, 1]);
        }else{
            this.xScale.domain([0, xMax]);
        }
        
        // let xDomain = [0, d3.max(this.data, d => d[1])];
        // let yDomain = this.data.map(d => d[0]);
        this.yScale.domain(this.data.map(d => d[0]));
        
        this.xAxis.transition().call(d3.axisTop(this.xScale).ticks(5));
        this.yAxis.transition().call(d3.axisLeft(this.yScale));

        let xScale = this.xScale;
        let yScale = this.yScale;
        let height = this.height;
        let chart = this.chart;

        var tooltip = d3.select("body").append("div").attr("class", "toolTip");

        let update = this.chart.selectAll('.bar');

        // remove exiting bars
        update.exit().remove();
 
        // add new bars
        update
            .data(this.data)
            .enter()
            .append("g")
            .append('rect')
            .attr('class', 'bar')
            .attr('x', 0)
            .attr('y', d => this.yScale(d[0]))
            .attr('height', this.yScale.bandwidth())
            .attr('width', 0)   // set with to 0 first. Then animate to actual width later.
            .style('fill', (d, i) => this.colors(i))
            .on('mouseenter', function (actual, i) {
                d3.select(this)
                    .transition()
                    .duration(300)
                    .attr('opacity', 0.6)
                    .style('fill', '#00e68a')
            
                chart.append('line')
                    .attr('id', 'limit')
                    .attr('x1', xScale(actual[1]))
                    .attr('y1', 0)
                    .attr('x2', xScale(actual[1]))
                    .attr('y2', height)
                    .attr('stroke', 'red')
            
                d3.selectAll('.label')
                  .filter(function(d) { return d[0] == actual[0]; })
                  .attr('opacity', 1)
                  .style('fill', '#000')

                tooltip
                    .style("left", d3.event.pageX - 50 + "px")
                    .style("top", d3.event.pageY - 90 + "px")
                    .style("display", "inline-block")
                    .html("<div style='width:100%; padding: 10px;'> File name: "+(actual[0]) + "</div><div style='padding-bottom: 10px'>" + "Total Times of Downloads: " + (actual[1]) + "</div>");
            })
            .on("mousemove", (actual) => {
                tooltip
                    .style("left", d3.event.pageX - 50 + "px")
                    .style("top", d3.event.pageY - 90 + "px");
            })
            .on('mouseleave', function () {
                d3.selectAll('.label')
                  .attr('opacity', 1)
                  .style('fill', '#fff')
        
                d3.select(this)
                .transition()
                .duration(300)
                .attr('opacity', 1)
                .style('fill', '#257a2d')
        
                chart.selectAll('#limit').remove()
                tooltip.html(``).style('display', 'none');
            });

        this.chart.selectAll('rect')
            .transition()
            .duration(200)
            .attr("x", 0)
            .attr('width', d => this.xScale(d[1]) < 0 ? 0 : this.xScale(d[1]))
            .delay(function(d,i){return(i*10)});

        // Display bar value
        let label = this.chart.selectAll(".label").data(this.data);

        label.exit().remove();
        label.enter().append("text").attr("class", "label");

        this.chart.selectAll(".label").data(this.data)
            .attr('x', (d) => xScale(d[1])-30)
            .attr('y', (d) => yScale(d[0]) + yScale.bandwidth()*5/8)
            .attr('text-anchor', 'right')
            .style("font-size", "15px")
            .style('fill', '#fff')
            .text((d) => `${d[1]}`);
    }


    saveMetricsAsImage(){
        if(this.inBrowser)
            saveSvgAsPng(document.getElementsByTagName("svg")[0], "plot.png", {scale: 2, backgroundColor: "#FFFFFF"});

        // var svgString = this.getSVGString(this.svg.node());
        // this.svgString2Image( svgString, 2*this.width, 2*this.height, 'png' ); // passes Blob and filesize String to 
    }

}
