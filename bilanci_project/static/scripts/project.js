/* Project specific Javascript goes here. */

!function($){
    var isVisible = false;
    var hideAllPopovers = function() {
       $('a[rel=info-popover]').each(function() {
            $(this).popover('hide');
        });
    };

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
        $('a[rel=info-popover]').popover({
            trigger: 'manual'
        }).on('click', function(e) {
            // if any other popovers are visible, hide them
            if(isVisible) {
                hideAllPopovers();
            }
            $(this).popover('show');

            // handle clicking on the popover itself
            $('.popover').off('click').on('click', function(e) {
                e.stopPropagation(); // prevent event for bubbling up => will not get caught with document.onclick
            });

            isVisible = true;
            e.stopPropagation();
            return false;
        });
        // close all popovers on document click
        $(document).on('click', function(e) {
            hideAllPopovers();
            isVisible = false;
        });

        // enable nested accordion
        setupNestedAccordion();
    });
}(jQuery);


var setupNestedAccordion = function(startElement) {

    var panels_tree = $('.panel-tree');

    // add sub collapse ( first level close its sub-tree)
    panels_tree
        .on('hidden.bs.collapse', '> .panel > .panel-collapse', function (e) {
            e.stopPropagation();
            $(this).find('.panel-collapse.in').collapse('hide');
        });

    // panels toggling
    panels_tree
        .on('hidden.bs.collapse', '.chart-container', function(e){
            e.stopPropagation()
        })
        .on('show.bs.collapse', '.chart-container', function(e){
            e.stopPropagation()
        });

    panels_tree

        .on('hidden.bs.collapse', '.panel-collapse', function (e) {
            e.stopPropagation();
            var heading = $('#heading-' + $(this).attr('id'));
            // replace minus with plus
            heading.find('.fa-minus-circle').removeClass('fa-minus-circle').addClass('fa-plus-circle');

            // remove bold style
            heading.find('.entry .collapse-toggle').css({
                'font-weight': 'inherit',
                'text-decoration': 'none'
            });
            // hide secondary line chart button
//          heading.find('.trend-chart-toggle').addClass('hidden');
            // hide graph
            heading.parent().find('.chart-container.in').collapse('hide');

        }).on('show.bs.collapse', '.panel-collapse', function (e) {
            e.stopPropagation();
            var heading = $('#heading-' + $(this).attr('id'));
            // replace plus with minus
            heading.find('.entry .collapse-toggle').css({
                'font-weight': 'bold',
                'text-decoration': 'underline'
            });
            // add bold style
            heading.find('.fa-plus-circle').removeClass('fa-plus-circle').addClass('fa-minus-circle');
            // show secondary line chart button
//          heading.find('.trend-chart-toggle').removeClass('hidden');
        });

    // add graph toggler
    panels_tree.on('click', '.trend-chart-toggle', function(e) {
        e.preventDefault();
    });

    // auto open accordion
    if ( startElement != undefined ) {
        $(startElement).collapse('show');
    }
};

