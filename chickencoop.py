import paho.mqtt.client as mqtt
import Adafruit_DHT
from datetime import datetime, time, timedelta, timezone
import time
import requests
import json

MQTT_broker = "192.168.1.8"
sub_topic01 = "test01"
sub_topic02 = "test02"
sub_topics = [("chickencoop/door", 0), ("chickencoop/test",0) ]
pub_topics = [("chickencoop/temperature", 0), ("chickencoop/humidity", 0), ("chickencoop/time",0)]
door_open=false
reed_switch = 13#numer pinu
# --------------------------Temperature-------------
def get_temp():
    sensor = Adafruit_DHT.DHT11
    pin_DHT11 = 14  # GPIO 23
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin_DHT11)
    if humidity is not None and temperature is not None:
        print("Temp: {}, humidity: {}".format(temperature, humidity))
        #client.publish.single("temperature", temperature, hostname=MQTT_broker)
        #client.publish.single("humidity", humidity, hostname=MQTT_broker)
    return temperature,humidity
#--------------------------Time----------------------
def get_sunrise_sunset():
    latitude = 50.907034 #latitude for API to get sunrise,sunset
    longitude = 16.653227 #longitude for API to get sunrise,sunset
    url = "https://api.sunrise-sunset.org/json?lat=" + str(latitude) + "&lng=" + str(
        longitude) + "&formatted=0"  # URL, change lat and lng
    r = requests.get(url)  # query data
    data = json.loads(r.content)
    sunrise = data['results']['sunrise']
    sunset = data['results']['sunset']
    sunrise_time = time(int(sunrise[11:13]), int(sunrise[14:16]))  # Change sunrise in time format
    sunset_time = time(int(sunset[11:13]), int(sunset[14:16]))  # Change sunset into time format
    sunrise_time_obj = datetime.strptime(str(sunrise_time),
                                         '%H:%M:%S')  # Change sunrise into datetime format so it can be compared
    sunset_time_obj = datetime.strptime(str(sunset_time),
                                        '%H:%M:%S')  # Change sunset into datetime format so it can be compared
    return sunrise_time_obj.time(),sunset_time_obj.time()
def get_times():
    d = datetime.now()  # - timedelta(hours=2)
    today_date = d.date()  # date today
    time_utc = d.astimezone(tz=timezone.utc).time()
    #print(time_comparison)
    #print(sunrise_time_obj.time())
    #if str(sunrise[0:10]) != str(today_date):  # different date? Get new data
    #    r = requests.get(url)
    return time_utc, d.strftime("%d %m %Y %H:%M:%S")
#-----------------------Stepper_motor---------------
def calibration():
    if reed_switch: # jesli stan jest wysoki to znaczy ze jest na gorze/dole
        while not reed_switch: #poki jest na dole to podnos
            #podnos
            door_open=true

# -------------------------MQTT---------------------
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("test_topic")
    client.subscribe(sub_topics)
    # client.subscribe(sub_topic02)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    topic = msg.topic
    m_decode = str(msg.payload.decode("utf-8"))
#	    print("Topic: " + topic + ", message: " + m_decode)
    message_handler(client, m_decode, topic)

def message_handler(client, msg, topic):
    if topic == sub_topics[0][0]:
        if msg == "up":
            #Go up
        elif msg == "down":
            #go down
    else:
        print("Topic: " + topic + ", message: " + msg)



client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.1.8", 1883, 60)
client.loop_start()
while True:
    temp,hum=get_temp()
    sunrise, sunset = get_sunrise_sunset()
    utc_time, pub_time = get_times()
    client.publish(pub_topics[0][0],str(temp))
    client.publish(pub_topics[1][0],str(hum))
    client.publish(pub_topics[2][0], pub_time)
    if utc_time > sunrise and not door_open:
        #Go up
        door_open = true
    if utc_time > sunset and door_open:
        #Go down
        door_open = close

    time.sleep(600) #waiting 10min

client.loop_stop()
client.disconnect()
# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
#client.loop_forever()
