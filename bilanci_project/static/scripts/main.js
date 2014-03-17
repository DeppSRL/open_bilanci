/**
 * Main scripts
 * @author mleone
 * @version 1.3.0
 **/

$(document).ready(function(){
    var $window = $(window),
        $sidebar = $( '#sidebar' ),
        $content = $( '#content' ),
        results  = $( '#results' ),
        togglers = results.find( '.collapse-toggle' ),
        panels   = results.find( '.collapse' );

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

    togglers.on('click', function(e) {
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

    });

    // resize sidebar
    function resizeSidebar() {
        $sidebar.find('.scrollbox').enscroll({
            showOnHover: true,
            pollChanges: true,
            verticalTrackClass: 'track',
            verticalHandleClass: 'handle'
        });
    }

    /*$window.load(function() {
        resizeSidebar();
    });

    $window.resize(function() {
        resizeSidebar();
    });*/

    resizeSidebar();


    $( '#toggle-menu' ).on( 'click', function( e ){
        e.preventDefault();

        var $this =  $( this ),
            clss = {
                btn: {
                    on: 'active'
                },
                content: {
                    on: 'col-sm-12',
                    off: 'col-sm-8 col-sm-push-4'
                },
                sidebar: {
                    on: 'col-sm-4 col-sm-pull-8',
                    off: 'hidden'
                }
            };

        if ( !$this.hasClass( clss.btn.on ) ) {
            $sidebar
                .removeClass( clss.sidebar.off )
                .addClass( clss.sidebar.on );
            $content
                .removeClass( clss.content.on )
                .addClass( clss.content.off );
            $this.addClass( clss.btn.on );
        } else {
            $sidebar
                .removeClass( clss.sidebar.on )
                .addClass( clss.sidebar.off );
            $content
                .removeClass( clss.content.off )
                .addClass( clss.content.on );
            $this.removeClass( clss.btn.on );
        }

    });

});
