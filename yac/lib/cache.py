
import shelve  # for local cache
import os, sys, time, datetime

from yac.lib.paths import get_config_path

class CacheError():
    def __init__(self, msg):
        self.msg = msg

# set expiration in ms
def set_cache_value_ms(key_name, value, expiration_ms=""):

    # save value to shelve db
    yac_db = _get_cache()

    if not expiration_ms:
        # set expiration to next year
        expiration_dt = datetime.date.today() + datetime.timedelta(days=365)
        # convert to ms
        expiration_ms = int(expiration_dt.strftime("%s")) * 1000

    yac_db[key_name] = {"value": value, "expiration_ms": expiration_ms}

# set expiration using a datetime object
def set_cache_value_dt(key_name, value, expiration_dt=""):

    # save value to shelve db
    yac_db = _get_cache()

    if not expiration_dt:
        # set expiration to next year
        expiration_dt = datetime.date.today() + datetime.timedelta(days=365)

    # convert to ms
    expiration_ms = int(expiration_dt.strftime("%s")) * 1000

    yac_db[key_name] = {"value": value, "expiration_ms": expiration_ms}

def get_cache_value(key_name, default_value={}):

    cache_db = _get_cache()

    # current time in ms
    time_ms = int(time.time() * 1000)

    if (key_name in cache_db and time_ms < cache_db[key_name]["expiration_ms"]):

        # convert the expiration to millis
        return cache_db[key_name]['value']
    else:
        return default_value

def delete_cache_value(key_name):

    cache_db = _get_cache()

    if key_name in cache_db:
        cache_db.pop(key_name)

def get_cache_keys():

    cache_db = _get_cache()

    return list(cache_db.keys())

def _get_cache():

    # cache should be saved under the user's home directory
    home = os.path.expanduser("~")
    db_home = os.path.join(home,'.yac')

    if not os.path.exists(db_home):
        os.makedirs(db_home)

    yac_db_path = os.path.join( db_home,'yac_cache')

    cache_db = shelve.open(yac_db_path)

    return cache_db
