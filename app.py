#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Alexandre Bulté <alexandre[at]bulte[dot]net>
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from flask import Flask, request, render_template, jsonify

import datetime
import json
import serial
import collections
import time

import gevent

app = Flask(__name__)
app.debug = True

## DB STUFF ##
import sqlite3
from flask import g

DATABASE = '../monitor_serial_git/temps.db'
DATABASE_SALON = '../monitor_serial_git/salon.db'
DATABASE_TOBACCO = '../monitor_serial_git/temps_w_tobacco.db'

def connect_db(database):
    return sqlite3.connect(database)

def query_db_orig(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

def date_from_timestamp(ts):
    mydate = datetime.datetime.fromtimestamp(ts)
    return mydate.strftime('%d/%m/%y - %H:%M:%S')


def query_db(dbtouse, query, args=(), convert_date=True):
    db = connect_db(dbtouse)
    cur = db.execute(query, args)
    rv = []
    for row in cur.fetchall():
        new_row = []
        if convert_date:
            new_row.append(date_from_timestamp(row[0]))
        else:
            new_row.append(row[0])
        for item in row[1:]:
            new_row.append(item)
        rv.append(new_row)
    db.close()
    return rv

## END DB ##

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

def connect_serial():
    serialport = '/dev/ttyACM0'
    baudrate = '9600'
    ser = serial.Serial(serialport, baudrate)
    ser.stopbits = 2
    return ser

def make_result(values, hum_list):
    result = []
    # date
    result.append(date_from_timestamp(time.time()))
    # temp, rhum, thum
    result.extend(values[1::2])
    # thum average
    hum_list.append(float(values[5]))
    result.append(int(float(sum(hum_list)) / len(hum_list)))
    # send result through websocket
    return result, hum_list

def _read_serial(ws):
    input = ''
    hum_list = collections.deque(maxlen=10)
    ser = connect_serial()
    # todo: exit loop when websocket disconnects?
    # todo: timeout?
    while True:
        input += ser.read()
        # gevent.sleep(0)
        while input.find("\r\n") != -1:
            chopped_line = input[:input.find("\r\n")]
            input = input[input.find("\r\n")+2:]
            if chopped_line.find('temperature') != -1:
                values = chopped_line.split(' ')
                if len(values) > 5:
                    result, hum_list = make_result(values, hum_list)
                    ws.send(json.dumps({'latest': result}))
                else:
                    ws.send(json.dumps({'error':'wrong length of parsed line'}))
            else:
                ws.send(json.dumps({'error':'wrong line format'}))


def read_serial(ws):
    ws.send(json.dumps('coucou'))
    i = 0
    while i < 60:
        ws.send(json.dumps(i))
        time.sleep(1)
        i += 1
    ws.send(json.dumps('end'))

# get the latest measure
# directly through serial
@app.route('/api/live')
def api_live():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        read_serial(ws)
    return jsonify({'status': 'ok'})

@app.route('/api')
def api():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        readings = query_db(DATABASE, 'SELECT * FROM readings ORDER BY ts DESC')
        readings_salon = query_db(DATABASE_SALON, 'SELECT * FROM readings ORDER BY ts DESC')
        readings_tobacco = query_db(DATABASE_TOBACCO, 'SELECT * FROM readings ORDER BY ts DESC')
        ws.send(json.dumps({'en_cours': readings, 'salon': readings_salon, 'tobacco' : readings_tobacco}))
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    http_server = WSGIServer(('',80), app, handler_class=WebSocketHandler)
    http_server.serve_forever()
