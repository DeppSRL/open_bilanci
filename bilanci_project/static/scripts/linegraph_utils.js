/**
 * Created by stefano on 3/21/14.
 */
/*
* linegraph_utils is a collection of js calls to draw in a div the linechart and adapt it
* to the page, even when resized
* */

"use strict";
var chart = visup.linechart(".timeline-multiline");
chart.options({
    timeline: {
        start: 2003,
        end: 2014,
        barPadding: 3,
        format: "%Y-%m-%d",
        visible: true
    },
    linechart: {
        height: 270,
        start: 2003,
        end: 2014,
        circleRadius: 9,
        axisUnit: "MILLION",
        tooltipUnit: "MLN",
        format: "%Y",
        visible: true
    },
    legend: {
        rowItems: 2
    }
});
$(document).ready(function(){

    //    adapt the chart to the page
    chart.resize();

    // binds the indicator menu toggle with the graph resize
    if($('#toggle-menu').length){
        $("#toggle-menu").on("click", function(){ chart.resize();});
    }

});

$(window).on('resize', function(){
    chart.resize();
});