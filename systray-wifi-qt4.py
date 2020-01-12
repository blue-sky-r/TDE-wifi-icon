#!/usr/bin/python

"""
    Systray icon showing wifi singnal strength on remote device (wifi repeater etc)

    Designed for TDE (whch is Qt3 based), but implemented for Qt4 as Qt3 (TQt) is missing QSystemTrayIcon class

    Note: QSound is not working (broken ?) - so no audible notifications for now

"""

import sys, os
from PyQt4 import QtGui, QtCore
import urllib2
import re


class SystemTrayIcon(QtGui.QSystemTrayIcon):
    """ system tray icon showing wifi signal strength on remore device """

    def __init__(self, icon, parent=None):
        """ init"""
        QtGui.QSystemTrayIcon.__init__(self, icon, parent)
        # menu - exit
        self.menu = QtGui.QMenu(parent)
        exitAction = self.menu.addAction("Exit")
        self.setContextMenu(self.menu)
        # menu refresh
        QtCore.QObject.connect(exitAction,QtCore.SIGNAL('triggered()'), self.exit)
        refreshAction = self.menu.addAction("Refresh")
        self.setContextMenu(self.menu)
        QtCore.QObject.connect(refreshAction, QtCore.SIGNAL('triggered()'), self.update)
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
        """ load resources - icons from dir identified by name with extension ext """
        path = '/'.join([dir, name + ext])
        return QtGui.QIcon(path) if os.path.exists(path) else None

    def _load_sound(self, dir, name, ext=['.ogg', '.mp3', '.wav']):
        """ load resources - sound file from dir identified by name, try ext extensions (the first wins) """
        dirname = '/'.join([dir, name])
        for e in ext:
            path = dirname + e
            if os.path.exists(path):
                return QtGui.QSound(path)
        return None

    def cfg_signal_table(self, levelstr, dir, ext='.png', sep=':,'):
        """ build configurable signal table - signal_level:icon_name, ... from string from config file """
        self.signal = []
        for lvl_txt in levelstr.strip().split(sep[1]):
            level, txt = lvl_txt.strip().split(sep[0])
            level, txt = level.strip(), txt.strip()
            item = {
                # numeric level Q10 (Q*10)
                'level': int(level),
                # signal description - low, medium, high, error
                'signal': txt,
                # preloaded icon resource
                'icon':  self._load_icon(dir, txt),
                # preloaded audible notification
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
        """ get icon for signal text txt (used for error when level is not available) """
        return [ i['icon'] for i in self.signal if i['signal'] == txt ][0]

    def cfg_device(self, device):
        """ configure device to monitor """
        self.device = device

    def check_device(self, device):
        """ get data from monitored (remote) device """
        res = {
            'signal': 'error',
            'desc': '?'
        }
        try:
            #                          MAC           if    uutime     Tx    Rx   signal noise SNR Q10
            # setWirelessTable('00:26:18:85:25:87','eth1','0:28:11','39M','78M','-57','-79','22','453');
            for line in urllib2.urlopen(device['url'], timeout=device['timeout']).readlines():
                m = re.search(device['regex'], line)
                if m:
                    return m.groupdict()
            res = {
                'signal': 'nocon',
                'desc': device['no_wifi']
            }
        except urllib2.HTTPError as e:
            res['desc'] = device['http_error'] % { 'errno': e.code, 'strerror': e.reason }
        except urllib2.URLError as e:
            res['desc'] = device['url_error'] % { 'errno': e.reason.errno, 'strerror': e.reason.strerror }
        return res

    def callculate(self, d):
        """ calculate Q, SN fields """
        if d.get('Q10'):
            d['Q'] = int(d['Q10']) // 10
            d['SN'] = int(d['signal']) - int(d['noise'])
        return d

    def update(self):
        res = self.test_data() if hasattr(self, 'data') else self.check_device(self.device)
        # if ok (got Q10)
        if res.get('Q10'):
            # valid data {Q10: 123, SNR: 30} so calculate Q,SN fields
            res = self.callculate(res)
            tooltip = self.device['tooltip'] % res
            entry = self.get_entry_for_level(res[self.device['tab_key']])
            #self.play_sound(entry['sound'])
            icon = entry['icon']
        else:
            # error 'signal':'nocon', 'desc':description
            icon = self.get_icon_for_signal(res['signal'])
            tooltip = self.device['tooltip_error'] % res
        self.setIcon(icon)
        self.setToolTip(tooltip)

    def play_sound(self, sound):
        """ audible notification """
        #QtGui.QSound(file).play()
        if sound: sound.play()

    def test_data(self, data=None):
        """ diagnostic data """
        # initiate data if provided
        if data:
            self.data, self.data_idx = data, 0
            return
        # get actual entry
        d = self.data[self.data_idx]
        # next in round-robin fasion
        self.data_idx = (self.data_idx + 1) % len(self.data)
        # return diag entry
        return d


def main():
    """ main - instatiate app, read/process config and execute """

    # application
    app = QtGui.QApplication(sys.argv[1:])

    # default icon
    style = app.style()
    icon = QtGui.QIcon(style.standardPixmap(QtGui.QStyle.SP_ComputerIcon))
    wifiIcon = SystemTrayIcon(icon)

    # config
    app_dir = os.path.dirname(sys.argv[0])

    # signal table
    #
    # signal_level:icon_name - signal_level can be Q,Q10,SNR,SN based on tab_key
    # negative numbers are for error conditions so they can be arbitrary negative number
    # entries are trimmed so whitespaces are removed before processing
    wifiIcon.cfg_signal_table('-2:error, -1:nocon, 0:low, 16:medium, 35:high', app_dir + '/icon/128')

    # remote device
    #
    device = {
        # device to check
        'url': 'http://rep2',
        # dd-wrt r22000++ king-kong
        #'regex': r"setWirelessTable\('(?P<MAC>.+)',"
        #         r"'(?P<if>.+)','(?P<uptime>.+)','(?P<TXrate>.+)','(?P<RXrate>.+)',"
        #         r"'(?P<signal>.+)','(?P<noise>.+)','(?P<SNR>\d+)','(?P<Q10>\d+)'\);",
        # dd-wrt r41328
        'regex': r"setWirelessTable\('(?P<MAC>.+)',"
                 r"'(?P<rname>.*)','(?P<if>.+)','(?P<uptime>.+)','(?P<TXrate>.+)','(?P<RXrate>.+)',"
                 r"'(?P<info>.+)','(?P<signal>.+)','(?P<noise>.+)','(?P<SNR>\d+)','(?P<Q10>\d+)'\);",
        # connect timeout
        'timeout': 3,
        # key for signal table - one of Q, Q10, SNR, SN
        'tab_key': 'Q',
        # ok tooltip
        'tooltip': "SNR: %(SNR)s / SN: %(SN)d / Q: %(Q)d%%",
        # error tooltip
        'tooltip_error': 'ERR: %(desc)s',
        # error message - no wifi connection to AP
        'no_wifi': 'no wifi connection',
        # error message - http error - supported keys: errno, strerror
        'http_error': 'http %(strerror)s',
        # error message - url error - supported keys: errno, strerror
        'url_error':  'url %(strerror)s',
    }
    wifiIcon.cfg_device(device)

    # execute diagnostic test without quering remote device
    tdata = [
        {'signal': 'error', 'desc': 'connection timeout'},
        {'signal': 'nocon', 'desc': 'no wifi connection'},
        {'Q10': '0',   'SNR': '-5'},
        {'Q10': '150', 'SNR': '5'},
        {'Q10': '350', 'SNR': '15'},
        {'Q10': '500', 'SNR': '25'},
        {'Q10': '750', 'SNR': '35'},
        {'Q10': '1000', 'SNR': '55'}
    ]
    #wifiIcon.test_data(tdata)

    # run
    wifiIcon.show()
    wifiIcon.autoupdate(30)
    sys.exit(app.exec_())


# MAIN
#
if __name__ == '__main__':
    main()
