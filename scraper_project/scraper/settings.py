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

OUTPUT_FOLDER = 'output/'
LISTA_COMUNI = 'listacomuni.csv'
LISTA_COMUNI_PATH =OUTPUT_FOLDER +LISTA_COMUNI
LOGFILE = 'scraper_logfile'
LOGFILE_PATH =OUTPUT_FOLDER +LOGFILE
