import paho.mqtt.client as mqtt
import Adafruit_DHT
from datetime import datetime, time, timedelta, timezone
import time as dtime
import requests
import json
import RPi.GPIO as GPIO

MQTT_broker = "192.168.0.21"
MQTT_port = 1883
MQTT_keep_alive = 600
sub_topics = [("chickencoop/door", 0), ("chickencoop/test", 0)]
pub_topics = [("chickencoop/temperature", 0), ("chickencoop/humidity", 0), ("chickencoop/time", 0)]
door_open = 0

# reed_switch = 13  # numer pinu
DIR = 20  # Direction GPIO Pin
STEP = 21  # Step GPIO Pin
CW = 1  # Clockwise Rotation
CCW = 0  # Counterclockwise Rotation
SPR = 200  # Steps per Revolution (360 / 1.5)

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.output(DIR, CW)

step_count = SPR
delay = .018


# --------------------------Temperature-------------
def get_temp():
    sensor = Adafruit_DHT.DHT11
    pin_DHT11 = 23  # GPIO 23, Position 16
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin_DHT11)
    if humidity is not None and temperature is not None:
        print("Temp: {}, humidity: {}".format(temperature, humidity))
        # client.publish.single("temperature", temperature, hostname=MQTT_broker)
        # client.publish.single("humidity", humidity, hostname=MQTT_broker)
    else:
        humidity = 0
        temperature = 0
    return temperature, humidity


# --------------------------Time----------------------
def get_sunrise_sunset():
    latitude = 50.907034  # latitude for API to get sunrise,sunset
    longitude = 16.653227  # longitude for API to get sunrise,sunset
    url = "https://api.sunrise-sunset.org/json?lat=" + str(latitude) + "&lng=" + str(
        longitude) + "&formatted=0"  # URL, change lat and lng
    r = requests.get(url)  # query data
    data = json.loads(r.content)
    sunrise = data['results']['sunrise']
    sunset = data['results']['sunset']
    sunrise_time =time(int(sunrise[11:13]), int(sunrise[14:16]))  # Change sunrise in time format
    sunset_time = time(int(sunset[11:13]), int(sunset[14:16]))  # Change sunset into time format
    sunrise_time_obj = datetime.strptime(str(sunrise_time),'%H:%M:%S')  # Change sunrise into datetime format so it can be compared
    sunset_time_obj = datetime.strptime(str(sunset_time),'%H:%M:%S')  # Change sunset into datetime format so it can be compared
    return sunrise_time_obj.time(), sunset_time_obj.time()


def get_times():
    d = datetime.now()  # - timedelta(hours=2)
    today_date = d.date()  # date today
    time_utc = d.astimezone(tz=timezone.utc).time()
    # print(time_comparison)
    # print(sunrise_time_obj.time())
    # if str(sunrise[0:10]) != str(today_date):  # different date? Get new data
    #    r = requests.get(url)
    return time_utc, d.strftime("%d %m %Y %H:%M:%S")


# -----------------------Stepper_motor---------------
def open(rotation=7):
    GPIO.output(DIR, CCW)
    for x in range(step_count * rotation):
        GPIO.output(STEP, GPIO.HIGH)
        dtime.sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        dtime.sleep(delay)


def close(rotation=7):
    GPIO.output(DIR, CW)
    for x in range(step_count * rotation):
        GPIO.output(STEP, GPIO.HIGH)
        dtime.sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        dtime.sleep(delay)


def calibration():
    # if reed_switch: # jesli stan jest wysoki to znaczy ze jest na gorze/dole
    while not reed_switch:  # poki jest na dole to podnos
        GPIO.output(STEP, GPIO.HIGH)
        dtime.sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        dtime.sleep(delay)
    door_open = 1


# -------------------------MQTT---------------------
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("test_topic")
    client.subscribe(sub_topics)
    # client.subscribe(sub_topic02)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    topic = msg.topic
    m_decode = str(msg.payload.decode("utf-8"))
    print("Topic: " + topic + ", message: " + m_decode)
    message_handler(client, m_decode, topic)


def message_handler(client, msg, topic):
    if topic == sub_topics[0][0]:
        if msg == "UP":
            open()
        elif msg == "DOWN":
            close()
    else:
        print("Topic: " + topic + ", message: " + msg)

#print(get_times())
#print(get_sunrise_sunset())
#open()
#dtime.sleep(2)
#close()
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_broker, MQTT_port, MQTT_keep_alive)
client.loop_start()
# calibration()
while True:
    #print(get_sunrise_sunset())
    #print(get_times())
    temp, hum = get_temp()
    sunrise, sunset = get_sunrise_sunset()
    utc_time, pub_time = get_times()
    print(temp, hum, sunrise,sunset, utc_time, pub_time)
    client.publish(pub_topics[0][0], str(temp))
    client.publish(pub_topics[1][0], str(hum))
    client.publish(pub_topics[0][0], str(temp))
    #client.publish(pub_topics[2][0], pub_time)
    # if utc_time > sunset and door_open:
    #    close()
    #    door_open = close
    # elif utc_time > sunrise and not door_open:
    #   close()
    #    door_open = true
    #if utc_time > sunset:
        #close()
        #open()
    #    print("DOWN")
    #elif utc_time > sunrise:
        #close()
   #     print("UP")

    dtime.sleep(MQTT_keep_alive)  # waiting 10min

client.loop_stop()
client.disconnect()
# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
# client.loop_forever()


