/* Project specific Javascript goes here. */

!function($){

    $(document).ready(function(){
        // Fix input element click problem
        // http://mifsud.me/adding-dropdown-login-form-bootstraps-navbar/
        $('.dropdown input, .dropdown label').click(function(e) {
            e.stopPropagation();
        });

        $(".autosubmit input, .autosubmit select").on("change", function() {
            $(this).parents('form:first').submit();
        });

        // enable popovers
        $('a[rel=info-popover]').popover().on('click', function(e) {
            e.preventDefault();
        });
        // close all popovers on document click
        $('body').on('click', function (e) {
            $('[data-toggle="popover"]').each(function () {
                //the 'is' for buttons that trigger popups
                //the 'has' for icons within a button that triggers a popup
                if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
                    $(this).popover('hide');
                }
            });
        });

        $('.checkbox-toggler').on('click', function() {
            var $this = $(this);
            $this.parent().parent().find('input[type=checkbox]').not($this).prop('checked', $this.prop('checked'));
        });

        $('.dropdown-menu input, .dropdown-menu label').click(function(e) {
            e.stopPropagation();
        });




    });
}(jQuery);

var autoOpenNestedAccordion = function (startElement) {

    // auto open accordion
    if (startElement != undefined) {

        // turn the parent toggle element icon from "+" to "-" as the accordion is going to be expanded
        var parent_toggle_icons = $(startElement).parents('.collapse').prev('.panel').find('.panel-heading .row .entry a i');
        parent_toggle_icons.removeClass('fa-plus-circle');
        parent_toggle_icons.addClass('fa-minus-circle');
        parent_toggle_icons.css('color','rgb(143, 151, 158)');

        // expand parents if exists
        $(startElement).parents('.collapse').collapse('show');
        $(startElement).collapse('show');
        $(startElement + '> .row').addClass('highlighted');
    }

};

function goToClassByScroll(classname){
      // Scroll
    $('html,body').animate({
        scrollTop: $("."+classname).offset().top},
        'slow');
}

function goToIdByScroll(div_id){
      // Scroll

    if($(div_id).offset() != undefined){
        $('html,body').animate({
            scrollTop: $(div_id).offset().top-100},
            'slow');
    }

}

//escapes a string to be used in a regex
function escapeRegExp(str) {
  return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
}

function init_parameter_menu(site_section){
    //initialize side menu for classifiche / confronti
    // default selected value: the one present in the url address

    var parameter_type=null;
    var dropdown_id = '#'+site_section+'-dropdown';

    //if site_section is 'classifiche' the par type is whatever comes after classifiche in the page url:
    //given the url : classifiche/indicatori/foo -> par_type = indicatori
    var address_split = window.location.pathname.split('/');

    if(site_section == 'classifiche')
        parameter_type = address_split[2];
    else
        parameter_type = address_split[4];

    var par_type_id = '#pl-'+parameter_type;

    // on module load is selected the type of parameter present in the page url
    $('.pl-list').hide();
    $(par_type_id).show(0,function() {
        $(par_type_id).children().show();
        $(dropdown_id).val(parameter_type);
    });

    // binds the selector dropdown change to hide / show parameter lists
      $(dropdown_id).change(function() {

        var selected_element = '#pl-' + $(this).val();
        $('.pl-list').hide(0,function() {
            $(selected_element).children().show(0);
        });
        $(selected_element).show(0,function() {
            $(selected_element).children().show(0);
        });

     });
}
