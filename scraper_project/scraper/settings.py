# Scrapy settings for scraper_project project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#
LOG_LEVEL = "DEBUG"

BOT_NAME = 'scraper_project'

SPIDER_MODULES = ['scraper.spiders']
NEWSPIDER_MODULE = 'scraper.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'bilanci_scraper'

OUTPUT_FOLDER = 'scraper/output/'
LISTA_COMUNI = 'listacomuni.csv'
LISTA_COMUNI_PATH =OUTPUT_FOLDER +LISTA_COMUNI
LOGFILE = 'scraper_logfile'
LOGFILE_PATH =OUTPUT_FOLDER +LOGFILE

BILANCI_PAGES_FOLDER = '/home/nishant/NAS/bilanci'

# preventivi url
URL_PREVENTIVI_PRINCIPALE = "http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/%s/anno/%s/cod/3/md/0/tipo_modello/U"
# consuntivi url
URL_CONSUNTIVI_PRINCIPALE ="http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/%s/anno/%s/cod/4/md/0/tipo_modello/U"

START_YEAR_SPIDER = 2002
END_YEAR_SPIDER = 2003

ITEM_PIPELINES = {
    'scraper.pipelines.BilanciPagesPipeline': 300,

    }