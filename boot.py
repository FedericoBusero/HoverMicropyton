# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import network
import ubinascii
import gc
from machine import Pin
import utime

SSID_SOFTAP_PREFIX = "hover-"
PASWORD_SOFTAP = "12345678"
WIFI_SOFTAP_CHANNEL = const(6)

# pin configuration
servopin = Pin(14, Pin.OUT)
motorpin = Pin(27, Pin.OUT)
led_pin = Pin(22, Pin.OUT)

# ----------------------------------------------------------------------------
# led control functions
def led_on():
    led_pin.value(0)
    
def led_off():
    led_pin.value(1)

def led_toggle(t=None):
    global led_pin
    led_pin.value(not led_pin.value())

# ----------------------------------------------------------------------------
led_on()
utime.sleep_ms(10)
led_off()
utime.sleep_ms(100)
led_on()
utime.sleep_ms(10)
led_off()

print("setup softap")
ap = network.WLAN(network.AP_IF)
ap.active(True)
    
# Define SSID name as hover-XXXX with XXXX the last 4 hexadecimal values of the WiFi mac address
wlan_mac = ap.config('mac')
my_mac_addr = ubinascii.hexlify(wlan_mac).decode().upper()[8:12]
ssid = SSID_SOFTAP_PREFIX+my_mac_addr
ap.config(channel=WIFI_SOFTAP_CHANNEL, essid=ssid, authmode=network.AUTH_WPA_WPA2_PSK, password=PASWORD_SOFTAP)
print('ssid:', ssid)

while ap.active() == False:
    pass
    
print('network config:', ap.ifconfig())

gc.collect()
