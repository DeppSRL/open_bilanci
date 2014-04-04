/**
 * Created by stefano on 4/4/14.
 */
/*
* initialize the confronti page
*/

function init_bilancio_indicatori_page(){
    /*
    opens by default the parameter menu on page load
    */

    var $sidebar = $( '#sidebar' ),
        $content = $( '#content' );

    var clss = {
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

    $sidebar
        .removeClass( clss.sidebar.off )
        .addClass( clss.sidebar.on );
    $content
        .removeClass( clss.content.on )
        .addClass( clss.content.off );
    $( '#toggle-menu' ).addClass( clss.btn.on );



    //initialize linechart element
    //init_main_linechart();
}