#!/usr/bin/env python 

"""
Modified on Wednseday July 11 08:00:00 2019
by Severine DENIS
This script is used to live plot the zmq flux sent by a redpitaya
"""

import zmq, time, numpy, struct, sys, argparse
#import matplotlib.pyplot as plt

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

DEVICE_IP = '10.1.28.46'
OUT_PORT = '9902 9904 9902 9904'
DELAY = 0.05
CHANNEL = '1 1 2 2'
SAVE = 0
FORMAT = '4096h'
#==============================================================================
def parse():
    """
    parsing procedure to use this script
    """
    parser = argparse.ArgumentParser( \
        description='Monitor data sent using a ZeroMQ message transport '\
        'protocol on the local network.',
        epilog='Example: zmqplotqt -ip "192.168.0.xxx 192.168.0.xxx 192.168.0.zzz" -p "9902 9902 9903" -t 0.05 -ch "1 2 1" -s 1 /// zmqplotqt -ip "192.168.0.xxx -ch y -p y -fo f')
    parser.add_argument('-ip', action='store', dest='ip', \
                        default=DEVICE_IP,\
                        help='Ip adress on the local network of each zmq sender. A single IP can be mentionned for multiple channels/ports. (default '+DEVICE_IP+')')
    parser.add_argument('-p', action='store', dest='port', \
                        default=OUT_PORT,\
                        help='Port of the zmq sender. If several channels are mentionned -p requieres the port to listen for each channel. (default '+str(OUT_PORT)+')')
    parser.add_argument('-t', action='store', dest='delay', \
                        default=DELAY,\
                        help='Delay in seconds between two points. (default '+str(DELAY)+'s)')
    parser.add_argument('-ch', action='store', dest='channel', \
                        default=CHANNEL,\
                        help='Channels to display. (default '+str(CHANNEL)+')')
    parser.add_argument('-s', action='store', dest='save', \
                        default=SAVE,\
                        help='To export the stream to a .dat file : -s 1. The file is created in the current folder. (default '+str(SAVE)+')')
    parser.add_argument('-fo', action='store', dest='Format', \
                        default=FORMAT,\
                        help='Data format in zmq protocol. (default '+str(FORMAT)+')')
    args = parser.parse_args()
    return args

#==============================================================================

args = parse()

args.port = args.port.split()
args.channel = args.channel.split()
args.channel = map(int,args.channel)
args.ip = args.ip.split()

sock = [0]*len(args.channel)
p = [0]*len(args.channel)
curve = [0]*len(args.channel)
data = [0]*len(args.channel)
datas = [0]*len(args.channel)
tmp = [0]*len(args.channel)
ttf = np.empty(100)
ptr1 = 0
t0=time.time()
tf=0
ee=0

dt=float(args.delay)*1000

filename = time.strftime("%Y%m%d-%H%M%S", time.gmtime(t0)) + '-RP.dat'
if int(args.save) == 1:
    data_file = open(filename, 'wr', 0)

context = zmq.Context()
for i in range(len(args.port)):
    sock[i] = context.socket(zmq.SUB)
    sock[i].setsockopt(zmq.SUBSCRIBE, "".encode('utf-8'))
    sock[i].setsockopt(zmq.CONFLATE,1)
    #sock[i].setsockopt(zmq.RCVTIMEO,0)
    #sock[i].setsockopt(zmq.LINGER,0)
    if len(args.ip) != 1:
        sock[i].connect("tcp://"+args.ip[i]+":"+str(args.port[i]))
    else :
        sock[i].connect("tcp://"+args.ip[0]+":"+str(args.port[i]))

win = pg.GraphicsWindow()
win.setWindowTitle('zmqplotqt.py IP:'+str(args.ip)+':'+str(args.port)+' ch'+str(args.channel)+' dt='+str(args.delay)+'s')

for i in range(len(args.channel)):
    p[i] = win.addPlot()
    win.nextRow()
    p[i].setDownsampling(mode='peak')
    p[i].setClipToView(True)
    p[i].showGrid(True,True)
    curve[i] = p[i].plot()
    data[i] = np.empty(100)
    datas[i] = 0

def valrcv(e):
    global ee, value, datas, datasi
    recv_to_crop = sock[e].recv()
    #print('r', len(recv_to_crop))
    value = struct.unpack(args.Format.encode('utf-8'), recv_to_crop)
    #value = struct.unpack(args.Format.encode('utf-8'), recv_to_crop[2:])
    data[e][ptr1] = sum(value[args.channel[e]-1::2])/len(value[args.channel[e]-1::2])
    if int(args.save) == 1:
        datas[e] = sum(value[args.channel[e]-1::2])/len(value[args.channel[e]-1::2])
        datasi = str(datas)
        datasi = datasi.replace('+','')
        datasi = datasi.replace(',','\t')
        datasi = datasi.replace('[','')
        datasi = datasi.replace(']','')
        datasi = datasi.replace(' ','')
#ttt=[]

def update1():
    global epoch, mjd, string, data, ttf, ptr1, ttt

#    tt=time.time()

    for i in range(len(args.port)):
        valrcv(i)

#    ttt=ttt+[time.time()-tt]
#    print(sum(ttt))/len(ttt)

    if int(args.save) == 1:
        epoch = time.time()
        mjd = epoch / 86400.0 + 40587
        string = "%f\t%f\t%s\n" % (epoch, mjd, datasi)
        data_file.write(string)
        print("%f\t%f\t%s" % (epoch, mjd, datasi))

    ttf[ptr1] = time.time()-t0
    ptr1 += 1

    if ptr1 >= data[0].shape[0]:
        tmpttf = ttf
        ttf = np.empty(ttf.shape[0] * 2)
        ttf[:tmpttf.shape[0]] = tmpttf
        for i in range(len(args.channel)):
            tmp[i]=data[i]
            data[i] = np.empty(data[i].shape[0] * 2)
            data[i][:tmp[i].shape[0]] = tmp[i]

    for i in range(len(args.channel)):
        curve[i].setData(ttf[:ptr1], data[i][:ptr1], pen=pg.mkPen(6+3*i, width=1))

timer = pg.QtCore.QTimer()
timer.timeout.connect(update1)
timer.start(dt)


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

if int(args.save) == 1:
    data_file.close()
    print('filename : ' + filename)
print('zmqplotqt.py IP:' + str(args.ip) + ':' + str(args.port) + ' ch' + str(args.channel) + ' dt=' + str(args.delay) + 's')
