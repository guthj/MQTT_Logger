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
from apscheduler.schedulers.background import BackgroundScheduler
import var

os.chdir(os.path.dirname(__file__))

pathSave = ""

for plant in var.plants:
    var.plantResponses.append(True)


for i in range(len(var.plants)):
    plantLogging = []
    for a in range(var.plantLogLenght):
        plantLogging.append("")
    var.plantLog.append(plantLogging)


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
    for plant in var.plants:
        client.subscribe(plant + "/Ping/Response")
        client.subscribe(plant + "/Log")
    client.subscribe("Logger/Save")


def on_message(client, userdata, msg):
    messageText = str(msg.payload, 'utf-8')
    print(msg.topic + " " + str(msg.payload))
    log(msg.topic + " -> " + messageText, 4)
    # CHECK FOR PLANT SPECIFIC MESSAGES
    for i in range(len(var.plants)):
        if msg.topic == var.plants[i] + "/Log":
            var.plantLog[i].pop(0)
            dateTimeObj = datetime.now()
            timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S)")
            var.plantLog[i].append(timestampStr + " " + messageText + "\n")

        if msg.topic == var.plants[i] + "/Ping/Response":
            var.plantResponses[i] = True
    if msg.topic == "Logger/Save":
        saveLogs()


def saveLogs():
    for i in range(len(var.plants)):
        if var.plantLog[i][var.plantLogLenght-1] != "":
            try:
                with open(pathSave + var.plants[i] + ".txt", 'w') as txtfile:
                    txtfile.writelines(var.plantLog[i])

            except:
                log("Couldn't save values for " + var.plants[i], 1)
        else:
            log("No new logs for for " + var.plants[i], 1)


def pingEveryone():
    var.unresponsivePlants = []
    var.plantsUnresponsive = False
    for i in range(len(var.plants)):
        if (var.plantResponses[i] == False):
            var.unresponsivePlants.append(i)
            var.plantsUnresponsive = True
        var.plantResponses[i] = False

    for plant in var.plants:
        client.publish(plant + "/Ping/Send", "Ping")


def sendAlarms():
    # Save logs 1x/d
    saveLogs()
    if var.plantsUnresponsive:
        for plant in var.unresponsivePlants:
            client.publish(var.plants[plant] + "/Alarm", "true")
            sleep(3)
            client.publish(var.plants[plant] + "/Alarm", "false")


def log(text, level):
    if level <= var.debuglevel:
        print(var.debugStr[level] + text)
        client.publish("Logger/Log", var.debugStr[level] + text)


if __name__ == "__main__":
    sleep(10.0)  # wait for everything to connect (Wifi, etc)
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("10.0.0.50", 1883, 60)
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
