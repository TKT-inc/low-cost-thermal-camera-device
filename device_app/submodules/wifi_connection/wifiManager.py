from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
import NetworkManager
import subprocess
import uuid
import time

class WifiManager:
    
    def __init__(self):
        self.ssids = []

    def getAvailableWifis(self):
        subprocess.run(['sudo','nmcli', "d", "wifi", "rescan"])
        time.sleep(3)

        NM_SECURITY_NONE       = 0x0
        NM_SECURITY_WEP        = 0x1
        NM_SECURITY_WPA        = 0x2
        NM_SECURITY_WPA2       = 0x4
        NM_SECURITY_ENTERPRISE = 0x8

        self.ssids = [] # list we return

        for dev in NetworkManager.NetworkManager.GetDevices():
            if dev.DeviceType != NetworkManager.NM_DEVICE_TYPE_WIFI:
                continue
            for ap in dev.GetAccessPoints():

                # Get Flags, WpaFlags and RsnFlags, all are bit OR'd combinations 
                # of the NM_802_11_AP_SEC_* bit flags.
                # https://developer.gnome.org/NetworkManager/1.2/nm-dbus-types.html#NM80211ApSecurityFlags

                security = NM_SECURITY_NONE

                # Based on a subset of the flag settings we can determine which
                # type of security this AP uses.  
                # We can also determine what input we need from the user to connect to
                # any given AP (required for our dynamic UI form).
                if ap.Flags & NetworkManager.NM_802_11_AP_FLAGS_PRIVACY and \
                        ap.WpaFlags == NetworkManager.NM_802_11_AP_SEC_NONE and \
                        ap.RsnFlags == NetworkManager.NM_802_11_AP_SEC_NONE:
                    security = NM_SECURITY_WEP

                if ap.WpaFlags != NetworkManager.NM_802_11_AP_SEC_NONE:
                    security = NM_SECURITY_WPA

                if ap.RsnFlags != NetworkManager.NM_802_11_AP_SEC_NONE:
                    security = NM_SECURITY_WPA2

                if ap.WpaFlags & NetworkManager.NM_802_11_AP_SEC_KEY_MGMT_802_1X or \
                        ap.RsnFlags & NetworkManager.NM_802_11_AP_SEC_KEY_MGMT_802_1X:
                    security = NM_SECURITY_ENTERPRISE

                #print(f'{ap.Ssid:15} Flags=0x{ap.Flags:X} WpaFlags=0x{ap.WpaFlags:X} RsnFlags=0x{ap.RsnFlags:X}')

                # Decode our flag into a display string
                security_str = ''
                if security == NM_SECURITY_NONE:
                    security_str = 'NONE'
        
                if security & NM_SECURITY_WEP:
                    security_str = 'WEP'
        
                if security & NM_SECURITY_WPA:
                    security_str = 'WPA'
        
                if security & NM_SECURITY_WPA2:
                    security_str = 'WPA2'
        
                if security & NM_SECURITY_ENTERPRISE:
                    security_str = 'ENTERPRISE'

                entry = {"ssid": ap.Ssid, "security": security_str, "strength": ap.Strength }

                if self.ssids.__contains__(entry):
                    continue

                self.ssids.append(entry)
        self.ssids.sort(key=lambda x: x["strength"], reverse=True)
        return self.ssids

    def connectNewWifi(self, ssid, password, username="" , conn_name=""):
        wifiInfo = None
        for wifi in self.ssids:
            # orubt
            if (wifi["ssid"] == ssid):
                wifiInfo = wifi
                break
        if wifiInfo is None:
            return 'FAILED: Can not find this ssid'

        if (conn_name == ""):
            conn_name = ssid

        try:
            # This is what we use for "MIT SECURE" network.
            enterprise_dict = {
                '802-11-wireless': {'mode': 'infrastructure',
                                    'security': '802-11-wireless-security',
                                    'ssid': ssid},
                '802-11-wireless-security': 
                    {'auth-alg': 'open', 'key-mgmt': 'wpa-eap'},
                '802-1x': {'eap': ['peap'],
                        'identity': username,
                        'password': password,
                        'phase2-auth': 'mschapv2'},
                'connection': {'id': conn_name,
                            'type': '802-11-wireless',
                            'uuid': str(uuid.uuid4()),
                            'auth-retries': 5},
                'ipv4': {'method': 'auto'},
                'ipv6': {'method': 'auto'}
            }

            # No auth, 'open' connection.
            none_dict = {
                '802-11-wireless': {'mode': 'infrastructure',
                                    'ssid': ssid},
                'connection': {'id': conn_name,
                            'type': '802-11-wireless',
                            'uuid': str(uuid.uuid4())},
                'ipv4': {'method': 'auto'},
                'ipv6': {'method': 'auto'}
            }

            # Hidden, WEP, WPA, WPA2, password required.
            passwd_dict = {
                '802-11-wireless': {'mode': 'infrastructure',
                                    'security': '802-11-wireless-security',
                                    'ssid': ssid},
                '802-11-wireless-security': 
                    {'key-mgmt': 'wpa-psk', 'psk': password},
                'connection': {'id': conn_name,
                            'type': '802-11-wireless',
                            'uuid': str(uuid.uuid4()),
                            'auth-retries': 5},
                'ipv4': {'method': 'auto'},
                'ipv6': {'method': 'auto'}
            }
            # print(passwd_dict)

            conn_dict = None
            # conn_str = ''

            if wifiInfo["security"] == 'NONE':
                conn_dict = none_dict 
            
            if wifiInfo["security"] == 'WEP' or wifiInfo["security"] == 'WPA' or wifiInfo["security"] == 'WPA2' :
                conn_dict = passwd_dict 

            if wifiInfo["security"] == 'ENTERPRISE':
                conn_dict = enterprise_dict

            if conn_dict is None:
                # print(f'connect_to_AP() Error: Invalid conn_type="{conn_type}"')
                return 'FAILED: Invalid connection type'

            for connection in NetworkManager.Settings.ListConnections():
                settings = connection.GetSettings()['connection']
                if settings['id'] == ssid:
                    break;
            else:
                NetworkManager.Settings.AddConnection(conn_dict)

            # Now find this connection and its device
            connections = NetworkManager.Settings.ListConnections()
            connections = dict([(x.GetSettings()['connection']['id'], x) for x in connections])
            conn = connections[conn_name]

            # Find a suitable device
            ctype = conn.GetSettings()['connection']['type']
            dtype = {'802-11-wireless': NetworkManager.NM_DEVICE_TYPE_WIFI}.get(ctype,ctype)
            devices = NetworkManager.NetworkManager.GetDevices()

            for dev in devices:
                if dev.DeviceType == dtype:
                    break
            else:
                return 'FAILED: No suitable and available {ctype} device found.'

            # And connect
            if (self.wifiConnected()):
                return 'SUCCESS'
            NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")
            # print(f"Activated connection={conn_name}.")

            # Wait for ADDRCONF(NETDEV_CHANGE): wlan0: link becomes ready
            # print(f'Waiting for connection to become active...')
            loop_start = time.time()
            while dev.State != NetworkManager.NM_DEVICE_STATE_ACTIVATED and time.time() - loop_start < 80:
                #print(f'dev.State={dev.State}')
                time.sleep(1)

            if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
                print(f'Connection {conn_name} is live.')
                return 'SUCCESS'
            else:
                return 'FAILED: can not establish the connection'

        except Exception as e:
            return f'FAILED: Connection error: {e}'

    def wifiConnected(self):
        devices = NetworkManager.NetworkManager.GetDevices()
        for dev in devices:
            if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI and dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
                return True
        return False