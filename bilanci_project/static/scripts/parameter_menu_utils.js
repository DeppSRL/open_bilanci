/**
 * Created by stefano on 5/7/14.
 */

//escapes a string to be used in a regex
function escapeRegExp(str) {
  return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
}

function init_parameter_menu(site_section){
    //initialize side menu for classifiche / confronti
    // default selected value: the one present in the url address

    var parameter_type=null;
    var dropdown_id = '#'+site_section+'-dropdown';

    //if site_section is 'classifiche' the par type is whatever comes after classifiche in the page url:
    //given the url : classifiche/indicatori/foo -> par_type = indicatori
    var address_split = window.location.pathname.split('/');

    if(site_section == 'classifiche')
        parameter_type = address_split[2];
    else
        parameter_type = address_split[4];

    var par_type_id = '#pl-'+parameter_type;

    // on module load is selected the type of parameter present in the page url
    $('.pl-list').hide();
    $(par_type_id).show(0,function() {
        $(par_type_id).children().show();
        $(dropdown_id).val(parameter_type);
    });

    // binds the selector dropdown change to hide / show parameter lists
      $(dropdown_id).change(function() {

        var selected_element = '#pl-' + $(this).val();
        $('.pl-list').hide(0,function() {
            $(selected_element).children().show(0);
        });
        $(selected_element).show(0,function() {
            $(selected_element).children().show(0);
        });

     });
}
