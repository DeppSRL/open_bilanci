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
          heading.find('.trend-chart-toggle').addClass('hidden');
            // hide graph
            heading.parent().find('.chart-container.in').collapse('hide');

        }).on('show.bs.collapse', '.panel-collapse', function (e) {
            e.stopPropagation();
            var heading = $('#heading-' + $(this).attr('id'));
            // replace plus with minus
            heading.find('.entry .collapse-toggle').css({
                'font-weight': 'bold',
                'text-decoration': 'none'
            });
            // add bold style
            heading.find('.fa-plus-circle').removeClass('fa-plus-circle').addClass('fa-minus-circle');
            // show secondary line chart button
          heading.find('.trend-chart-toggle').removeClass('hidden');
        });

    // add graph toggler
    panels_tree.on('click', '.trend-chart-toggle', function(e) {
        e.preventDefault();
    });

    // auto open accordion
    if ( startElement != undefined ) {
        // expand parents if exists
        $(startElement, panels_tree).parents('.collapse').collapse('show');
        $(startElement, panels_tree).collapse('show');
    }
};

