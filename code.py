# OLED Pinout : GP6 - SDA, GP7 - SCL
# Installing CircuitPython - https://learn.adafruit.com/getting-started-with-raspberry-pi-pico-circuitpython/circuitpython
import time
import busio as io
import adafruit_ssd1306
import time
import busio
import adafruit_espatcontrol.adafruit_espatcontrol_socket as socket
from adafruit_espatcontrol import adafruit_espatcontrol
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import board
import analogio
from math import log
import time_api as t
import rtc

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

sleep_duration = 10
deviceid = secrets["deviceid"]
# Grove - Temperature Sensor
sensor_read = analogio.AnalogIn(board.GP27)
potentiometer = sensor_read     # Grove - Temperature Sensor connect to A0
B = 4275;               # B value of the thermistor
R0 = 100000;            # R0 = 100k
#print(sensor_read.value)

def convert(x,in_min,in_max,out_min,out_max):
    return(x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min
# #Grove temperature
def get_temperature():
	# #Grove temperature
	tb = convert(potentiometer.value,0,65535,0,1023)
	R = ((1023.0/tb)-1.0) * R0
	tempGrove = round((1.0/ (log(R/100000)/B+1/298.15) )-273.15,0)
	#print("Grove temperature  %.0f " %(tempGrove))
	return tempGrove
tempGrove  = get_temperature()

#oled init
i2c = io.I2C(board.GP7, board.GP6)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
oled.fill(0)
oled.text('Starting.....!',30,10, 1)
oled.show()

# Initialize UART connection to the ESP8266 WiFi Module.
RX = board.GP17
TX = board.GP16
uart = busio.UART(
    TX, RX, receiver_buffer_size=2048
)  # Use large buffer as we're not using hardware flow control.

esp = adafruit_espatcontrol.ESP_ATcontrol(uart, 115200, debug=False)

# wifi = adafruit_espatcontrol_wifimanager.ESPAT_WiFiManager(esp, secrets)

wifi = adafruit_espatcontrol.ESP_ATcontrol(uart, 115200, debug=False)

mqtt_topic = "nodered/topic"

### Code ###
# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    print("Connected to MQTT Broker!")
    print("Flags: {0}\n RC: {1}".format(flags, rc))


def disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    print("Disconnected from MQTT Broker!")


def subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client unsubscribes from a feed.
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))


def publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    print("Published to {0} with PID {1}".format(topic, pid))


def message(client, topic, message):
    # Method called when a client's subscribed feed has a new value.
    print("New message on topic {0}: {1}".format(topic, message))


# Initialize MQTT interface with the esp interface
MQTT.set_socket(socket,esp)
mqtt_client = MQTT.MQTT(
    broker=secrets["broker"],
    port=secrets["port"],
    username=secrets["aio_username"],
    password=secrets["aio_key"],
)

# Connect to WiFi
print("Connecting to WiFi...")
wifi.connect(secrets=secrets)
print("Connected!")
local_ip = wifi.local_ip
print("ip:" + str(local_ip))
oled.fill(0)
oled.text('Connecting to WiFi..',0,10, 1)
oled.text('Connected!',0,20, 1)
oled.text('ip:',0,30, 1)
oled.text(local_ip,0,40, 1)
oled.show()
ip = '8.8.8.8'
resp = wifi.ping(ip)
print("ping:" + str(resp))

# Connect callback handlers to mqtt_client
mqtt_client.on_connect = connect
mqtt_client.on_disconnect = disconnect
mqtt_client.on_subscribe = subscribe
mqtt_client.on_unsubscribe = unsubscribe
mqtt_client.on_publish = publish
mqtt_client.on_message = message

#Get restapi time "http://worldtimeapi.org/api/ip"
the_rtc = rtc.RTC()
time_api = t.Time_Api(esp,secrets)
time_api.connect()
the_rtc = time_api.get_time()

print(the_rtc.datetime)

while True:
    str_date = str(the_rtc.datetime.tm_year) + '-' + str(the_rtc.datetime.tm_mon) + '-' +  str(the_rtc.datetime.tm_mday)
    str_time = str(the_rtc.datetime.tm_hour) + ':' + str(the_rtc.datetime.tm_min) + ':' +  str(the_rtc.datetime.tm_sec)
    print(str_date + ' ' + str_time)
    temperature = get_temperature()
    print("Sleeping for: {0} Seconds".format(sleep_duration))
    print("Grove temperature  %.0f " %(temperature))
    print("Attempting to connect to %s" % mqtt_client.broker)
    mqtt_client.connect()
    print("Publishing to %s" % mqtt_topic)
    msg = '{"measurement":"' + deviceid + '","payload":{"temperature": ' + str(temperature) +'} }'
    print(msg)
    mqtt_client.publish(mqtt_topic,msg )
    oled.fill(0)
    oled.text('DateTime:',0,20, 1)
    oled.text(str_date + ' ' + str_time ,0,30, 1)
    oled.text('Temperature:',0,40, 1)
    oled.text(str(temperature),50,50, 1)
    oled.show()
    time.sleep(sleep_duration)
