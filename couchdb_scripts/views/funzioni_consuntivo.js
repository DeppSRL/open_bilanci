function (doc) {
	var considered_keys= [ 'consuntivo', 'preventivo' ];
	var considered_quadro=['04','05'];

    var tipo_bilancio = considered_keys[0];
    if(doc!==null){
        if(tipo_bilancio in doc){
            if(doc[tipo_bilancio]!==null){

                for (var j = 0; j < considered_quadro.length; j++) {
                    quadro_n = considered_quadro[j];
                    if( quadro_n in doc[tipo_bilancio] ){
                        for( var nome_titolo in doc[tipo_bilancio][quadro_n]){
                            if('data' in doc[tipo_bilancio][quadro_n][nome_titolo]){
                                for(funzione in doc[tipo_bilancio][quadro_n][nome_titolo]['data']){
                                    if(doc[tipo_bilancio][quadro_n][nome_titolo]['data'][funzione].length >0){

                                        var funzione_clean = funzione.toLowerCase();
                                        if(funzione_clean.indexOf('- ') === 0){
                                            funzione_clean = funzione_clean.replace('- ','');
                                        }

                                        var titolo_clean = nome_titolo.replace('quadro-','');
                                        emit([funzione_clean,titolo_clean]);
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