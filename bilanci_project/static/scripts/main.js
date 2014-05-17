/**
 * Main scripts
 * @author mleone
 * @version 1.5.7
 **/

$(document).ready(function(){

    // Main vars
    var $window   = $( window ),
        $lock     = $( '#lock' ),
        $main     = $( '#main-content'),
        $sidebar  = $( '#sidebar' ),
        $content  = $( '#content' ),
        $results  = $( '#results' ),
        $comments = $( '#comments' ),
        $controls = $( '#side-controls' ),
        $settings = $( '#settings' ),
        $sidemenu = $( '#side-menu' ),
        mapPage  = ( $( '#map-canvas' ).length ? true : false ),

        options    = {
            'env': 'development', // Environment. Values: production, development
            'autoScroll': !mapPage, // Side controls automatic scrolling. Values: true, false
            'offset': ( mapPage ? 180 : 100 ), // Top offset.
            'collapsibleMenu': {
                'closeOthers': true // On click collapse other items. Values: true, false
            },
            'pushMenu': {
                'scroll': true, // Push menu scrolling. Values: true, false
                'scrollto': false // On click scroll page to menu position. Values: true, false
            }
        };

    function homeInit()
    {
        var home = {
            $sections : $( '#main-content > section' ),
            $more : $( '#more-content a' ),
            $navlinks : $( '#nav-links > a' ),
            currentLink : 0,
            $body : $( 'html, body' ),
            animspeed : 650,
            animeasing : 'easeInOutExpo'
        };

        home.$more.css( 'opacity', 1 );

        home.$sections.waypoint( function( direction ) {
            if( direction === 'down' ) { changeNav( $( this ) ); }
        }, { offset: '30%' } ).waypoint( function( direction ) {
            if( direction === 'up' ) { changeNav( $( this ) ); }
        }, { offset: '-30%' } );

        // on window resize: the body is scrolled to the position of the current section
        $window.on( 'debouncedresize', function() {
            scrollAnim( home.$sections.eq( home.currentLink ).offset().top );
        });

        // click on a navigation link: the body is scrolled to the position of the respective section
        home.$navlinks.on( 'click', function() {
            scrollAnim( home.$sections.eq( $( this ).index() ).offset().top );
            return false;
        });

        // click on the arrow link
        home.$more.on( 'click', function() {
            var n = (home.currentLink + 1 < home.$sections.length ? home.currentLink + 1 : 0);
            scrollAnim( home.$sections.eq( n ).offset().top );
            home.$more.css( 'opacity', '');
            return false;
        });

        // update the current navigation link
        function changeNav( $section ) {
            home.$navlinks.eq( home.currentLink ).removeClass( 'current' );
            home.currentLink = $section.index( 'section' );
            home.$navlinks.eq( home.currentLink ).addClass( 'current' );
        }

        // function to scroll / animate the body
        function scrollAnim( top )
        {
            home.$body.stop().animate( { scrollTop : top }, home.animspeed, home.animeasing );
        }
    }




    // Function to get the Max value in Array
    Array.max = function( array ){
        return Math.max.apply( Math, array );
    };

    // Function to get the Min value in Array
    Array.min = function( array ){
       return Math.min.apply( Math, array );
    };

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

            panel.siblings( '.shown' ).removeClass( 'shown' );
            panel.prev().addClass( 'shown' );

            panel.siblings( '.panel-heading' ).not( $( '.shown' ) ).find( 'span.icon' )
                    .removeClass( 'sprite-minus' )
                    .addClass( 'sprite-plus' );

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

    // Scroll box
    function setupScrollbox()
    {
        $( '.scrollbox' ).enscroll({
            showOnHover: true,
            pollChanges: true,
            verticalTrackClass: 'track',
            verticalHandleClass: 'handle'
        });
    }

    // Collapsible menu
    function setupCollapsibleMenu( $container )
    {
        $container.find( '.panel-collapse' ).on( 'click', function(e){
            e.preventDefault();
            var $togglers = $container.find( '.panel-collapse' ),
                $toggler = $( this ),
                $submenu = $toggler.next( 'ul' ),
                $pin = null,
                selected = 0;

            $togglers.each(function( i, el ){

                if ( !$toggler.is($( el )) ) {
                    if ( options.collapsibleMenu.closeOthers ) {
                        $( el ).addClass( 'collapse' );
                        $( el ).next( 'ul' ).addClass( 'hidden' );
                    }
                } else {
                    $toggler.toggleClass( 'collapse' );
                        $submenu.toggleClass( 'hidden' );
                }

                selected = $( el ).next( 'ul' ).find( 'input:checked' ).length;
                $pin = $( el ).prev();

                if (selected > 0) {
                    $pin.removeClass( 'hidden' );
                } else {
                    $pin.addClass( 'hidden' );
                }
            });
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
            $controls.css({ left: -50 });

            $sidebar
                .removeClass( clss.sidebar.off )
                .addClass( clss.sidebar.on );
            $content
                .removeClass( clss.content.on )
                .addClass( clss.content.off );

            $window.trigger( 'scroll' );

            if ( options.pushMenu.scrollto ) {
                $( 'html, body' ).animate({
                    scrollTop: $sidebar.offset().top
                }, 0);
            }
        });

        $closer.on( 'click', function( e ){
            e.preventDefault();
            $controls.css({ left: -2 });

            $sidebar
                .removeClass( clss.sidebar.on )
                .addClass( clss.sidebar.off );
            $content
                .removeClass( clss.content.off )
                .addClass( clss.content.on );
        });


        $sidebar.find( 'ul.dropdown-menu li a' ).on( 'click', function( e ){
            e.preventDefault();

            var $this = $( this ),
                $dropdown = $this.parents( '.dropdown' ),
                $btn = $dropdown.find( 'button' );

            $btn.html( '<span class="caret pull-right" />' + $this.text() );
            $dropdown.removeClass('open');

            $sidebar.find( 'ul.menu' ).addClass( 'hidden' );
            $sidebar.find( $this.attr( 'href' ) ).removeClass( 'hidden' );

        });

        setupCollapsibleMenu( $sidebar );
    }

    // Settings menu
    function setupSettingsMenu()
    {
        var $panel  = $settings,
            $opener = $( '#open-settings' ),
            $closer = $( '#hide-settings' ),
            delta   = $panel.width();

        $opener.on( 'click', function( e ){
            e.preventDefault();
            $panel.css({ left: 4 }).show( 0 );
            $controls.css({ left: -50 });
        });

        $closer.on( 'click', function( e ){
            e.preventDefault();
            $panel.css({ left: -1 * (delta + 20) });
            $controls.css({ left: -2 });
        });

        // Check for map page
        if ( mapPage ) {
            $opener = $( '#open-menu-schede, #open-menu-indicatori, #open-menu-filtri' );
            $closer = null;

            $opener.on( 'click', function( e ){
                e.preventDefault();

                var $this = $( this ),
                    $target = $( $this.attr( 'href' ) ),
                    $closer = $target.find( 'a.close-menu' );

                $target
                    .removeClass('hidden')
                    .siblings().addClass('hidden');

                $closer.on( 'click', function( e ){
                    e.preventDefault();
                    $target.addClass('hidden');
                });
            });

            setupCollapsibleMenu( $( '#menu-indicatori' ) );
        }

    }

    // Reposition controls and settings panel
    function moveScroll( $el, offset )
    {
         var y = 0,
             h = 0,
             t = 0;

         if ( $el.length ) {

            h = $( '#header' ).height() || 0;
            t = $el.closest( $sidebar ).length ? $sidebar.position().top : 0;

            if ( $window.scrollTop() >= offset + h + t ) {
                    y = $window.scrollTop() - h - t;
                    if ( y >= $main.height() - $el.height() - t) {
                        y = $main.height() - $el.height() - t;
                    }
                } else {
                    y = offset;
                }

            $el.css( 'top', y );
        }
    }

    // Side controls
    function setupSideControls()
    {
        $controls.show();

        moveScroll( $controls, options.offset );
        moveScroll( $settings, options.offset );

        if ( options.pushMenu.scroll ) {
            moveScroll( $sidemenu, 0 );
        }

        $window.on( 'load', function() {
            moveScroll( $controls, options.offset );
            moveScroll( $settings, options.offset );
            if ( options.pushMenu.scroll ) {
                moveScroll( $sidemenu, 0 );
            }
        });

        if ( options.autoScroll) {
            $window.on( 'scroll', function() {
                moveScroll( $controls, options.offset );
                moveScroll( $settings, options.offset );
                if ( options.pushMenu.scroll ) {
                    moveScroll( $sidemenu, 0 );
                }
            });
        }

        setupPushMenu();
        setupSettingsMenu();
    }

    // Tooltips
    function setupTooltips()
    {
        $( '[data-toggle="tooltip"]' ).tooltip( {placement: 'right', container: 'body'} );
    }

    // Donut chart
    function setDonutChart(holder, cx, cy, radius, data)
    {
        cx = cx || 100;
        cy = cy || 100;
        radius = radius || 50;
        data = data || [];
        colors = ['#ceccc4', '#cc6633'];
        overs = ['#ceccc4', '#888888'];

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

    // Line chart
    function setLineChart(holder, cx, cy, xdata, data)
    {
        cx = cx || 200;
        cy = cy || 100;
        data = data || [];
        xdata = xdata || [0, 1, 3, 4, 5];

        var vmax = Array.max(data),
            idx = data.indexOf(vmax),
            r = Raphael(holder, cx, cy),
            pmax = null,
            x = -5,
            y = 5,
            xlen = cx,
            ylen = cy,
            gutter = 20,
            l = r.linechart(x, y, xlen, ylen, xdata, data, {
                gutter: gutter,
                nostroke: false,
                width: 7,
                colors: ['#ceccc4'],
                axis: "0 0 0 0",
                symbol: "circle",
                smooth: false
            });

        // reset radius of all points
        l.symbols.attr({ r: 0 });

        // hightlight the point with higher y value
        // for the last instead of max:
        // l.symbols[0].length;
        // idx = last-1
        pmax = l.symbols[0][idx];
        pmax.attr({ r: 8, fill: '#cc6633' });

        // draw the line
        // "M10 10L90 90" = draw a line: move to 10,10, line to 90,90
        r.path( "M" + pmax.attr('cx') + " " + pmax.attr('cy') + "L" + pmax.attr('cx') + " " + (pmax.attr('cy') - 13) ).attr({ 'stroke-width': 3, stroke: '#cc6633' });

        // print the label
        r.text( pmax.attr('cx'), (pmax.attr('cy') - 21), xdata[idx]).attr({'font-size': 10, 'font-family': "Lato", 'font-weight': 700, fill: "#cc6633"});

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

        // Main set
        st.push(
            faces,
            bars
        );

        // Scale
        translate = 't' + (-1 * st.getBBox().x) +','+ (-1 * st.getBBox().y);
        st.transform(translate + 's'+ scale +','+ scale +', -1, -1' );

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
                val = chartData.chartValue,
                xdata = chartData.chartXdata,
                w = parseFloat( chartData.chartWidth ) || false,
                h = parseFloat( chartData.chartHeight ) || false,
                r = parseFloat( chartData.chartRadius ) || false,
                scale = parseFloat( chartData.chartScale ) || 1;

            switch ( chartData.chartType ) {
                case 'rank':
                    val = parseFloat( val ) || 0;
                    w = w || 95;
                    h = h || 24;
                    setRankChart( el.id, w, h, scale, val );
                    break;

                case 'trend':
                    val = val.replace(/ /g,'').split(',').map(Number);
                    xdata = xdata.replace(/ /g,'').split(',').map(Number);
                    w = w || 95;
                    h = h || 24;
                    setLineChart( el.id, w, h, xdata, val );
                    break;

                default:
                case 'donut':
                    val = parseFloat( val ) / 100 ;
                    w = w || 20;
                    h = h || 20;
                    r = r || 15;
                    setDonutChart( el.id, w, h, r, [1 - val, val] );
                    break;
            }

        });
    }


    function parallax()
    {
        $('section[data-type="background"]').each(function(){

        var $scroll = $(this);

            $window.scroll(function() {
            var yPos = -($window.scrollTop() / $scroll.data('speed'));

            // background position
            var coords = '50% '+ yPos + 'px';

            // move the background
            $scroll.css({ backgroundPosition: coords });
         });
      });
    }

    // App init
    function init()
    {
        setupTooltips();
        setupScrollbox();
        setupCollapsibleTable();
        setupSideControls();
        parallax();

        if ( $( 'body#home' ).length ) {
            homeInit();
        }

        $window.load(function(){
            addChart();
        });
    }

    init();

    // Dev
    if ( options.env === 'development' ) {
        $( 'body' ).append( '<script src="scripts/live.js"></script>' );
    }


});
