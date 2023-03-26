# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import network
import ubinascii
import gc
import neopixel
from machine import Pin
import utime

SSID_SOFTAP_PREFIX = "hover-"
PASWORD_SOFTAP = "12345678"
WIFI_SOFTAP_CHANNEL = const(6)

# pin configuration
motorpin = Pin(4, Pin.OUT)
servopin = Pin(5, Pin.OUT)
led_pin = Pin(7, Pin.OUT)

# ----------------------------------------------------------------------------
# led control functions
led_is_on = False
pixels = neopixel.NeoPixel(led_pin, 1)

def led_on():
    global led_is_on
    pixels[0] = (0, 20, 0) # GRB
    pixels.write()
    led_is_on = True
    
def led_off():
    global led_is_on
    pixels[0] = (0, 0, 0) # GRB
    pixels.write()
    led_is_on = False

def led_toggle(t=None):
    global led_is_on
    if led_is_on:
        led_off()
    else:
        led_on()

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
ap.config(channel=WIFI_SOFTAP_CHANNEL, essid=ssid, authmode=network.AUTH_WPA_WPA2_PSK, password=PASWORD_SOFTAP)
print('ssid:', ssid)

while ap.active() == False:
    pass
    
print('network config:', ap.ifconfig())

gc.collect()

