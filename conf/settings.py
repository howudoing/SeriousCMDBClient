import os


BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = "127.0.0.1"
PORT = 9000
REQUEST_TIMEOUT = 30
URLS = {
    "asset_report_with_no_id": "/cmdb/report/asset_with_no_id",
    "asset_report": "/cmdb/report/",
}
LOG_FILE = "%s/logs/run.log" % BASEDIR
ASSET_ID_FILE = "%s/var/.asset_id" % BASEDIR
USER = "weian.li@sao.so"
TOKEN = "abcd"

