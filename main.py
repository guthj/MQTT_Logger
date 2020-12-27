#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 16:41:54 2020

@author: janguth
"""

import os
from datetime import datetime
from time import sleep

import paho.mqtt.client as mqtt
# from apscheduler.schedulers.background import BackgroundScheduler

debuglevel = 5
debugStr = ["None  :  ", "Error :  ", "Notice:  ", "Info  :  ", "Debug :  "]

plants = ["AlocasiaZ", "CalathiaM", "Avocado"]

plantResponses = []
unresponsivePlants = []
plantsUnresponsive = False
os.chdir(os.path.dirname(__file__))

pathSave = ""

for plant in plants:
    plantResponses.append(True)

plantLog = []

plantLogLenght = 50

for i in range(len(plants)):
    plantLogging = []
    for a in range(plantLogLenght):
        plantLogging.append("")
    plantLog.append(plantLogging)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    if rc == 0:
        print("-> This means we connected successfully")
        log("Connection to server successfull", 2)
    else:
        print("Major connection error")
        raise SystemExit

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    for plant in plants:
        client.subscribe(plant + "/Ping/Response")
        client.subscribe(plant + "/Log")
    client.subscribe("Logger/Save")


def on_message(client, userdata, msg):
    messageText = str(msg.payload, 'utf-8')
    print(msg.topic + " " + str(msg.payload))
    log(msg.topic + " -> " + messageText, 4)
    # CHECK FOR PLANT SPECIFIC MESSAGES
    for i in range(len(plants)):
        if msg.topic == plants[i] + "/Log":
            plantLog[i].pop(0)
            dateTimeObj = datetime.now()
            timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S)")
            plantLog[i].append(timestampStr + " " + messageText + "\n")

        if msg.topic == plants[i] + "/Ping/Response":
            plantResponses[i] = True
    if msg.topic == "Logger/Save":
        saveLogs()


def saveLogs():
    for i in range(len(plants)):
        if plantLog[i][plantLogLenght-1] != "":
            try:
                with open(pathSave + plants[i] + ".txt", 'w') as txtfile:
                    txtfile.writelines(plantLog[i])

            except:
                log("Couldn't save values for " + plants[i], 1)
        else:
            log("No new logs for for " + plants[i], 1)


def pingEveryone():
    unresponsivePlants = []
    plantsUnresponsive = False
    for i in range(len(plants)):
        if (plantResponses[i] == False):
            unresponsivePlants.append(i)
            plantsUnresponsive = True
        plantResponses[i] = False

    for plant in plants:
        client.publish(plant + "/Ping/Send", "Ping")


def sendAlarms():
    if plantsUnresponsive:
        for plant in unresponsivePlants:
            client.publish(plants[plant] + "/Alarm", "true")
            sleep(3)
            client.publish(plants[plant] + "/Alarm", "false")


def log(text, level):
    if level <= debuglevel:
        print(debugStr[level] + text)
        client.publish("Logger/Log", debugStr[level] + text)


if __name__ == "__main__":
    sleep(10.0)  # wait for everything to connect (Wifi, etc)
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("10.0.0.16", 1883, 60)
    client.loop_start()
    sleep(2)
    log("MQTT Started", 2)
    log("Waiting For Everything To Settle", 2)
    sleep(5)
    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.

    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(pingEveryone, 'interval', minutes=39)
    scheduler.add_job(sendAlarms, 'cron', hour=18, minute=0, second=0)

    try:
        while (True):
            sleep(10)


    except KeyboardInterrupt:
        saveLogs()
        print("Exiting program")


    finally:

        print("done")
