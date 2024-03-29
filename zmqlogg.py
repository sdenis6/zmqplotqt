#!/usr/bin/env python 

"""
Modified on 2022 03 11
by Severine DENIS
This script is used to logg the zmq stream sent by a redpitaya
"""

import zmq, time, struct, sys, argparse, threading

DEVICE_IP = '138.131.232.137'
OUT_PORT = '9901 9903 9905 9905'
DELAY = 0.05
CHANNEL = '1 1 1 2'
NB_CHAN = '2'
SAVE = 0
FORMAT = '4096h'
HEADERS = ''
FOOTER = ''
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
    parser.add_argument('-nbch', action='store', dest='nb_chan', \
                        default=NB_CHAN,\
                        help='Nomber of interleaved channels. (default '+str(NB_CHAN)+')')
    parser.add_argument('-s', action='store', dest='save', \
                        default=SAVE,\
                        help='To export the stream to a .dat file : -s 1. The file is created in the current folder. (default '+str(SAVE)+')')
    parser.add_argument('-fo', action='store', dest='Format', \
                        default=FORMAT,\
                        help='Data format in zmq protocol. (default '+str(FORMAT)+')')
    parser.add_argument('-he', action='store', dest='Headers', \
                        default=HEADERS,\
                        help='Headers for graphs and data save option. (default '+str(HEADERS)+')')
    parser.add_argument('-foo', action='store', dest='Footer', \
                        default=FOOTER,\
                        help='Foter to place at the end of the filename. (default '+str(FOOTER)+')')
    args = parser.parse_args()
    return args

#==============================================================================

try:
    args = parse()
    
    args.port = args.port.split()
    args.channel = args.channel.split()
    args.channel = list(args.channel)
    args.ip = args.ip.split()
    args.nb_chan = int(args.nb_chan)
    
    sock = [0]*len(args.channel)
    p = [0]*len(args.channel)
    curve = [0]*len(args.channel)
    data = [0]*len(args.channel)
    datas = [0]*len(args.channel)
    tmp = [0]*len(args.channel)
    #ttf = np.empty(100)
    ttf = [0]*100
    ptr1 = 0
    t0 = time.time()
    tf = 0
    ee = 0
    
    dt = int(args.delay)*1000
    
    if args.Footer != '':
        args.Footer = '_' + args.Footer
    filename = time.strftime("%Y%m%d-%H%M%S", time.gmtime(t0)) + '-RP' + args.Footer + '.dat'
    if int(args.save) == 1:
        data_file = open(filename, 'w')
        if args.Headers == '':
            def_headers = ''
            for i in range(len(args.port)):
                if len(args.ip) != 1:
                    def_headers = def_headers + str(args.ip[i]) + ':' + str(args.port[i]) + '/' + str(args.channel[i])
                else :
                    def_headers = def_headers + str(args.ip[0]) + ':' + str(args.port[i]) + '/' + str(args.channel[i])
                def_headers = def_headers + '\t'
            data_file.write('epoch_time\tYYYY-MM-DD\thh:mm:ss.ss\t' + def_headers + '\n')
        else:
            data_file.write('epoch_time\tYYYY-MM-DD\thh:mm:ss.ss\t' + args.Headers.replace(' ','\t') + '\n')
    
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
    
    #win = pg.GraphicsWindow()
    #win.setWindowTitle('zmqplotqt.py IP:'+str(args.ip)+':'+str(args.port)+' ch'+str(args.channel)+' dt='+str(args.delay)+'s')
    
    for i in range(len(args.channel)):
    
        #if args.Headers == '':
        #    if len(args.ip) != 1:
        #        def_headers = str(args.ip[i]) + ':' + str(args.port[i]) + '/' + str(args.channel[i])
        #    else :
        #        def_headers = str(args.ip[0]) + ':' + str(args.port[i]) + '/' + str(args.channel[i])
        #    p[i] = win.addPlot(title=def_headers)
        #else:
        #    p[i] = win.addPlot(title=args.Headers.split()[i])
    
        #p[i] = win.addPlot(title=)
        #win.nextRow()
        #p[i].setDownsampling(mode='peak')
        #p[i].setClipToView(True)
        #p[i].showGrid(True,True)
        #curve[i] = p[i].plot()
        #data[i] = np.empty(100)
        data[i] = [0]*100
        datas[i] = 0
    
    def valrcv(e):
        global ee, value, datas, datasi
        recv_to_crop = sock[e].recv()
        #print('r', len(recv_to_crop))
        value = struct.unpack(args.Format.encode('utf-8'), recv_to_crop)
        #value = struct.unpack(args.Format.encode('utf-8'), recv_to_crop[2:])
        data[e][ptr1] = sum(value[int(args.channel[e])-1::args.nb_chan])/len(value[int(args.channel[e])-1::args.nb_chan])
        if int(args.save) == 1:
            datas[e] = sum(value[int(args.channel[e])-1::args.nb_chan])/len(value[int(args.channel[e])-1::args.nb_chan])
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
            #mjd = epoch / 86400.0 + 40587
            date = time.strftime('%Y-%m-%d\t%H:%M:%S.' + str(epoch).split('.')[1] , time.localtime(epoch))
            #string = "%f\t%f\t%s\n" % (epoch, mjd, datasi)
            string = "%f\t%s\t%s\n" % (epoch, date, datasi)
            data_file.write(string)
            #print("%f\t%f\t%s" % (epoch, mjd, datasi))
            print("%f\t%s\t%s" % (epoch, date, datasi))
    
        ttf[ptr1] = time.time()-t0
        ptr1 += 1
    
        if ptr1 >= len(data[0]):
            tmpttf = ttf
            #ttf = np.empty(len(ttf) * 2)
            ttf = [0]*(len(ttf) * 2)
            ttf[:len(tmpttf)] = tmpttf
            for i in range(len(args.channel)):
                tmp[i]=data[i]
                #data[i] = np.empty(len(data[i]) * 2)
                data[i] = [0]*(len(data[i]) * 2)
                data[i][:len(tmp[i])] = tmp[i]
    
        #for i in range(len(args.channel)):
        #    curve[i].setData(ttf[:ptr1], data[i][:ptr1], pen=pg.mkPen(6+3*i, width=1))
    
    
    # update all plots
    def update():
        update1()
        update.thread = threading.Timer(float(args.delay), update)
        update.thread.start()
    
    update()
    
    print("wait")
    input()

    #timer = pg.QtCore.QTimer()
    #timer.timeout.connect(update1)
    #timer.start(dt)
    
    
    ## Start Qt event loop unless running in interactive mode or using pyside.
    #if __name__ == '__main__':
    #    import sys
    #if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #        QtGui.QApplication.instance().exec_()

except:
    if int(args.save) == 1:
        data_file.close()
        print('filename : ' + filename)
    
    print('zmqplotqt.py IP:' + str(args.ip) + ':' + str(args.port) + ' ch' + str(args.channel) + ' dt=' + str(args.delay) + 's')
