# Google Account credentials
g_user = 'USERNAME@gmail.com'
g_password = 'PASSWORD'

# gdoc keys
gdoc_keys= {
    'titoli':
        'INSERT_DOCUMENT_KEY_HERE',
    'voci':
        'INSERT_DOCUMENT_KEY_HERE',
    'simplify':
        'INSERT_DOCUMENT_KEY_HERE',
}


accepted_types={
    'voci':{
        'csv_keys':["tipo","quadro","titolo", "voce"],
    },
    'titoli':{
        'csv_keys':["tipo","quadro", "titolo"]
    }
}


accepted_servers = {
    'localhost': {
        'host': 'localhost',
        'port': '5984',
        'user': '',
        'password':'',
        'raw_db_name':'DB_NAME_HERE',
        'normalized_titoli_db_name':'DB_NAME_HERE',
        'normalized_voci_db_name': 'DB_NAME_HERE',
    },
    'staging': {
        'host': 'staging.depp.it',
        'port': '5984',
        'user': 'USER',
        'password':'PASSW',
        'raw_db_name':'DB_NAME_HERE',
        'normalized_titoli_db_name':'DB_NAME_HERE',
        'normalized_voci_db_name': 'DB_NAME_HERE',
    },
}

