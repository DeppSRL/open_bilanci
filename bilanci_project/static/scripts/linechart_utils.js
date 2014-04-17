/**
 * Created by stefano on 3/21/14.
 */
/*
* linegraph_utils is a collection of js calls to draw in a div the linechart and adapt it
* to the page, even when resized
*/

var linechart = null;
var secondary_linechart = null;

function init_main_linechart(timeline_start_year, timeline_end_year, axisUnit, tooltipUnit){

    "use strict";
    linechart = visup.linechart(".timeline-multiline");

    // sets default values for Y axis value unit and tooltip value unit
    axisUnit = typeof axisUnit !== 'undefined' ? axisUnit : 'MILIONI';
    tooltipUnit = typeof tooltipUnit !== 'undefined' ? tooltipUnit : 'MLN';

    linechart.options({
        timeline: {
            start: timeline_start_year,
            end: timeline_end_year,
            barPadding: 3,
            format: "%Y-%m-%d",
            visible: true
        },
        linechart: {
            height: 270,
            start: timeline_start_year,
            end: timeline_end_year,
            circleRadius: 9,
            axisUnit: axisUnit,
            tooltipUnit: tooltipUnit,
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

function init_secondary_linechart(event){
    event.preventDefault();
    var timeline_start_year = event.data.timeline_start_year;
    var timeline_end_year = event.data.timeline_end_year;

    var btn = $( this );
    var chart_container = $('tr#trend-chart-container-' + btn.attr('id').split('-').pop());
    var chart_td = chart_container.find('td');
    var voce_slug = btn.attr('href').substring(1);

    if (chart_td.find('div').length == 0) {
        chart_td.append($("<div>").addClass("trend-chart"));
        secondary_linechart = visup.linechart("#" + chart_container.attr('id') + " .trend-chart");
        secondary_linechart.options({
                timeline: {
                    visible: false
                },
                linechart: {
                    height: 150,
                    start: timeline_start_year,
                    end: timeline_end_year,
                    circleRadius: 9,
                    axisUnit: "MILIONI",
                    tooltipUnit: "MLN",
                    format: "%Y",
                    visible: true
                },
                legend: {
                    rowItems: 2
                }
            });
        feed_secondary_linechart(voce_slug);
    }

    if (chart_container.hasClass('hidden')) {
        chart_container.removeClass( 'hidden' );
    } else {
        chart_container.addClass( 'hidden' );
    }

    return false;

    }


if(linechart){
    $(window).on('resize', function(){

    linechart.resize();
});
}
