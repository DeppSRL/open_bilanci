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
