
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


function init_selector(default_year, selected_year, visible_buttons, selected_button_label, reference_url){
    "use strict";
    year_selector = visup.selector(".year-selector");
    var selected_button=null;

    // defines default values for the function parameters
    if(typeof(visible_buttons)==='undefined' || visible_buttons == null ) visible_buttons = false;
    if(typeof(selected_year)==='undefined'  || selected_year == null) selected_year = default_year;
    if(typeof(selected_button_label)==='undefined' || selected_button_label == null) selected_button_label = 'PREVENTIVO';

    //sets the selected button of the yr selector based on selected button label
    if(visible_buttons == true){
        selected_button_label = selected_button_label.toUpperCase();
        if(selected_button_label == 'PREVENTIVO')
            selected_button = 'button1';
        else
            selected_button = 'button2';

    }



    /*
    * different init_struct: one with buttons for entrate/spese and one without buttons for classifiche
    * */
    var init_struct_buttons = {
            padding: {
                left: 40,
                right: 240
            },
            timeline: {
                start: 2003,
                end: 2013,
                circleRadius: 11,
                defaultYear: selected_year
            },
            buttons: {
                button1: "PREVENTIVO",
                button2: "CONSUNTIVO",
                selected: selected_button,
                visible: visible_buttons
            },
            colors: {
                base: "#c6d1cf",
                selected: "#cc6633"
            }
        };

    var init_struct_no_buttons = {
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
                button1: "PREVENTIVO",
                button2: "CONSUNTIVO",
                selected: selected_button,
                visible: visible_buttons
            },
            colors: {
                base: "#c6d1cf",
                selected: "#cc6633"
            }
        };


    var init_struct;
    if(visible_buttons == true)
        init_struct = init_struct_buttons;
    else
        init_struct = init_struct_no_buttons;

    //initialize the selector
    year_selector.options(init_struct);

    //    adapt the year_selector to the page
    year_selector.resize();

    //when year is selected, navigate to the new page
    year_selector.on("clickYear", function(selected_year){
        // gets the 4 digits in the reference url representing the year value and substitutes
        //  it with the selected year value
        window.location.href = reference_url.replace(/[-\d]{4}/,String(selected_year));
    } );



    function clicked_button(){
        // if we are seeing preventivo navigates to consuntivo and viceversa
        var destination_bilancio_type = '';
        var re = /type=([\w]+)$/;

        var actual_bilancio_type = reference_url.match(re)[1].toLowerCase();
        if(actual_bilancio_type=='preventivo')
            destination_bilancio_type = 'consuntivo';
        else
           destination_bilancio_type = 'preventivo';

        window.location.href = reference_url.replace(re,'type='+destination_bilancio_type);

    }
    //if we are using buttons, binds the un-selected button with the callback function on the click event.
    // ie: if the Preventivo page is viewed and the user clicks Consuntivo -> the app navigates to the Consuntivo page

    if(visible_buttons){
        if(selected_button == 'button1')
            year_selector.on("clickButton2", clicked_button);
        else
            year_selector.on("clickButton1", clicked_button);
    }



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