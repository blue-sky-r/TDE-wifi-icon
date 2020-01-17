## SystemTray Icon for WiFi signal

SystemTray Icon is a PyQt script for TDE (KDE 3.x) to depict WiFi signal strength on remote (networked) device.

The remote device is usually a router (client, client/bridge, repeater, repeater/bridge mode) on local LAN segment
to provide connectivity to another (adjancent) LAN segment. Due to nature of wifi there are fluctuations and collisions
affecting the quality of this intersegment wifi link. Therefore is necessary to provide simple visual feedback 
of the link quality (rx/tx speed) to the user. The SysTray icon is the obvious solution.  

![SysTray-WiFi-icon](screen/signal-high.png)

### config

The current PyQt implementation is based on hardcoded config, however it is quite easy to read and edit Python code.

_Note: The separate ini-file based configuration is on TO-DO list._
 
### how it works

* The script periodicaly queries the wifi status web page (dd-wrt info page)

* The wireless access point information line is parsed and each column value is extracted.

* A few other values are calculated from existing ones and actual Tooltip is constructed.

* Based on preconfigured table for signal value lookup to get corresponding icon and optional audible sound
  (Please note that audio notifications are not functional due to problems with QSound in PyQt)

* The new icon is rendered in systray area corresponding tootip

* There is a menu on right-click with just two actions (for now)

 * refresh - force manual refresh of icon and tooltip (addtionally to periodical updates from QTimer)
 * exit - stop monitoring end exit
 

### implementation

The current implementation is intended for [TDE - Trinity Desktop Environment](http://www.trinitydesktop.org) as 
continuation of classic KDE 3.x (which was replaced by KDE 4/5 so all great KDE 3 concepts were forgotten). It might work on other KDE based
environments if they support [QSystrayIcon](http://qt.com/) class from Qt4/5.

Implementation is done with Pyton3 and PyQt5 so additional required packages has to be installed:
PyQt5

![SysTray-WiFi-icon](screen/demo.gif)

### to do


