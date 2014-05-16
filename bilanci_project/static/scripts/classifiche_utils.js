/**
 * Created by stefano on 5/11/14.
 */

//unchecks all checkboxes
function toggle_checkboxes(source) {

  var regioni = document.getElementsByName('regione[]');
  var cluster = document.getElementsByName('cluster[]');

  for(var i=0, n=regioni.length;i<n;i++) {
    regioni[i].checked = source.checked;
  }

  for(i=0, n=cluster.length;i<n;i++) {
    cluster[i].checked = source.checked;
  }
}
