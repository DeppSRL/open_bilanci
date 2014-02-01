#!/usr/local/bin/python
# coding: utf-8
import sys
from urllib2 import URLError
import couchdb
from  gspread.exceptions import SpreadsheetNotFound
import gspread
import argparse
from pprint import pprint
import requests
from settings_local import *


def simplify(source_db, destination_db, id_list_response, list_sheet):
    voci_map = {}
    #prende entrambi i fogli di calcolo e li inserisce nella stessa lista, saltando le prime due righe di intestazione
    try:
        voci_ws = list_sheet.worksheet("preventivo").get_all_values()[2:]
        voci_ws.extend(list_sheet.worksheet("consuntivo").get_all_values()[2:])
    except URLError:
        print "Connection error to Gdrive"
        return

    # prima di creare la mappa di voci fa una passata sulla lista e marca con un booleano le voci
    # che saranno soggette a somme

    # per identificare le voci in cui si effettuera' una somma usero' la colonna 8 della lista
    # per cui prima faccio una passata e metto la colonna 8 a False, eliminando possibili valori sporchi presi dal gdoc

    for row in voci_ws:
        if len(row)> 8:
            del row[-1]

        row.append(None)

    # contatori per statistiche e controllo
    c_uniche=0
    c_no=0

    # scorre la lista delle voci una per una confrontando ogni voce con tutte le altre.
    # se trova che una voce e' ripetuta piu' di una volta la marca con somma=True,
    # in questo modo quando andro' a fare la traduzione delle voci se la voce che
    # viene analizzata confluisce in una voce semplificata per cui e' prevista la somma
    # andro' a sommare il valore a quelli eventualmente gia' presenti nell'albero semplificato
    # viceversa sara' un assegnamento semplice


    for actual_row_idx, actual_row_val in enumerate(voci_ws):
        tipo_bilancio_ar = unicode(actual_row_val[0]).lower()
        entrata_uscita_ar = unicode(actual_row_val[7]).lower()
        titolo_ar = unicode(actual_row_val[6]).lower()
        categoria_ar = unicode(actual_row_val[5]).lower()
        voce_ar = unicode(actual_row_val[4]).lower()
        somma_ar = actual_row_val[8]

        # se somma_ar == None allora vuol dire che non e' ancora stato analizzato
        # se e' True o False vuol dire che e' gia' stato marcato dall'algoritmo
        if somma_ar is None:
            trovato = False
            for compare_row_idx, compare_row_val in enumerate(voci_ws):
                # evita di comparare la riga considerata con se' stessa nel secondo loop
                if compare_row_idx != actual_row_idx:
                    if tipo_bilancio_ar == unicode(compare_row_val[0]).lower() and \
                        entrata_uscita_ar == unicode(compare_row_val[7]).lower() and \
                        titolo_ar == unicode(compare_row_val[6]).lower() and \
                        categoria_ar == unicode(compare_row_val[5]).lower() and \
                        voce_ar == unicode(compare_row_val[4]).lower():

                            # ha trovato almeno un valore uguale per cui
                            # mette a True somma_ar per compare_row
                            # e mette a True trovato per mettere a True somma_ar anche per actual_row
                            trovato = True
                            compare_row_val[8]=True

            # assegna come valore di somma_ar il valore di Trovato
            actual_row_val[8] = trovato

            # incrementa contatori statistiche
            if trovato is True:
                c_uniche+=1
            else:
                c_no +=1




    # crea la mappa per voci e funzioni
    for row in voci_ws:
        # considero valide solo le righe che hanno i valori di entrata/uscita e di titolo non nulli
        if row[6] and row[7]:

            tipo_bilancio_norm = unicode(row[0]).lower()
            # zero padding per n_quadro: '2' -> '02'
            quadro_norm=row[1].zfill(2)
            titolo_norm = unicode(row[2]).lower()
            voce_norm = unicode(row[3]).lower()


            if tipo_bilancio_norm not in voci_map:
                voci_map[tipo_bilancio_norm] = {}
            if quadro_norm not in voci_map[tipo_bilancio_norm]:
                voci_map[tipo_bilancio_norm][quadro_norm] = {}
            if titolo_norm not in voci_map[tipo_bilancio_norm][quadro_norm]:
                voci_map[tipo_bilancio_norm][quadro_norm][titolo_norm] = {}

            if voce_norm not in voci_map[tipo_bilancio_norm][quadro_norm][titolo_norm]:
                voci_map[tipo_bilancio_norm][quadro_norm][titolo_norm][voce_norm] = {}


            #  crea la mappa di conversione delle voci
            # la chiave e' tipo_bilancio_norm, numero_quadro , nome_titolo, voce_raw

            translation_dict=\
                {
                'tipo_bilancio_norm': tipo_bilancio_norm,
                'entrata_uscita': unicode(row[7]).lower(),
                'titolo': unicode(row[6]).lower(),
                'somma': row[8]
            }

            # se la categoria e/o la voce non sono specificati, non li inserisce nella mappa
            if unicode(row[5]).lower() != "":
                translation_dict['categoria']=unicode(row[5]).lower()
            if unicode(row[4]).lower() != "":
                translation_dict['voce']=unicode(row[4]).lower()

            voci_map[tipo_bilancio_norm][quadro_norm][titolo_norm][voce_norm]= translation_dict

    # todo: creare la mappa per gli interventi


    # per ogni documento nel db applica la conversione
    if 'rows' in id_list_response.keys():
        id_list=id_list_response['rows']

        for id_object in id_list:
            source_document = source_db.get(id_object['id'])


            if source_document is not None:
                destination_document = {'_id': id_object['id']}

                if "_design/" not in id_object['id']:

                    print "Copying document id:"+id_object['id']
                    #  per ogni tipo di bilancio
                    for tipo_bilancio_norm in ['preventivo','consuntivo']:
                        if tipo_bilancio_norm in source_document.keys():
                            bilancio_norm = source_document[tipo_bilancio_norm]
                            destination_document[tipo_bilancio_norm]={}

                            for quadro_name_norm, quadro_norm in bilancio_norm.iteritems():

                                if quadro_name_norm != '04' and quadro_name_norm != '05':
                                    for titolo_name_norm, titolo_norm in quadro_norm.iteritems():
                                        # analizza i titoli e traduce titoli e voci

                                        # se la voce e' presente nella mappa di traduzione
                                        for voce_name_norm, voce_norm in titolo_norm['data'].iteritems():
                                            if quadro_name_norm in voci_map[tipo_bilancio_norm].keys():
                                                if titolo_name_norm in voci_map[tipo_bilancio_norm][quadro_name_norm].keys():
                                                    if voce_name_norm in voci_map[tipo_bilancio_norm][quadro_name_norm][titolo_name_norm].keys():
                                                        voce_translation_map = voci_map[tipo_bilancio_norm][quadro_name_norm][titolo_name_norm][voce_name_norm]
                                                        
                                                        tipo_bilancio_simple = voce_translation_map['tipo_bilancio_norm']
                                                        entrata_uscita_simple = voce_translation_map['entrata_uscita']
                                                        titolo_simple = voce_translation_map['titolo']

                                                        voce_simple = None
                                                        if 'voce' in voce_translation_map:
                                                            voce_simple = voce_translation_map['voce']

                                                        categoria_simple = None
                                                        if 'categoria' in voce_translation_map:
                                                            categoria_simple = voce_translation_map['categoria']

                                                        somma_simple = voce_translation_map['somma']
                                                        
                                                        if tipo_bilancio_simple not in destination_document:
                                                            destination_document[tipo_bilancio_simple]={}
                                                        
                                                        if entrata_uscita_simple not in destination_document[tipo_bilancio_simple]:
                                                            destination_document[tipo_bilancio_simple][entrata_uscita_simple]={}

                                                        if titolo_simple not in destination_document[tipo_bilancio_simple][entrata_uscita_simple]:
                                                            destination_document[tipo_bilancio_simple][entrata_uscita_simple][titolo_simple]={}

                                                        if categoria_simple:
                                                            if categoria_simple not in destination_document[tipo_bilancio_simple][entrata_uscita_simple][titolo_simple]:
                                                                destination_document[tipo_bilancio_simple][entrata_uscita_simple][titolo_simple][categoria_simple]={}

                                                            if voce_simple:
                                                                if voce_simple not in destination_document[tipo_bilancio_simple][entrata_uscita_simple][titolo_simple][categoria_simple]:
                                                                    try:
                                                                        destination_document[tipo_bilancio_simple][entrata_uscita_simple][titolo_simple][categoria_simple][voce_simple]={}
                                                                    except TypeError:
                                                                        print "Error: different levels for "+tipo_bilancio_simple,\
                                                                            entrata_uscita_simple,titolo_simple,categoria_simple,voce_simple
                                                                        return


                                                        if somma_simple is True:
                                                            #somma la voce
                                                            pass
                                                        else:
                                                            # assegnamento della voce
                                                            if voce_simple and categoria_simple:
                                                                destination_document[tipo_bilancio_simple]\
                                                                    [entrata_uscita_simple]\
                                                                    [titolo_simple]\
                                                                    [categoria_simple]\
                                                                    [voce_simple]=voce_norm
                                                            else:
                                                                if categoria_simple and not voce_simple:
                                                                    destination_document[tipo_bilancio_simple]\
                                                                    [entrata_uscita_simple]\
                                                                    [titolo_simple]\
                                                                    [categoria_simple]=voce_norm
                                                                else:
                                                                    print "Error: voce_simple != None and categoria_simple == None"
                                                                    print "Error in following voce_translation_map:"
                                                                    pprint(voce_translation_map)







                        else:
                            # se il documento e' un design doc, non lo copia
                            pass


                        # scrive il nuovo oggetto nel db di destinazione
                        destination_db.save(destination_document)

    return



def main(argv):
    description = 'Simplify DB structure, copying elements from voci normalized db to the simplified db'
    parser = argparse.ArgumentParser(description=description)

    accepted_servers_help = "Server name: "
    for accepted_servers_name in accepted_servers.keys():
        accepted_servers_help+= accepted_servers_name+" | "


    parser.add_argument('--server','-s', dest='server_name', action='store',
               default='localhost',
               help=accepted_servers_help
        )

    args = parser.parse_args()
    server_name= args.server_name



    if server_name in accepted_servers.keys():
        # Login with the script Google account
        gc = gspread.login(g_user, g_password)


        print "Gets data from Gdoc..."
        # open the list worksheet
        list_sheet = None
        try:
            list_sheet = gc.open_by_key(gdoc_keys['simplify'])
        except SpreadsheetNotFound:
            print "Error: gdoc url not found"
            return
        print "Done!"

        # connessione a couchdb
        # costruisce la stringa per la connessione al server aggiungendo user/passw se necessario
        server_connection_address ='http://'
        if accepted_servers[server_name]['user']:
            server_connection_address+=accepted_servers[server_name]['user']+":"
            if accepted_servers[server_name]['password']:
                server_connection_address+=accepted_servers[server_name]['password']+"@"

        server_connection_address+=accepted_servers[server_name]['host']+":"+accepted_servers[server_name]['port']

        print "Connecting to: "+server_connection_address+" ..."
        # open db connection
        server = couchdb.Server(server_connection_address)

        # set source db name / destination db name
        source_db_name = accepted_servers[server_name]['normalized_voci_db_name']
        destination_db_name = accepted_servers[server_name]['simplified_db_name']


        source_db = server[source_db_name]
        print "Source DB connection OK! Db name: "+source_db_name

        # se esiste il db lo cancella

        if destination_db_name in server:
            del server[destination_db_name]
            print  "Destination db: "+  destination_db_name +" deleted"

        # crea il db
        destination_db = server.create(destination_db_name)
        print  "Destination db: "+  destination_db_name +" created"

        print "Gets all Document ids from db"
        # legge la lista di id per recuperare tutti gli oggetti del db
        get_all_docs_url = server_connection_address+'/'+source_db_name+'/_all_docs?include_docs=false'

        id_list_response = requests.get(get_all_docs_url ).json()
        print "Done"
        simplify(source_db, destination_db, id_list_response, list_sheet)

    else:
        print "server not accepted:"+server_name



# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
