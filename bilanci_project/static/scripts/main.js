/**
 * Main scripts
 * @author mleone
 * @version 1.4.4
 **/

$(document).ready(function(){

    // Main vars
    var $window   = $(window),
        lock      = $( '#lock'),
        $sidebar  = $( '#sidebar' ),
        $content  = $( '#content' ),
        $results  = $( '#results' ),
        $comments = $( '#comments' );


    // Collapsible table
    function setupCollapsibleTable()
    {

        var tables   = $results.find( 'table' ),
            togglers = $results.find( '.collapse-toggle' ),
            panels   = $results.find( '.collapse' );

        panels.collapse({
            toggle: false
        });

        tables.find('.collapse').on('hidden.bs.collapse', function(){
            var panel = $(this);
            panel.prev().removeClass('shown');
        });

        tables.find('.collapse').on('shown.bs.collapse', function(){
            var panel = $(this);

            panel.siblings('.shown').removeClass('shown');
            panel.prev().addClass('shown');

            panel.siblings('.panel-heading').not( $('.shown') ).find('span.icon')
                    .removeClass('sprite-minus')
                    .addClass('sprite-plus');
        });

        togglers.on('click', function(e) {
            e.preventDefault();

            var toggler = $(this),
                target  = $(toggler.attr('href'));

            toggler.closest('tr').siblings('.panel-collapse').each(function(i, el){
                if ($(el).attr('id') !== target.attr('id')) {
                    $(el).collapse('hide');
                }
            });

            if (target.hasClass('in')) {
                target.collapse('hide');
                toggler.find('span.icon')
                    .removeClass('sprite-minus')
                    .addClass('sprite-plus');
            } else {
                target.collapse('show');
                toggler.find('span.icon')
                    .removeClass('sprite-plus')
                    .addClass('sprite-minus');
            }

            return false;

        });

        $results.find( '.more-info' ).on( 'click', function( e ){
            e.preventDefault();

            var btn = $( this ),
                trend = btn.parents( '.details' ).find( '.trend' );
            if (trend.hasClass('hidden')) {
                trend.removeClass( 'hidden' );
                btn.html( btn.data().close );
            } else {
                trend.addClass( 'hidden' );
                btn.html( btn.data().open );
            }

            return false;

        });

    }

    // Resize sidebar
    function resizeSidebar()
    {
        $sidebar.find('.scrollbox').enscroll({
            showOnHover: true,
            pollChanges: true,
            verticalTrackClass: 'track',
            verticalHandleClass: 'handle'
        });
    }

    // Sidebar menu
    function setUpMenu()
    {
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
    }

    // Settings menu
    function setUpSettingsMenu()
    {
        var $panel = $( "#settings" ),
            $opener = $panel.find( '.slider-arrow.show' ),
            $closer = $panel.find( '.slider-arrow.close' ),
            delta = $panel.width(),
            hook = $( 'h2.text-alt' ).first(),
            y =  hook.offset().top - hook.position().top - hook.height();

            console.log($( 'h2.text-alt' ).first(), delta, y);

        $panel.css('top', y).show('fast');

        $opener.on( 'click', function(e){
            e.preventDefault();
            $panel.animate({left: -2}, 400, function() {

            });
            $closer.removeClass('hidden');
            $opener.animate({right: 20}, 200);
        });

        $closer.on( 'click', function(e){
            e.preventDefault();
            $panel.animate({left: -1 * (delta + 20)}, 400, function() {
                $opener.animate({right: -50}, 200);
            });
            $closer.addClass('hidden');
        });

    }

    // Tooltips
    function setUpTooltips()
    {
        $('[data-toggle="tooltip"]').tooltip( {placement: 'right'} );
    }

    // Pie chart
    function setDonutChart(holder, cx, cy, radius, data)
    {
        cx = cx || 100;
        cy = cy || 100;
        radius = radius || 50;
        data = data || [];
        colors = ['#cccccc', '#cc6633'];
        overs = ['#cccccc', '#888888'];

        var ms = 500,
            r = Raphael(holder),
            p = r.piechart(cx, cy, radius, data, {
                init: true,
                colors: colors,
                stroke: 'none',
                donut: true,
                preserveValues: true,
                donutDiameter: 0.6
            });


        /*p.mouseover(function () {
            var node =  $( this.node );
            if (node.attr('fill') == colors[1]) {
                node.attr({
                    fill: overs[1],
                });
            }
            //p.stop().animate({transform: "s1.1 1.1 " + cx + " " + cy}, ms, "elastic");
        }).mouseout(function () {
            var node =  $( this.node );
            if (node.attr('fill') == overs[1]) {
                node.attr({
                    fill: colors[1],
                });
            }
            //p.stop().animate({transform: ""}, ms, "elastic");
        });
        */
    }

    function addChart()
    {
        $( '.chart' ).each( function(i, el) {
            var val1 =  parseInt( $( el ).data().chartValue ) / 100,
                val2 = 1 - val1;
            setDonutChart(el.id, 20, 20, 15, [val2, val1]);
        });
    }

    // App init
    function init()
    {
        setUpMenu();
        setUpTooltips();
        resizeSidebar();
        setupCollapsibleTable();
        setUpSettingsMenu();

        $window.load(function(){
            addChart();
        });
    }

    init();


});
