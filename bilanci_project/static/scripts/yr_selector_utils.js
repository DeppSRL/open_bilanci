
/**
 * Created by stefano on 3/26/14.
 */
/*
* yr selector utils is a collection of js calls to draw in a div the yr widget and adapt it
* to the page, even when resized
* */

var year_selector = null;
var year_selector_mobile = null;
var reference_url = null;

function clicked_year(selected_year){
    // gets the 4 digits in the reference url representing the year value and substitutes
    //  it with the selected year value
    var navigate_to_url;
    var separator='/';
    var split_path = window.location.pathname.split(separator);

    //  determines the path to which the page will navigate:
    // classifiche page has a different url compared to bilancio pages in which the selector is used
    if(split_path[1] == 'classifiche'){

        split_path[4]=selected_year;
        navigate_to_url = split_path.join(separator) + window.location.search;
    }
    else{
        navigate_to_url = window.location.href.replace(/year=[-\d]{4}/,"year=" + String(selected_year));
    }

    window.location.href = navigate_to_url;

}

function clicked_year_mobile(){
    //calls clicked yr when the mobile select box is clicked
    //giving the selected yr as a parameter
    clicked_year(year_selector_mobile.val());
}


function clicked_button(){
    // if we are seeing preventivo navigates to consuntivo and viceversa
    var destination_bilancio_type = '';
    var re = /type=([\w]+)?/;

    var actual_bilancio_type = reference_url.match(re)[1].toLowerCase();
    if(actual_bilancio_type=='preventivo')
        destination_bilancio_type = 'consuntivo';
    else
       destination_bilancio_type = 'preventivo';

    window.location.href = window.location.href.replace(re,'type='+destination_bilancio_type);

}


function init_selector(selector_init_obj){
    "use strict";
    var selector_default_year = selector_init_obj['default_year'];
    var selected_year = selector_init_obj['selected_year'];
    var visible_buttons = selector_init_obj['visible_buttons'];
    var selected_bilancio_type = selector_init_obj['selected_bilancio_type'];
    var start_year = selector_init_obj['start_year'];
    var end_year  = selector_init_obj['end_year'];
    reference_url = selector_init_obj['reference_url'];
    var selected_button=null;
    var selected_button_label = null;

    year_selector = visup.selector(".year-selector");
    year_selector_mobile = $(".year-selector-mobile");


    // defines default values for the function parameters
    if(typeof(visible_buttons)==='undefined' || visible_buttons == null ) visible_buttons = false;
    if(typeof(selected_year)==='undefined'  || selected_year == null) selected_year = selector_default_year;
    if(typeof(selected_button_label)==='undefined' || selected_button_label == null) selected_button_label = 'PREVENTIVO';

    //sets the selected button of the yr selector based on selected button label
    if(visible_buttons == true){

        selected_button_label=selected_bilancio_type.toUpperCase();
        if(selected_button_label == 'PREVENTIVO')
            selected_button = 'button1';
        else
            selected_button = 'button2';

    }

    /*
    * selector init array
    * */
    var selector_init_array = {
        padding: {
            left: 0,
            right: 0
        },
        barPadding: 1,
        timeline: {
            start: start_year,
            end: end_year,
            circleRadius: 6,
            defaultYear: selected_year
        },
        buttons: {
            button1: "PREVENTIVO",
            button2: "CONSUNTIVO",
            selected: selected_button,
            visible: visible_buttons,
            head: "Scegli il bilancio"
        },
        colors: {
            base: "#c6d1cf",
            selected: "#cc6633"
        }
    };


    //initialize the selector
    year_selector.options(selector_init_array);

    //    adapt the year_selector to the page
    year_selector.resize();


    //when year is selected, navigate to the new page
    year_selector.on("clickYear",clicked_year);
    year_selector_mobile.on("change",clicked_year_mobile);


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
    if($('#push-menu').length && year_selector){
        $("#push-menu").on("click", function(){ year_selector.resize();});
    }

});

if(year_selector){
    $(window).on('resize', function(){
    year_selector.resize();
});
}
