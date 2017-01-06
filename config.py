import logging


bot_token = 'YOUR_TOKEN'
db_test_name = 'database/ukrposhta_tests.db'
db_name = 'database/ukrposhta.db'
botan_token = 'YOUR_BOTAN_TOKEN'

logger = logging.getLogger('UkrPoshtaBot')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(u'[%(asctime)s] - %(filename)s[LINE:%(lineno)d]# %(levelname)-8s %(message)s')
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
try:
    log = open('/home/logs/ukrposhta.log', "a", encoding="utf-8")
except FileNotFoundError:
    log = open('./logs/ukrposhta.log', "a", encoding="utf-8")
ch = logging.StreamHandler(log)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(sh)
