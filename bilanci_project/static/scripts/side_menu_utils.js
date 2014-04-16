/**
 * Created by stefano on 4/16/14.
 */
$(document).ready(function(){

    /*
    opens by default the parameter menu on page load
    */

    var $sidebar = $( '#sidebar' ),
        $content = $( '#content'),
        $pushMenu = $( '#push-menu' ) ,
        $hideMenu = $( '#hide-menu' ) ;

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
    $pushMenu.addClass( clss.btn.on );


    // binds the menu toggles with the graph / year selector resize when clicked

    if($pushMenu.length){
        $pushMenu.on("click", resizeComponents);
    }
    if($hideMenu.length){
        $hideMenu.on("click", resizeComponents);
    }
});

function resizeComponents(){
    if(year_selector){
        year_selector.resize();
    }
    if(linechart){
        linechart.resize();
    }
}