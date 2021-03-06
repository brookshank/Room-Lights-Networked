#!/home/pi/.virtualenvs/Lighting2/bin/python
import json
import time
import socket
import threading
from Testing.Config import Config
MITCH_LIGHT_ID = 7
ROOM_GROUP_ID = 2

import phue
import rgbxy

class Lighting:

    def __init__(self):
        # Using GamutC for the new bulbs 
        self.converter = rgbxy.Converter(rgbxy.GamutC)
        self.bridge = phue.Bridge('10.5.44.119')
        self.r = 255
        self.g = 255
        self.b = 255
        self.update = False




    def main(self):

        server_thread = threading.Thread(target=self.socket_server)
        server_thread.daemon = True
        server_thread.start()

        oldr, oldg, oldb = self.r, self.g, self.b
        while True:
            try:
                master_lamp = self.bridge.get_light(MITCH_LIGHT_ID)['state']
                if master_lamp['on'] is False:
                    print("Off")
                    self.r,self.g,self.b = 0,0,0
                else:
                    x,y = master_lamp['xy']
                    brightness = master_lamp['bri']
                    self.r,self.g,self.b = self.converter.xy_to_rgb(x,y,brightness)

            except phue.PhueRequestTimeout:
                print("Timeout, trying again...")

            print(self.r, self.g, self.b)
            if (oldr is not self.r or oldg is not self.g or oldb is not self.b):
                print("Lighting changed, at if statement")
                self.update = True

            oldr, oldg, oldb = self.r, self.g, self.b
            time.sleep(0.5)


    def socket_server(self):
        # Server setup, to communicate with LED controllers
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind((Config.SERVER_HOST, Config.PORT))
        except socket.error as e:
            print(str(e))

        self.server_socket.listen(5)

        while True:
            conn, addr = self.server_socket.accept()
            print('got connection')
            client_thread = threading.Thread(target=self.handler, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()

    def handler(self, conn, addr):
        conn.sendall("Connected to Light Server".encode())
        while True:
            if self.update:
                conn.sendall(json.dumps([self.r, self.g, self.b]).encode())
                self.update = False
                print("data sent, handler")


if __name__ == '__main__':
    Lighting().main()
