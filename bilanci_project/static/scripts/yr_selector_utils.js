
/**
 * Created by stefano on 3/26/14.
 */
/*
* yr selector utils is a collection of js calls to draw in a div the yr widget and adapt it
* to the page, even when resized
* */

var year_selector = null;

function xfunct(y){
    alert(y);
}

function init_selector(default_year, selected_year, visible_buttons, selected_button, reference_url){
    "use strict";
    year_selector = visup.selector(".year-selector");

    // defines default values for the function parameters
    if(typeof(visible_buttons)==='undefined') visible_buttons = false;
    if(typeof(selected_year)==='undefined') selected_year = default_year;
    if(typeof(selected_button)==='undefined') selected_button = 'preventivo';


    var init_struct = {
        padding: {
            left: 40,
            right: 40
        },
        timeline: {
            start: 2003,
            end: 2013,
            circleRadius: 11,
            defaultYear: selected_year
        },
        buttons: {
            preventivo: "PREVENTIVO",
            consuntivo: "CONSUNTIVO",
            selected: selected_button,
            visible: visible_buttons
        },
        colors: {
            base: "#c6d1cf",
            selected: "#cc6633"
        }
    };

    //initialize the selector
    year_selector.options(init_struct);

    //    adapt the year_selector to the page
    year_selector.resize();

    //when year is selected, navigate to the new page
    year_selector.on("clickYear", function(selected_year){
        window.location.href = reference_url.replace(/[-\d]+$/,String(selected_year));
    } );

}


$(document).ready(function(){

    // binds the indicator menu toggle with the graph resize
    if($('#toggle-menu').length){
        $("#toggle-menu").on("click", function(){ year_selector.resize();});
    }

});

$(window).on('resize', function(){
    year_selector.resize();
});