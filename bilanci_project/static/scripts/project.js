/* Project specific Javascript goes here. */

!function($){
    $(document).ready(function(){
        // Fix input element click problem
        // http://mifsud.me/adding-dropdown-login-form-bootstraps-navbar/
        $('.dropdown input, .dropdown label').click(function(e) {
            e.stopPropagation();
        });

        $(".autosubmit input, .autosubmit select").on("change", function() {
            $(this).parents('form:first').submit();
        });

        // bilanci entrate/uscite
        // if the element called "bilancio_rootnode" is present then calls the
        // toggle function to open the root node by default
        var bilancio_rootnode_id = "bilancio_rootnode";

        if ($('#'+bilancio_rootnode_id).length){
            $('#'+bilancio_rootnode_id).click();
        }



    });
}(jQuery);