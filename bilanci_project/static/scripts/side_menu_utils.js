/**
 * Created by stefano on 4/16/14.
 */

function resizeComponents(){
    /*
    When the side menu is hidden / shown resizes the components that are defined for the page
    */

    if(typeof year_selector !== 'undefined' ){
        if(year_selector){
            year_selector.resize();
        }
    }
    if(typeof linechart !== 'undefined' ){
        if(linechart){
            linechart.resize();
        }
    }
}