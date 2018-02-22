from plugins.linux import linux_collector
from plugins.windows import windows_collector
import platform, sys


class Collector:
    def __init__(self):
        self._collector = None
        self.info_data = self.collect()

    def collect(self):
        os_platform = platform.system()
        try:
            func = getattr(self, os_platform.lower())
            info_data = func()
            return info_data
        except AttributeError as e:
            sys.exit("Error! OS [%s] is not supported!" % os_platform)

    def linux(self):
        self._collector = linux_collector.LinuxCollector()
        return self._collector.data


    def windows(self):
        self._collector = windows_collector.WindowsCollector()
        return self._collector.data

