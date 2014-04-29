/**
 * Main scripts
 * @author mleone
 * @version 1.4.6
 **/

$(document).ready(function(){

    // Main vars
    var dev       = false,
        scroll    = false,
        $window   = $(window),
        $lock     = $( '#lock' ),
        $sidebar  = $( '#sidebar' ),
        $content  = $( '#content' ),
        $results  = $( '#results' ),
        $comments = $( '#comments' ),
        $controls = $( '#side-controls' ),
        $hook     = $( 'h2.text-alt' ).first();

    // Collapsible table
    function setupCollapsibleTable()
    {

        var tables   = $results.find( 'table' ),
            togglers = $results.find( '.collapse-toggle' ),
            panels   = $results.find( '.collapse' );

        panels.collapse({
            toggle: false
        });

        tables.find( '.collapse' ).on( 'hidden.bs.collapse', function(){
            var panel = $(this);
            panel.prev().removeClass( 'shown' );
            $lock.modal( 'hide' );
        });

        tables.find( '.collapse' ).on( 'shown.bs.collapse', function(){
            var panel = $(this);
            var panel_id = panel[0].id;

            panel.siblings( '.shown' ).removeClass( 'shown' );
            panel.prev().addClass( 'shown' );

            //finds sibling who are already expaneded and changes icon minus to icon plus
            panel.siblings('.panel-heading').not("#heading-"+panel_id).find('span.sprite-minus')
                .removeClass( 'sprite-minus' ).addClass( 'sprite-plus' );

            $lock.modal( 'hide' );
        });

        togglers.on( 'click', function(e) {
            e.preventDefault();
            $lock.modal( 'show' );

            var toggler = $(this),
                target  = $(toggler.attr( 'href' ));

            toggler.closest( 'tr' ).siblings( '.panel-collapse' ).each(function(i, el){
                if ($(el).attr( 'id' ) !== target.attr( 'id' )) {
                    $(el).collapse( 'hide' );
                }
            });

            if (target.hasClass( 'in' )) {
                target.collapse( 'hide' );
                toggler.find( 'span.icon' )
                    .removeClass( 'sprite-minus' )
                    .addClass( 'sprite-plus' );
            } else {
                target.collapse( 'show' );
                toggler.find( 'span.icon' )
                    .removeClass( 'sprite-plus' )
                    .addClass( 'sprite-minus' );
            }

        });

        $results.find( '.more-info' ).on( 'click', function( e ){
            e.preventDefault();

            var btn = $( this ),
                trend = btn.parents( '.details' ).find( '.trend' );
            if (trend.hasClass( 'hidden' )) {
                trend.removeClass( 'hidden' );
                btn.html( btn.data().close );
            } else {
                trend.addClass( 'hidden' );
                btn.html( btn.data().open );
            }
        });

    }

    // Resize sidebar
    function resizeSidebar()
    {
        $sidebar.find( '.scrollbox' ).enscroll({
            showOnHover: true,
            pollChanges: true,
            verticalTrackClass: 'track',
            verticalHandleClass: 'handle'
        });
    }

    // Push menu
    function setupPushMenu()
    {
        var $opener = $( '#push-menu' ),
            $closer = $( '#hide-menu' ),
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

        $opener.on( 'click', function( e ){
            e.preventDefault();
            $controls.animate({ left: -50 }, 200);

            $sidebar
                .removeClass( clss.sidebar.off )
                .addClass( clss.sidebar.on );
            $content
                .removeClass( clss.content.on )
                .addClass( clss.content.off );

        });

        $closer.on( 'click', function( e ){
            e.preventDefault();
            $controls.animate({ left: -2 }, 200);

            $sidebar
                .removeClass( clss.sidebar.on )
                .addClass( clss.sidebar.off );
            $content
                .removeClass( clss.content.off )
                .addClass( clss.content.on );
        });

        $sidebar.find( '.panel-collapse' ).on( 'click', function(e){
            e.preventDefault();
            var $toggler = $( this ),
                $submenu = $toggler.next(),
                $pin =  $toggler.prev(),
                selected = $submenu.find( 'input:checked' ).length;

            if ( $toggler.hasClass( 'collapse' ) ) {
                $submenu.removeClass( 'hidden' );
                $toggler.removeClass( 'collapse' );
            } else {
                $submenu.addClass( 'hidden' );
                $toggler.addClass( 'collapse' );
            }

            if (selected > 0) {
                $pin.removeClass( 'hidden' );
            } else {
                $pin.addClass( 'hidden' );
            }
        });
    }

    // Settings menu
    function setupSettingsMenu()
    {
        var $panel = $( '#settings' ),
            $opener = $( '#open-settings' ),
            $closer = $( '#hide-settings' ),
            delta = $panel.width(),
            y = ( $hook.length > 0 ? $hook.offset().top - $hook.position().top - $hook.height() : 30 );

        $panel.css( 'top', y ).show( 'fast' );

        $opener.on( 'click', function(e){
            e.preventDefault();
            $panel.animate({ left: 4 }, 400);
            $controls.animate({ left: -50 }, 200);
        });

        $closer.on( 'click', function(e){
            e.preventDefault();
            $panel.animate({ left: -1 * (delta + 20) }, 400, function() {
                $controls.animate({ left: -2 }, 200);
            });

        });

    }

    // Side controls
    function setupSideControls()
    {
        var y = ( $hook.length > 0 ? $hook.offset().top - $hook.position().top - $hook.height() : 30 );

        $controls.css( 'top', y ).show( 'fast' );
        setupPushMenu();
        setupSettingsMenu();

        if (scroll) {
            y = 30;

            $window.on( 'scroll', function() {
                var offset = y + $window.scrollTop();
                if ( $window.scrollTop() == y + $controls.height() ) {
                    offset = $window.scrollTop() - y;
                } else {
                    offset = y;
                }
                $controls.css( 'top', offset );
            });
        }
    }

    // Tooltips
    function setupTooltips()
    {
        $( '[data-toggle="tooltip"]' ).tooltip( {placement: 'right', container: 'body'} );
    }

    // Donut chart
    function setDonutChart(holder, cx, cy, radius, scale, data)
    {
        cx = cx || 100;
        cy = cy || 100;
        radius = radius || 50;
        data = data || [];
        colors = ['#cc6633', '#cccccc'];
        overs = ['#888888', '#cccccc'];

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
    }

    // Rank chart
    function setRankChart(holder, cx, cy, scale, data)
    {
        cx = cx || 200;
        cy = cy || 100;
        scale = scale || 1;
        data = data || 0;

        var r = Raphael(holder, cx, cy),
            translate = null,
            i = null,
            wrapper = null,
            colors = ['#ceccc4', '#9d2e23', '#aa4a3f', '#b8665d', '#c5837b', '#d3a099', '#c3ca9b', '#b3bc80', '#a1ac65', '#909d4b', '#7b8a33'],
            st = r.set(),
            bars = r.set(),
            faces = r.set();

        // Faces subset
        faces.push(
            r.path( 'M 87.5 12.6 C 87.5 13 87.2 13.3 86.8 13.3 C 86.4 13.3 86.1 13 86.1 12.6 C 86.1 12.2 86.4 11.9 86.8 11.9 C 87.2 11.9 87.5 12.2 87.5 12.6' ),
            r.path( 'M 90.2 12.6 C 90.2 13 89.9 13.3 89.5 13.3 C 89.1 13.3 88.8 13 88.8 12.6 C 88.8 12.2 89.1 11.9 89.5 11.9 C 89.9 11.9 90.2 12.2 90.2 12.6' ),
            r.path( 'M 88.1 16.6 C 88.1 16.6 88 16.6 88 16.6 C 86.5 16.5 85.6 15.3 85.6 15.2 C 85.4 15 85.4 14.7 85.7 14.5 C 85.9 14.3 86.2 14.4 86.4 14.6 C 86.4 14.6 87.1 15.5 88 15.5 C 88.7 15.6 89.3 15.2 89.9 14.6 C 90.1 14.3 90.5 14.3 90.7 14.5 C 90.9 14.7 90.9 15.1 90.7 15.3 C 89.9 16.1 89 16.6 88.1 16.6' ),
            r.path( 'M 88.1 8.3 C 85.1 8.3 82.5 10.8 82.5 13.9 C 82.5 17 85.1 19.5 88.1 19.5 C 91.2 19.5 93.8 17 93.8 13.9 C 93.8 10.8 91.2 8.3 88.1 8.3 M 88.1 18.3 C 85.7 18.3 83.7 16.3 83.7 13.9 C 83.7 11.4 85.7 9.4 88.1 9.4 C 90.6 9.4 92.6 11.4 92.6 13.9 C 92.6 16.3 90.6 18.3 88.1 18.3' ),
            r.path( 'M 4.9 12.6 C 4.9 13 4.6 13.3 4.2 13.3 C 3.8 13.3 3.5 13 3.5 12.6 C 3.5 12.2 3.8 11.9 4.2 11.9 C 4.6 11.9 4.9 12.2 4.9 12.6' ),
            r.path( 'M 7.7 12.6 C 7.7 13 7.4 13.3 7 13.3 C 6.6 13.3 6.3 13 6.3 12.6 C 6.3 12.2 6.6 11.9 7 11.9 C 7.4 11.9 7.7 12.2 7.7 12.6' ),
            r.path( 'M 5.6 14.4 C 5.7 14.4 5.7 14.4 5.8 14.4 C 7.2 14.5 8.2 15.7 8.2 15.7 C 8.4 16 8.3 16.3 8.1 16.5 C 7.9 16.6 7.5 16.6 7.4 16.4 C 7.4 16.3 6.7 15.5 5.7 15.4 C 5.1 15.4 4.4 15.7 3.8 16.4 C 3.6 16.6 3.3 16.6 3.1 16.4 C 2.9 16.2 2.9 15.9 3.1 15.7 C 3.9 14.8 4.7 14.4 5.6 14.4' ),
            r.path( 'M 5.6 8.3 C 2.5 8.3 0 10.8 0 13.9 C 0 17 2.5 19.5 5.6 19.5 C 8.7 19.5 11.2 17 11.2 13.9 C 11.2 10.8 8.7 8.3 5.6 8.3 M 5.6 18.3 C 3.2 18.3 1.2 16.3 1.2 13.9 C 1.2 11.4 3.2 9.4 5.6 9.4 C 8.1 9.4 10 11.4 10 13.9 C 10 16.3 8.1 18.3 5.6 18.3' )
        );
        faces.attr({ 'fill': '#202427', 'stroke': 'none' });

        // Vertical bars subset
        bars.push(
            r.path( 'M 16.6 20.1 L 19.9 20.1 L 19.9 10.4 L 16.6 11 L 16.6 20.1' ),
            r.path( 'M 22.8 20.1 L 26.1 20.1 L 26.1 9.2 L 22.8 9.8 L 22.8 20.1' ),
            r.path( 'M 29 20.1 L 32.3 20.1 L 32.3 8.1 L 29 8.7 L 29 20.1' ),
            r.path( 'M 35.3 20.1 L 38.6 20.1 L 38.6 7 L 35.3 7.6 L 35.3 20.1' ),
            r.path( 'M 41.8 20.1 L 45.1 20.1 L 45.1 5.8 L 41.8 6.4 L 41.8 20.1' ),
            r.path( 'M 48.3 20.1 L 51.6 20.1 L 51.6 4.6 L 48.3 5.2 L 48.3 20.1' ),
            r.path( 'M 54.6 20.1 L 57.9 20.1 L 57.9 3.4 L 54.6 4 L 54.6 20.1' ),
            r.path( 'M 60.8 20.1 L 64.1 20.1 L 64.1 2.3 L 60.8 2.9 L 60.8 20.1' ),
            r.path( 'M 67 20.1 L 70.3 20.1 L 70.3 1.1 L 67 1.7 L 67 20.1' ),
            r.path( 'M 73.2 0.6 L 73.2 20.1 L 76.6 20.1 L 76.6 0 L 73.2 0.6' )
        );
        bars.attr({ 'fill': colors[0], 'stroke': 'none' });

        for (i = 0; i < data; i++){
            bars[i].attr({ 'fill': colors[data] });
        }

        // main set
        st.push(
            faces,
            bars
        );

        translate = 't' + (-1 * st.getBBox().x) +','+ (-1 * st.getBBox().y);
        st.transform(translate + 's'+ scale +','+ scale +', 0, 0' );


        // Over/active colors
        wrapper =  $( '#' + holder ).parents( 'tr' );
        if (wrapper.hasClass( 'active' )) {
            faces.attr({ 'fill': '#ffffff' });
            bars.forEach(
                    function(el,j) {
                        if ( el.attrs.fill === colors[0]) {
                            bars[j].attr({ 'fill': '#ffffff' });
                        }
                });
        } else {
            wrapper.on( 'mouseover', function(){
                bars.forEach(
                    function(el,j) {
                        if ( el.attrs.fill === colors[0]) {
                            bars[j].attr({ 'fill': '#ffffff' });
                        }
                });
            }).on( 'mouseout', function(){
                bars.forEach(
                    function(el,j) {
                        if ( el.attrs.fill === '#ffffff' ) {
                            bars[j].attr({ 'fill': colors[0] });
                        }
                });
            });
        }


    }

    // Add charts
    function addChart()
    {
        $( '.chart' ).each( function(i, el) {
            var chartData = $( el ).data(),
                val = parseFloat( chartData.chartValue ) || 0,
                w = parseFloat( chartData.chartWidth ) || false,
                h = parseFloat( chartData.chartHeight ) || false,
                r = parseFloat( chartData.chartRadius ) || false,
                scale = parseFloat( chartData.chartScale ) || 1;

            switch ( chartData.chartType ) {
                case 'rank':
                    w = w || 95;
                    h = h || 24;
                    setRankChart( el.id, w, h, scale, val );
                    break;

                case 'trend':
                    break;

                default:
                case 'donut':
                    val = val / 100 ;
                    w = w || 20;
                    h = h || 20;
                    r = r || 15;
                    setDonutChart( el.id, w, h, r, scale, [1 - val, val] );
                    break;
            }

        });
    }

    // App init
    function init()
    {
        setupTooltips();
        resizeSidebar();
        setupCollapsibleTable();
        setupSideControls();

        $window.load(function(){
            addChart();
        });
    }

    init();

    // Dev
    if ( dev ) {
        $( 'body' ).append( '<script src="scripts/live.js">' );
    }


});
