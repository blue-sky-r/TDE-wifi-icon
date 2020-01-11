#!/usr/bin/python

import sys, os
from PyQt4 import QtGui, QtCore
import urllib2
import re


class SystemTrayIcon(QtGui.QSystemTrayIcon):
    """ system tray icon showing wifi signal strength on remore device """

    def __init__(self, icon, parent=None):
        """ init"""
        QtGui.QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QtGui.QMenu(parent)
        exitAction = self.menu.addAction("Exit")
        self.setContextMenu(self.menu)
        QtCore.QObject.connect(exitAction,QtCore.SIGNAL('triggered()'), self.exit)
        #
        self.timer = QtCore.QTimer()
        QtCore.QTimer.connect(self.timer, QtCore.SIGNAL("timeout()"), self.update)

    def exit(self):
        """ exit has been pressed """
        QtCore.QCoreApplication.exit()

    def autoupdate(self, sec=60):
        """ refresh icon every sec seconds """
        self.update()
        self.timer.start(sec * 1000)

    def _load_icon(self, dir, name, ext='.png'):
        path = '/'.join([dir, name + ext])
        return QtGui.QIcon(path) if os.path.exists(path) else None

    def _load_sound(self, dir, name, ext=['.ogg', '.mp3', '.wav']):
        dirname = '/'.join([dir, name])
        for e in ext:
            path = dirname + e
            if os.path.exists(path):
                return QtGui.QSound(path)
        return None

    def cfg_signal_table(self, levelstr, dir, ext='.png', sep=':,'):
        """ configure signal_level:icon_name, ... """
        self.signal = []
        for lvl_txt in levelstr.strip().split(sep[1]):
            level, txt = lvl_txt.strip().split(sep[0])
            level, txt = level.strip(), txt.strip()
            item = {
                'level': int(level),
                'signal': txt,
                'icon':  self._load_icon(dir, txt),
                'sound': self._load_sound(dir, txt)
            }
            self.signal.append(item)
        return

    def get_entry_for_level(self, level):
        """ get signal table entry for sugnal level """
        entry = None
        for tab in self.signal:
            if level < tab['level']: break
            entry = tab
        return entry

    def get_icon_for_signal(self, txt):
        """ get icon for signal text txt """
        return [ i['icon'] for i in self.signal if i['signal'] == txt ][0]

    def check_url(self, url='http://rep2',
                  regex=r"setWirelessTable\('(?P<MAC>.+)','(?P<if>.+)','(?P<uptime>.+)','(?P<TXrate>.+)','(?P<RXrate>.+)','(?P<signal>.+)','(?P<noise>.+)','(?P<SNR>\d+)','(?P<Q10>\d+)'\);"):
        error, desc = 'error', '?'
        try:
            #                          MAC           if    uutime     Tx    Rx   signal noise SNR Q10
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
        res = self.test_data() if self.diag is not None else self.check_url()
        # if ok
        if type(res) is dict:
            # valid data {Q10: 123, SNR: 30}
            quality = int(res['Q10']) // 10
            tooltip = "SNR: %(SNR)s / Q10: %(Q10)s" % res
            entry = self.get_entry_for_level(quality)
            #self.play_sound(entry['sound'])
            icon = entry['icon']
        else:
            # error tuple (error, description)
            icon = self.get_icon_for_signal(res[0])
            tooltip = 'ERR: %s' % res[1]
        self.setIcon(icon)
        self.setToolTip(tooltip)

    def play_sound(self, sound):
        #QtGui.QSound(file).play()
        sound.play()

    def test_data(self):
        #import random
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
        #d = random.choice(data)
        d = data[self.diag]
        self.diag = (self.diag + 1) % len(data)
        return d


def main():
    app = QtGui.QApplication(sys.argv[1:])

    style = app.style()
    icon = QtGui.QIcon(style.standardPixmap(QtGui.QStyle.SP_ComputerIcon))
    wifiIcon = SystemTrayIcon(icon)

    app_dir = os.path.dirname(sys.argv[0])
    # signal_level:icon_name
    wifiIcon.cfg_signal_table('-2:error, -1:nocon, 0:low, 20:medium, 50:high', app_dir + '/icon/128')

    # execute diagnostic test without quering remote device
    app.diag = 1

    app.show()
    wifiIcon.autoupdate(5)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
