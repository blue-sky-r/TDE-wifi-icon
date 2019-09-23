#!/usr/bin/python

import sys, os
from PyQt4 import QtGui, QtCore
import urllib2
import re
import random


class SystemTrayIcon(QtGui.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QtGui.QMenu(parent)
        exitAction = self.menu.addAction("Exit")
        self.setContextMenu(self.menu)
        QtCore.QObject.connect(exitAction,QtCore.SIGNAL('triggered()'), self.exit)
        #
        self.timer = QtCore.QTimer()
        QtCore.QTimer.connect(self.timer, QtCore.SIGNAL("timeout()"), self.update)
        self.timer.start(10000)
        #
        self.test = True

    def exit(self):
        QtCore.QCoreApplication.exit()

    def _load_icon(self, dir, name, size=128, ext='.png'):
        path = '/'.join([dir, "%s" % size, name + ext])
        return QtGui.QIcon(path) if os.path.exists(path) else None

    def _load_sound(self, dir, name, ext=['.ogg', '.mp3', '.wav']):
        dirname = '/'.join([dir, name])
        for e in ext:
            path = dirname + e
            if os.path.exists(path):
                return QtGui.QSound(path)
        return None

    def parse_str(self, levelstr, dir, size=128, ext='.png'):
        self.signal = []
        for lvl_txt in levelstr.split(','):
            level, txt = lvl_txt.split(':')
            item = {
                'level': int(level),
                'signal': txt,
                'icon':  self._load_icon(dir, txt),
                'sound': self._load_sound(dir, txt)
            }
            self.signal.append(item)
        return

    def get_icon_for_level(self, level):
        icon = None
        for l in self.signal:
            if level < l['level']: break
            icon = l['icon']
        return icon

    def get_icon_for_signal(self, txt):
        return [ i['icon'] for i in self.signal if i['signal'] == txt ][0]

    def check_url(self, url='http://rep', regex=r"setWirelessTable\('(?P<MAC>.+)','(?P<if>.+)','(?P<uptime>.+)','(?P<TXrate>.+)','(?P<RXrate>.+)','(?P<signal>.+)','(?P<noise>.+)','(?P<SNR>\d+)','(?P<Q10>\d+)'\);"):
        error, desc = 'error', ''
        try:
            # setWirelessTable('00:26:18:85:25:87','eth1','0:28:11','39M','78M','-57','-79','22','453');
            for line in urllib2.urlopen(url, timeout=3).readlines():
                m = re.search(regex, line)
                if m: return m.groupdict()
            error, desc = 'nocon', 'no wifi connection'
        except urllib2.HTTPError as e:
            desc = e.strerror
        except urllib2.URLError as e:
            desc = e.reason.strerror
        return error, desc

    def update(self):
        res = self.test_data() if self.test else self.check_url()
        # ok
        if type(res) is dict:
            quality = int(res['Q10']) // 10
            tooltip = "SNR: %(SNR)s / Q: %(Q10)s" % res
            icon = self.get_icon_for_level(quality)
        else:
            icon = self.get_icon_for_signal(res[0])
            tooltip = 'ERR: %s' % res[1]
        self.setIcon(icon)
        self.setToolTip(tooltip)

    def play_sound(self, file):
        QtGui.QSound(file).play()

    def test_data(self):
        data = [
            ('error','connection timeout'),
            ('nocon','no wifi connection'),
            {'Q10':    '0', 'SNR': '-5'},
            {'Q10':  '150', 'SNR':  '5'},
            {'Q10':  '350', 'SNR': '15'},
            {'Q10':  '500', 'SNR': '25'},
            {'Q10':  '750', 'SNR': '35'},
            {'Q10': '1000', 'SNR': '55'}
        ]
        d = random.choice(data)
        return d


def main():
    app = QtGui.QApplication(sys.argv[1:])
    style = app.style()
    icon = QtGui.QIcon(style.standardPixmap(QtGui.QStyle.SP_ComputerIcon))
    wifiIcon = SystemTrayIcon(icon)

    app_dir = os.path.dirname(sys.argv[0])
    # signal_level:icon_name
    wifiIcon.parse_str('-2:error,-1:nocon,0:low,35:medium,70:high', app_dir + '/icon')

    wifiIcon.show()
    #wifiIcon.update()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
