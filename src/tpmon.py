#!/usr/bin/python3

import requests
import hashlib
from pprint import pprint
import json
import time
import math
import RPi.GPIO as GPIO
import argparse
import sys
from tendo import singleton
import tpmon_pb2_grpc
import tpmon_pb2
import grpc
from concurrent import futures
from threading import Lock
from pprint import pprint
import os

class TPMonServer(tpmon_pb2_grpc.ThroughputRendererServicer):
    def __init__(self, m):
        self._motor_manager = m
        tpmon_pb2_grpc.ThroughputRendererServicer.__init__(self)

    def QueryPosition(self, request, context):
        print("QueryPositionRequest was called!\n")
        (pos, maxpos) = self._motor_manager.position()
        return tpmon_pb2.QueryPositionResponse(
                    raw_position=pos,
                    max_raw_position=maxpos)

    def SetPosition(self, request, context):
        print("SetPosition was called raw {}, pct {}".format(
                request.raw_position,
                request.pct_position))
        if request.raw_position > 0:
            self._motor_manager.seek(request.raw_position)
        else:
            self._motor_manager.seek_pct(request.pct_position)
        return tpmon_pb2.StatusResponse(rcode=0, diag_msg="Moved")


class Scoper(object):
    def __init__(self, cb):
        self._cb = cb
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pprint(self._cb)
        func = self._cb
        func()
 
class MotorManager(object):

    def __init__(self):
        self._d_pos = 0
        self._lock = Lock()
        # With 1/64 gear reduction and 32 steps per rotation,
        # the stepper motor has 2048 total steps per revolution
        self._d_max_pos = 1310
        self._interval = 0.003
        self._phases = [ 
                         [ 1, 0, 0, 0 ],
                         [ 0, 1, 0, 0 ],
                         [ 0, 0, 1, 0 ],
                         [ 0, 0, 0, 1 ],
                    ]
    def __enter__(self):
        GPIO.setmode(GPIO.BOARD)
        self._pins = [3, 5, 7, 11]
        for pin in self._pins:
            GPIO.setup(pin, GPIO.OUT)
        self._clear_gpio()
        return self

    def sweep(self):
        self.seek_pct(0)
        self.seek_pct(100)
        self.seek_pct(0)

    def _clear_gpio(self):
        GPIO.output(self._pins, [False, False, False, False])

    def _current_phase(self):
        return self._phases[self._d_pos % len(self._phases)]

    def fwd_phase(self, do_check=True):
        if do_check and (self._d_pos >= self._d_max_pos):
            self._d_pos = self._d_max_pos
            return

        self._d_pos += 1

    def back_phase(self, do_check=True):
        if do_check and (self._d_pos <= 0):
            self._d_pos = 0
            return

        self._d_pos -= 1

    def seek_max(self):
        self.seek(self._d_max_pos)

    def seek(self, pos):
        if pos > self._d_max_pos:
            pos = self._d_max_pos
        elif pos < 0:
            pos = 0
        print("SEEKING TO {0}".format(pos))
        self.move(pos - self._d_pos)
        print("DONE SEEKING")

    def unsafe_move(self, steps):
        self.move(delta=steps, safe=False)

    def seek_pct(self, pct):
        self.seek(int(pct * self._d_max_pos))

    def position(self):
        return (self._d_pos, self._d_max_pos)

    def move(self, delta=0, safe=True):
        with (self._lock):
            #First, output current phase
            GPIO.output(self._pins, self._current_phase())
            time.sleep(self._interval)

            for i in range(abs(delta)):
                if delta > 0:
                    self.fwd_phase(do_check=safe)
                else:
                    self.back_phase(do_check=safe)
                GPIO.output(self._pins, self._current_phase())
                time.sleep(self._interval)

            self._clear_gpio()

    def zero(self):
        self._d_pos = 0

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Calling cleanup")
        self.seek(0)
#        GPIO.cleanup()

def dumpresp(resp, cookies=False):
    return
    print("===================STATUS CODE: {0}".format(resp.status_code))
    print("URL: {0}".format(resp.url))
    print("====HEADERS====")
    pprint(resp.headers)
    print("====CONTENT====")
    pprint(resp.content)
    if cookies:
        print("===COOKIES====")
        pprint(resp.cookies)

def update_gauge(bw, m):
    max_bw_kbps = 1000000
    base = 10
    max_gauge_val = math.log(max_bw_kbps, base)
    current_gauge_val = 0
    if bw > 0:
        current_gauge_val = math.log(bw, base)
    pct = current_gauge_val / max_gauge_val
    print("BW {bw} means {pct}% of gauge".format(bw=bw, pct=pct*100.0))
    m.seek_pct(pct)

def main():
    me = singleton.SingleInstance()
    parser = argparse.ArgumentParser(description="Display internet bandwidth "+
                                    "on a log-scale dial")
    parser.add_argument("-c", "--calibrate", required=False, metavar="N", type=int, help="Calibrate motor by positive or negative steps")
    parser.add_argument("-p", "--port", required=False, metavar="P", type=int, help="Port number to listen on", default=5200)

    args = parser.parse_args()

    router_password = os.environ.get('VZ_ROUTER_PASSWORD', '')
    assert (router_password), 'Must set environment variable VZ_ROUTER_PASSWORD to your router\'s password'

    if args.calibrate is not None:
        with MotorManager() as m:
            tomove = args.calibrate
            print("Moving {0} steps".format(tomove))
            m.unsafe_move(tomove)
            m.zero()
            for bw in [0, 1, 10, 100, 1000, 10000, 100000, 1000000]:
                print("Here is {0}mbps".format(float(bw)/1000.))
                update_gauge(bw, m)
                time.sleep(5)
            m.seek(0)
            time.sleep(2)
            m.seek_max()
            time.sleep(5)

        sys.exit(0)

    with MotorManager() as m:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=3))
        tpmon_pb2_grpc.add_ThroughputRendererServicer_to_server(TPMonServer(m), server)
        server.add_insecure_port('[::]:%d'%(args.port))
        server.start()
        salt = getsalt()

        hashed_pw = getpw(router_password, salt)
        s = requests.Session()

        resp = s.post("http://192.168.1.1/api/login", json.dumps({'password': hashed_pw}))
        if resp.status_code != 200:
            raise Exception("Unable to login to router: {0}".format(resp.status_code))

        m.sweep()
            
        cookieJar = resp.cookies
        token = cookieJar.get("XSRF-TOKEN")
        s.headers.update({"X-XSRF-TOKEN": token})
       
        def logout():
            resp = s.get("http://192.168.1.1/api/logout", cookies=cookieJar)
            print("logged out with http response code {0}".format(resp.status_code))

        with Scoper(logout) as scoper:
            while True:
                resp = s.get("http://192.168.1.1/api/network/1", cookies=cookieJar)
                bw = resp.json()['bandwidth']['minutesRx'][0] * 8
                units = resp.json()['bandwidth']['units']
                print("Last reported bandwidth is {0} {1}".format(bw, units))
                update_gauge(bw, m)
                time.sleep(10)


def getsalt():
    r = requests.get("http://192.168.1.1/api/login")
    json = r.json()
    return json['passwordSalt']

def getpw(pw, salt):
    hasher = hashlib.sha512()
    hasher.update((pw + salt).encode('ascii', 'replace'))
    return hasher.hexdigest()

if  __name__ == "__main__":
    main()
