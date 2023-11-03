import { Component, OnInit, Input, ViewChild, ElementRef, ViewEncapsulation } from '@angular/core';
import * as d3 from 'd3';

const barWidth: number = 30;

@Component({
  selector: 'app-horizontal-barchart',
  templateUrl: './horizontal-barchart.component.html',
  styleUrls: ['./horizontal-barchart.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class HorizontalBarchartComponent implements OnInit {
    @ViewChild('chart', { static: true }) private chartContainer: ElementRef;
    @Input() inputdata: Array<any> = [];
    @Input() xAxisLabel: string = "";
    @Input() yAxisLabel: string = "";
    @Input() inBrowser: boolean = false;

    margin: any = { top: 30, bottom: 20, left: 50, right: 50};
    svg: any;
    chart: any;
    width: number;
    height: number;
    wholeChartWidth: number;
    xScale: any;
    yScale: any;
    colors: any;
    xAxis: any;
    yAxis: any;
    grid: any;
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
            return d3.ascending(a[3], b[3]);
        });

        let nbars = this.data.length;
        this.height = (nbars * barWidth);
        this.margin.left = this.calculateMarginForYScaleLabels();
    }

    /**
     * Calculate the max length of the y scale labels
     * @returns the max length of the y scale labels
     */
    calculateMarginForYScaleLabels() {
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
            maxTextWidth = Math.max(maxTextWidth, this.getComputedTextLength());
        }).remove();

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
            this.margin.left = this.calculateMarginForYScaleLabels();
            this.createChart();
            this.updateChart();
        }
    }

    /**
     * Sort the data by file name (4th column) and update the bar chart
     * @param event Sort option
     */
    sortBarChart(event) {
        var target = event.target;
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
                    return d3.ascending(a[3], b[3]);
                });

                this.updateChart();
                break; 
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
        this.wholeChartWidth = element_chart.offsetWidth - this.margin.right * 2;
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
        this.chartCleanup();    // Clean up existing grid lines

        this.grid = this.svg.append('g')
            .attr('class', 'x axis-grid')
            .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`)
            .attr("opacity",".1")
            .call(d3.axisTop(this.xScale.domain(xDomain).range([0, this.width]))
                    .tickSize(-this.height)
                    .tickFormat("")
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
            .attr('x', this.wholeChartWidth/2  + this.margin.right)
            .attr('y', this.margin.top-40)
            .attr('text-anchor', 'middle')
            .text(`${this.xAxisLabel}`);
    }

    /**
     * Update the bar chart and draw the bars
     */
    updateChart() {
        // update scales & axis
        // If the values of all bars are zero, we will set domain to [0, 1].
        // Otherwise, domain [0,0] will cause the chart unpredictible  
        let xMax = d3.max(this.data, d => d[1]);
        if(xMax == 0) {
            this.xScale.domain([0, 1]);
        }else{
            this.xScale.domain([0, xMax]);
        }
        
        this.yScale = d3.scaleBand().paddingInner(0.1);
        this.yScale.domain(this.data.map(d => d[0])).rangeRound([0, this.height]);
        
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
 
        // add new bars. Set with to 0 first. Then animate to actual width later.
        update
            .data(this.data)
            .enter()
            .append("g")
            .append('rect')
            .attr('class', 'bar')
            .attr('x', 0)
            .attr('y', d => this.yScale(d[0]))
            .attr('height', yScale.bandwidth())
            .attr('opacity', 1)
            // .attr('height', 10)
            .attr('width', 0) 
            .style('fill', (d, i) => this.colors(i))
            .on('mouseenter', function (event, actual) {
                d3.select(this)
                    .transition()
                    .duration(300)
                    .attr('opacity', 0.6)
                    .style('fill', '#00e68a')
            
                // draw a yellow dash line at the end of the active bar
                // line style is defined in line#limit
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
                    .style("left", event.pageX - 450 + "px")
                    .style("top", event.pageY - 120 + "px")
                    .style("display", "inline-block")
                    .html("<div style='width:100%; padding: 10px 10px 0px 10px;'> File path: "+(actual[2]) + "</div><div style='width:100%; padding: 0 10px 10px 10px;'>" + "Total Downloads: " + (actual[1]) + "</div>")
            })
            .on("mousemove", function (event, actual) {
                tooltip
                    .style("left", event.pageX - 50 + "px")
                    .style("top", event.pageY - 90 + "px");
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
            })

        // This is where we animate the bars to actual value.
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

        this.chart.selectAll(".label")
            .data(this.data)
            .attr('x', (d) => xScale(d[1])-30)
            .attr('y', (d) => yScale(d[0]) + yScale.bandwidth()*5/8)
            .attr('text-anchor', 'right')
            .style("font-size", "15px")
            .style('fill', '#fff')
            .text((d) => `${d[1]}`);
    }

    /**
     * Clean up chart for re-draw
     */
    chartCleanup(){
        if(this.svg){
            this.svg.selectAll('.axis-grid').remove();  
            this.svg.selectAll('.axis').remove();  
            this.svg.selectAll('.bar').remove();  
            this.svg.selectAll('.label').remove();  
            this.svg.selectAll('text').remove();  
        } 
    }

    /**
     * Save the bar chart as a png file
     */
    saveMetricsAsImage(filename: string = "Chart_Export.jpg"){
        var svgString = this.getSVGString(this.svg.node());
        this.svgString2Image( svgString, 2*this.width, 2*this.height, 'png', filename ); // passes Blob and filesize String to 
    }

    /**
     * Convert svg string to image
     * @param svgString 
     * @param width image width
     * @param height image height
     * @param format - image format, for example, 'png'
     */
    svgString2Image( svgString, width, height, format, filename: string = "Chart_Export.jpg" ) {
        var format = format ? format : 'png';
        var imgsrc = 'data:image/svg+xml;base64,'+ btoa( unescape( encodeURIComponent( svgString ) ) ); // Convert SVG string to data URL

        var canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;

        var context = canvas.getContext("2d");
        context.fillStyle = '#FFFFFF';  // Fill the background with white color

        var image = new Image();
        image.onload = function() {
            context.fillRect(0, 0, width, height);
            context.drawImage( image, 0, 0, width, height );
 
            try {
     
                // Try to initiate a download of the image
                var a = document.createElement("a");
                a.download = filename;
                a.href = canvas.toDataURL("image/jpeg");
                document.querySelector("body").appendChild(a);
                a.click();
                document.querySelector("body").removeChild(a);
     
            } catch (ex) {
     
                // If downloading not possible (as in IE due to canvas.toDataURL() security issue)
                // then display image for saving via right-click
     
                var imgPreview = document.createElement("div");
                imgPreview.appendChild(image);
                document.querySelector("body").appendChild(imgPreview);
     
            }
        };

        image.src = imgsrc;
    }

    /**
     * Convert svg to string
     * @param svgNode 
     * @returns svg string
     */
    getSVGString( svgNode ) {
        svgNode.setAttribute('xlink', 'http://www.w3.org/1999/xlink');
        var cssStyleText = this.getCSSStyles( svgNode );
        this.appendCSS( cssStyleText, svgNode );

        var serializer = new XMLSerializer();
        var svgString = serializer.serializeToString(svgNode);
        svgString = svgString.replace(/(\w+)?:?xlink=/g, 'xmlns:xlink='); // Fix root xlink without namespace
        svgString = svgString.replace(/NS\d+:href/g, 'xlink:href'); // Safari NS namespace fix

        return svgString;
    }

    /**
     * Get style sheet as a string
     * @param parentElement 
     * @returns style sheet string
     */
    getCSSStyles( parentElement ) {
        var selectorTextArr = [];

        // Add Parent element Id and Classes to the list
        selectorTextArr.push( '#'+parentElement.id );
        for (var c = 0; c < parentElement.classList.length; c++)
                if ( !this.contains('.'+parentElement.classList[c], selectorTextArr) )
                    selectorTextArr.push( '.'+parentElement.classList[c] );

        // Add Children element Ids and Classes to the list
        var nodes = parentElement.getElementsByTagName("*");
        for (var i = 0; i < nodes.length; i++) {
            var id = nodes[i].id;
            if ( !this.contains('#'+id, selectorTextArr) )
                selectorTextArr.push( '#'+id );

            var classes = nodes[i].classList;
            for (var c = 0; c < classes.length; c++)
                if ( !this.contains('.'+classes[c], selectorTextArr) )
                    selectorTextArr.push( '.'+classes[c] );
        }

        // Extract CSS Rules
        var extractedCSSText = "";
        for (var i = 0; i < document.styleSheets.length; i++) {
            // var s = document.styleSheets[i];
            var s = document.styleSheets[i];
            
            try {
                if(!(s as CSSStyleSheet).cssRules) continue;
            } catch( e ) {
                    if(e.name !== 'SecurityError') throw e; // for Firefox
                    continue;
                }

            var cssRules = (s as CSSStyleSheet).cssRules;
            for (var r = 0; r < cssRules.length; r++) {
                if ( this.contains( cssRules[r].cssText, selectorTextArr ) )
                    extractedCSSText += cssRules[r].cssText;
            }
        }
        

        return extractedCSSText;
    }

    /**
     * Check if a string contains another string
     * @param str searching string
     * @param arr string to be searched
     * @returns true if a string contains another string. False otherwise.
     */
    contains(str,arr) {
        return arr.indexOf( str ) === -1 ? false : true;
    }

    /**
     * Append a css text to an element
     * @param cssText 
     * @param element 
     */
    appendCSS( cssText, element ) {
        var styleElement = document.createElement("style");
        styleElement.setAttribute("type","text/css"); 
        styleElement.innerHTML = cssText;
        var refNode = element.hasChildNodes() ? element.children[0] : null;
        element.insertBefore( styleElement, refNode );
    }
}
