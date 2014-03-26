/**
 * Created by stefano on 3/21/14.
 */
var url_is_correct = false;
var error_box_visible = false;

function setIndicatorLinksUrl(){
    var territorio_1_slug = $("#id_territorio_1").select2("val");
    var territorio_2_slug = $("#id_territorio_2").select2("val");

    var url = '/confronti/'+territorio_1_slug+"/"+territorio_2_slug;
    //gets all the link in the parameter side menu
    var parameters = $('.confronti_parameter_container li a');

    //sets the link for indicators in the menu as
    // confronti/territorio1/territorio2/typeofindicator/indicator-slug

    $.each(parameters, function(index, value) {
        var indicator_id = this.id;

        var newLink = url + "/" + indicator_id;
        $(value).attr('href', newLink);
    });

}

function setSubmitButtonUrl(){

    var territorio_1_slug = $("#id_territorio_1").select2("val");
    var territorio_2_slug = $("#id_territorio_2").select2("val");

    var url = '/confronti/'+territorio_1_slug+"/"+territorio_2_slug;

    $("#confronti_submit_btn").attr("href", url);
}

function showWarningBox(msg){
    //insert error text
    $( "#error_msg_box_txt" ).html(msg);
    //show error_msg_box
    $("#error_msg_box").removeClass('hidden');
    error_box_visible = true;
}

function hideWarningBox(){
    if(error_box_visible){
        $("#error_msg_box").addClass('hidden');
        $( "#error_msg_box_txt" ).html('');
    }

}

function checkTerritoriCluster(){
    var needle = 'Cluster:';

    var territorio_1_name = $("#id_territorio_1").select2('data').text;
    var territorio_2_name = $("#id_territorio_2").select2('data').text;

    var territorio_1_cluster = territorio_1_name.substr(territorio_1_name.indexOf(needle) + needle.length);
    var territorio_2_cluster = territorio_2_name.substr(territorio_2_name.indexOf(needle) + needle.length);

    if(territorio_1_cluster != territorio_2_cluster){
        // if territori are in different cluster show the error box
        showWarningBox('ATTENZIONE, HAI SCELTO DUE COMUNI CHE APPARTENGONO A CLASSI DIMENSIONALI DIVERSE. IL CONFRONTO POTREBBE NON AVERE SIGNIFICATO');

    }
    else{
        // if territori are in the same cluster hide the error box
        hideWarningBox();
    }
}

function changeConfrontiUrl(){

    var territorio_1_slug = $("#id_territorio_1").select2("val");
    var territorio_2_slug = $("#id_territorio_2").select2("val");

    if(territorio_1_slug && territorio_2_slug){

        //sets url for the fake submit button
        setSubmitButtonUrl();

        // sets url for indicatori link in the side menu
        setIndicatorLinksUrl();

        //if the territori selected are in different cluster show warning msg
        checkTerritoriCluster();

        url_is_correct = true;
    }
    else{

        url_is_correct = false;
    }
}


function submitButtonConfronti(e){
     e.preventDefault();

    //if url is correct, navigates to confronti page, else display error msg

    if(url_is_correct)
    {
        window.location = $("#confronti_submit_btn").attr('href');
    }
    else{
        showWarningBox('ATTENZIONE, DEVI SELEZIONARE DUE COMUNI PER PROCEDERE NEL CONFRONTO');

    }
}