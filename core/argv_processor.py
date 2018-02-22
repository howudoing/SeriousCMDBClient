import sys, os
import logging, json,urllib

# BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(BASEDIR)
from plugins import collector
from conf import settings
from core import api_token

class ArgvProcessor:
    def __init__(self, argv_list):
        self.argvs = argv_list
        self.parse_argv()

    def parse_argv(self):
        if len(self.argvs) == 2:
            if hasattr(self, self.argvs[1]):
                func = getattr(self, self.argvs[1])
                func()
            else:
                self.help_msg()
        else:
            self.help_msg()

    def help_msg(self):
        msg = '''
        collect_data
        run_forever
        get_asset_id
        report_asset'''
        print("argv:", msg)

    def collect_data(self):
        pass

    def run_forever(self):
        pass

    def get_asset_id(self):
        pass

    def report_asset(self):
        asset_collector = collector.Collector()
        asset_data = asset_collector.info_data
        asset_id = self.load_asset_id()
        if asset_id: #reported before
            asset_data["asset_id"] = asset_id
            post_url = settings.URLS["asset_report"]
        else:
            asset_data["asset_id"] = None
            post_url = settings.URLS["asset_report_with_no_id"]
        data = {"asset_data": json.dumps(asset_data)}
        response = self.__submit_data(post_url, data, method="post")
        if "asset_id" in response:
            self.__update_asset_id(response["asset_id"])
        self.log_record(response)


    def load_asset_id(self):
        asset_id_file = settings.ASSET_ID_FILE
        if os.path.isfile(asset_id_file):
            asset_id = open(asset_id_file).read().strip()
            if asset_id.isdigit():
                return asset_id
            else:
                return False
        else:
            return False

    def __submit_data(self, url, data, method):
        if url in settings.URLS:
            if type(settings.PORT) is int:
                url = "http://%s:%s%s" % (settings.SERVER, settings.PORT, settings.URLS[url])
            else:
                url = "http://%s%s" % (settings.SERVER, settings.URLS[url])
            url = self.__attach_token(url)
            if method == "get":
                pass
            elif method == "post":
                try:
                    data_encode = urllib.urlencode(data)
                    req = urllib.request.Request(url)
                    res_data = urllib.request.urlopen(req, timeout=settings.REQUEST_TIMEOUT)
                    callback = json.loads(res_data.read())
                    print("\033[31;1m[%s]:[%s]\033[0m response:\n%s" %(method, url, callback))
                    return callback
                except Exception as e:
                    sys.exit(e)
        else:
            raise KeyError


    def __update_asset_id(self, asset_id):
        asset_id_file = settings.ASSET_ID_FILE
        f = open(asset_id_file, 'wb')
        f.write(str(asset_id))
        f.close()

    def __attach_token(self, url):
        user = settings.USER
        token = settings.TOKEN
        md5_token, timestamp = api_token.get_token(user, token)
        url_argv_str = "user=%s&timestamp=%s&token=%s" % (user, timestamp, md5_token)
        if "?" in url:
            new_url = url + "&" + url_argv_str
        else:
            new_url = url + "?" + url_argv_str
        return new_url

    def log_record(self, log):
        # logger = logging.getLogger(__name__)
        logging.basicConfig(filename=settings.LOG_FILE, level=logging.INFO,
                            format="%(asctime)s %(levelname)-8s: %(message)s")
        if type(log) is str:
            pass
        if type(log) is dict:
            if "info" in log:
                for msg in log["info"]:
                    logging.info(msg)
            if "error" in log:
                for msg in log["error"]:
                    logging.error(msg)
            if "warning" in log:
                for msg in log["warning"]:
                    logging.warning(msg)




# if __name__ == "__main__":
#     ArgvProcessor(sys.argv)
