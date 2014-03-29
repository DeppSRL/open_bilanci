/**
 * Created by stefano on 3/21/14.
 */
/*
* linegraph_utils is a collection of js calls to draw in a div the linechart and adapt it
* to the page, even when resized
*/

var linechart = null;

function init_linechart(){

    "use strict";
    linechart = visup.linechart(".timeline-multiline");

    linechart.options({
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

    // adapt the linechart to the page
    linechart.resize();

}

$(document).ready(function(){

    // binds the indicator menu toggle with the graph resize
    if($('#toggle-menu').length){
        $("#toggle-menu").on("click", function(){ linechart.resize();});
    }

    init_linechart();
    feed_linechart();
});

$(window).on('resize', function(){
    linechart.resize();
});