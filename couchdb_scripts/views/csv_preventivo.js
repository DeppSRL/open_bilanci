/**
 * Created by stefano on 2/6/14.
 */

function (doc) {
var considered_keys= [ "consuntivo", "preventivo" ];
var considered_quadro=['01','02','03','04','05','06'];
var tipo_bilancio = considered_keys[1];
var value_to_ignore = "Funzioni e servizi / Interventi correnti"
var label_index,single_value, final_key,intervento_name;
    if(doc!==null){
              if(tipo_bilancio in doc){
                if(doc[tipo_bilancio]!==null){

                for (var j = 0; j < considered_quadro.length; j++) {
                          quadro_n = considered_quadro[j];
                          if( quadro_n in doc[tipo_bilancio] ){
                            for( var nome_titolo in doc[tipo_bilancio][quadro_n]){

                     if('data' in doc[tipo_bilancio][quadro_n][nome_titolo]){
                         for(funzione in doc[tipo_bilancio][quadro_n][nome_titolo]['data']){
                            var funzione_value = doc[tipo_bilancio][quadro_n][nome_titolo]['data'][funzione];
                            if(funzione.indexOf("- ") == 0){
                             funzione = funzione.replace("- ","");
                             }

                             if(funzione_value.length == 1){
                                 final_key = tipo_bilancio+"_"+quadro_n+"_"+nome_titolo,funzione.toLowerCase();
                                 final_key = final_key.replace(/ /g, "-");
                                 emit(final_key,funzione_value);
                             }
                             else{
                                 //spacchetta i valori multi dimensionali
                                 for(var k=0; k<funzione_value.length; k++){

                                     single_value = funzione_value[k];
                                     label_index = k;
                                     if( doc[tipo_bilancio][quadro_n][nome_titolo]['meta']['columns'][0] == value_to_ignore ){
                                         label_index = k+1;
                                     }


                                     intervento_name = doc[tipo_bilancio][quadro_n][nome_titolo]['meta']['columns'][label_index];
                                     final_key = doc['_id']+"_"+tipo_bilancio+"_"+quadro_n+"_"+nome_titolo+"_"+funzione.toLowerCase()+"_"+intervento_name;
                                     //sostituisce eventuali spazi con il carattere -                                     
                                     final_key = final_key.replace(/ /g, "-");
                                     emit(final_key,single_value);

                                 }
                             }


                         }

                     }
                    }
                          }
                }
            }
            }

   }
}
