//funzioni preventivo

function (doc) {
	var considered_keys= [ 'consuntivo', 'preventivo' ];
	var considered_quadro=['04','05'];
    var anno = parseInt(doc['_id'].substring(0,4));

    var tipo_bilancio = considered_keys[1];
    if(doc!==null){
        if(tipo_bilancio in doc){
            if(doc[tipo_bilancio]!==null){

                for (var j = 0; j < considered_quadro.length; j++) {
                    quadro_n = considered_quadro[j];
                    if( quadro_n in doc[tipo_bilancio] ){
                        // se anno <= 2007 allora ogni titolo e' una funzione -> il sottotitolo nei meta contiene il nome funzione
                        //se anno > 2007: entro in data, ogni voce e' una funzione
                        if(anno <= 2007){
                            for( var nome_titolo in doc[tipo_bilancio][quadro_n]){
                                if('meta' in doc[tipo_bilancio][quadro_n][nome_titolo]){
                                   if('sottotitolo' in doc[tipo_bilancio][quadro_n][nome_titolo]['meta']){
                                       var funzione = doc[tipo_bilancio][quadro_n][nome_titolo]['meta']['sottotitolo'];
                                       funzione = funzione.toLowerCase();
                                       emit(quadro_n+'_'+funzione,1)
                                   }
                                }
                            }

                        }
                        else{
                            for( var nome_titolo in doc[tipo_bilancio][quadro_n]){
                                if('data' in doc[tipo_bilancio][quadro_n][nome_titolo]){
                                    for(voce in doc[tipo_bilancio][quadro_n][nome_titolo]['data']){
                                        if(voce.indexOf('- ') == 0){
                                            voce = voce.replace('- ','');
                                        }
                                        if(len(doc[tipo_bilancio][quadro_n][nome_titolo]['data'][voce]))
                                            emit(quadro_n+'_'+voce.toLowerCase(),1);
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