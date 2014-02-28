/**
 * Main scripts
 * @author mleone
 * @version 1.1
 **/

$(document).ready(function(){
    var results  = $('#results'),
        togglers = results.find('.collapse-toggle'),
        panels   = results.find('.collapse');

    panels.collapse({
        toggle: false
    });

    results.find('.collapse').on('hidden.bs.collapse', function(){
        var panel = $(this);
        panel.prev().removeClass('shown');
    });

    results.find('.collapse').on('shown.bs.collapse', function(){
        var panel = $(this);
        panel.siblings('.shown').removeClass('shown');
        panel.prev().addClass('shown');
    });

    function collapseElement(e){
        e.preventDefault();

        var toggler = $(this),
            target = $(toggler.attr('href'));

        toggler.closest('tr').siblings('.panel-collapse').each(function(i, el){
            if ($(el).attr('id') !== target.attr('id')) {
                $(el).collapse('hide');
            }
        });


        if (target.hasClass('collapse')) {
            target.collapse('show');
            //toggler.closest('tr').addClass('shown');
            toggler.find('span.glyphicon')
                .removeClass('glyphicon-plus-sign')
                .addClass('glyphicon-minus-sign');
        } else {
            target.collapse('hide');
            //toggler.closest('tr').removeClass('shown');
            toggler.find('span.glyphicon')
                .removeClass('glyphicon-minus-sign')
                .addClass('glyphicon-plus-sign');
        }

    }

    togglers.on('click', collapseElement);

});
