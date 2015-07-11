
function (doc) {
	var considered_keys= [ 'consuntivo', 'preventivo' ];
	var considered_quadro=['04','05'];
    var anno = doc['_id'].substring(0,4);
    var tipo_bilancio = considered_keys[1];
    if(doc!==null){
        if(tipo_bilancio in doc){
            if(doc[tipo_bilancio]!==null){

                for (var j = 0; j < considered_quadro.length; j++) {
                    quadro_n = considered_quadro[j];
                    if( quadro_n in doc[tipo_bilancio] ){
                        // fino al 2007 gli interventi stanno nel sottotitolo delle tabelle
                        for( var nome_titolo in doc[tipo_bilancio][quadro_n]){
                            if('meta' in doc[tipo_bilancio][quadro_n][nome_titolo]){
                                if(anno <= 2007){
                                    if('sottotitolo' in doc[tipo_bilancio][quadro_n][nome_titolo]['meta']){
                                        var intervento_a = doc[tipo_bilancio][quadro_n][nome_titolo]['meta']['sottotitolo'];
                                        emit([intervento_a.toLowerCase(), quadro_n])
                                    }
                                }
                                else{
                                    if('columns' in doc[tipo_bilancio][quadro_n][nome_titolo]['meta']){
                                        // salto il primo valore che e' sempre "Funzioni e servizi /Interventi Correnti"
                                        for(var k=1; k < doc[tipo_bilancio][quadro_n][nome_titolo]['meta']['columns'].length; k++){
                                            var intervento_b = doc[tipo_bilancio][quadro_n][nome_titolo]['meta']['columns'][k];
                                            emit([intervento_b.toLowerCase(), quadro_n])
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