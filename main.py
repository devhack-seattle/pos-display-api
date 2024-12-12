#TODO top line doesnt take 20char. make this configurable. update default state occasionally
#TODO later move all the send commands to their own file so that various send commands will be supported

from flask import Flask
from config import config
import serial
import time
import threading
import sys


app = Flask(__name__)
lock = threading.Lock()
is_running = False
stop_loop = False
defaultstateline1 = config.defaultStateLine1
defaultstateline2 = config.defaultStateLine2
scrolledstr1 = ""
scrolledstr2 = ""
poke1syn = False
poke1ack = False
poke2syn = False
poke2ack = False

# ---- Write Pipelines ----

def regular_send_thread(*args, **kwargs):
    thread = threading.Thread(target=regular_send, args=args, kwargs=kwargs)
    thread.start()

def regular_send(*args, fadetime=config.defaultFadetime, **kwargs):
    global is_running
    while True:
        with lock:
            if not is_running:
                is_running = True
                break
    write_pipeline_thread(*args, fadetime=fadetime, **kwargs) #tk 
    time.sleep(fadetime)
    default_state()

def write_pipeline_thread(*args, **kwargs):
    thread = threading.Thread(target=write_pipeline, args=args, kwargs=kwargs)
    thread.start()

def write_pipeline(str1, str2, close=True, scroll=False, blink=False, *args, **kwargs): #tk change default of scroll when its implemented
    if scroll == False and blink == False: #if it doesnt use special features, we can just write it directly
        direct_write(str1=str1, str2=str2, close=close) 
    elif scroll == True and blink == True:
        direct_write(str1="Err", str2="2", close=close) #Error 2, scroll and blink are both enabled. can't do this atm sorry!
        raise(Exception, "Error 2, scroll and blink cannot both be enabled.")
    elif scroll == True:
        if not len(str1) <= config.columns and not len(str2) <= config.columns: #maybe make it wiggle if it doesnt need to scroll but not right now
            direct_write(str1, str2, close=close)
        else:
            scroll(str1=str1, str2=str2, args=args, kwargs=kwargs)
    elif blink == True:
        blink(str1=str1, str2=str2, args=args, kwargs=kwargs)

def direct_write(str1, str2, close=True):
    with serial.Serial(config.tty, config.baudrate, timeout=config.timeout) as ser: 
        if str2:
            ser.write(f'\r{str1}\r{str2}'.encode())
        else: 
            ser.write(f'\r{str1}\r'.encode())
        if close == True:
                ser.close()

def default_state():
    global stop_loop, defaultstateline1, defaultstateline2
    stop_loop=True
    if config.blankDefaultState == True: #blank the display
        blank()
        print("Blanked the display.")
    else:
        direct_write(config.defaultStateLine1, config.defaultStateLine2, True)

def set_default_state(str1, str2):
    global defaultstateline1, defaultstateline2
    defaultstateline1 = str1
    defaultstateline2 = str2


# ---- Screen Functions ----

def blank(close=True):
    with serial.Serial(config.tty, config.baudrate, timeout=config.timeout) as ser: 
        ser.write(f'\r \r \r \r'.encode())  
        if close == True:     
            ser.close()

def blink(str1, str2, close, blinkspeed=config.blinkspeed, *args, **kwargs):
    global stop_loop
    stop_loop = False
    while not stop_loop:
        with serial.Serial(config.tty, config.baudrate, timeout=config.timeout) as ser:
            direct_write(str1, str2, close=False)
            time.sleep(blinkspeed)
            blank(close=False)
            time.sleep(blinkspeed)


def scrolltest():
    global stop_loop
    stop_loop = False
    scrollthread(str1="i got the scrolling working guys :)", str2="two lines tooooooooooooo")
    time.sleep(60)
    # stop_loop = True
    # default_state()

def scrollthread(*args, **kwargs):
    thread = threading.Thread(target=scroll, args=args, kwargs=kwargs)
    thread.start()

def scroll(str1, str2):
    global scrolledstr1, stop_loop, poke1syn, poke1ack, scrolledstr2, poke2syn, poke2ack
    scrollstr1thread(str1)
    scrollstr2thread(str2)
    stoploopthread(60)
    while not stop_loop:
        while not poke1syn:
            time.sleep(0.01)
            # print('poke1syn no', file=sys.stdout)
        str1 = scrolledstr1
        poke1ack = True
        while not poke2syn:
            # print('poke2syn no', file=sys.stdout)
            time.sleep(0.01)
        str2 = scrolledstr2
        poke2ack = True
        direct_write(str1, str2, close=False)
        time.sleep(config.scrollspeed)


def scrollstr1thread(*args, **kwargs):
    thread = threading.Thread(target=scrollstr1, args=args, kwargs=kwargs)
    thread.start()

def scrollstr1(str1):
    global scrolledstr1, poke1syn, poke1ack, stop_loop
    flipflop = False
    poke1syn = False
    poke1ack = False
    while not stop_loop:
        if len(str1) <= config.row1columns:
            scrolledstr1 = str1
            time.sleep(5)
        elif len(str1) > config.row1columns & flipflop == False:
            for i in range(len(str1)):
                c = i + config.row1columns 
                scrolledstr1 = str1[i:c]
                poke1syn = True
                while not poke1ack:
                    time.sleep(0.01)
                poke1syn = False
                poke1ack = False
                if c == (len(str1)):
                    poke1syn = True
                    flipflop = True
                    time.sleep(1.5)
                    poke1syn = False
                    poke1syn = False
                    break
        elif len(str1) > config.row1columns & flipflop == True:
            for i in range(len(str1), 0, -1):
                c = i - config.row1columns - 1
                time.sleep(config.scrollspeed)
                scrolledstr1 = str1[c:i-1]
                poke1syn = True
                while not poke1ack:
                    time.sleep(0.01)
                poke1syn = False
                poke1ack = False
                if i == 20:
                    poke1syn = True
                    flipflop = False
                    time.sleep(1.5)
                    poke1syn = False
                    poke1ack = False
                    break

def scrollstr2thread(*args, **kwargs):
    thread = threading.Thread(target=scrollstr2, args=args, kwargs=kwargs)
    thread.start()

def scrollstr2(str2):
    global scrolledstr2, poke2syn, poke2ack, stop_loop
    flipflop2 = False
    poke2syn = False
    poke2ack = False
    while not stop_loop:
        if len(str2) <= config.row2columns:
            scrolledstr2 = str2
            poke2syn = True
            time.sleep(5)
        elif len(str2) > config.row2columns & flipflop2 == False:
            for i in range(len(str2)):
                c = i + config.row2columns
                scrolledstr2 = str2[i:c]
                poke2syn = True
                while not poke2ack:
                    time.sleep(0.01)
                poke2syn = False
                poke2ack = False
                if c == (len(str2)):
                    poke2syn = True
                    flipflop2 = True
                    time.sleep(1.5)
                    poke2syn = False
                    poke2ack = False
                    break
        elif len(str2) > config.row2columns & flipflop2 == True:
            for i in range(len(str2), 0, -1):
                c = i - config.row1columns - 1
                time.sleep(config.scrollspeed)
                scrolledstr2 = str2[c:i-1]
                poke2syn = True
                while not poke2ack:
                    time.sleep(0.01)
                poke2syn = False
                poke2ack = False
                if i == 20:
                    poke2syn = True
                    flipflop2 = False
                    time.sleep(1.5)
                    poke2syn = False
                    poke2ack = False
                    break

# ---- The Loop Stopperrrrr -----

def stoploopthread(*args, **kwargs):
    thread = threading.Thread(target=stoploop, args=args, kwargs=kwargs)
    thread.start()

def stoploop(len):
    global stop_loop
    time.sleep(len)
    stop_loop = True


# ---- Flask Paths ----

@app.route('/entering/<str2>', methods=['GET'])
def entering(str2):
    str1 = "Now Entering:"
    regular_send_thread(str1, str2, config.defaultFadetime)
    print(f"Sent 2 lines to display. \"{str1 or '-nothing-'}\" on line 1 and \"{str2 or '-nothing-'}\" on line 2.")
    return f"Sent 2 lines to display. \"{str1 or '-nothing-'}\" on line 1 and \"{str2 or '-nothing-'}\" on line 2.", 200

@app.route('/display/<str1>', methods=['GET'])
@app.route('/display/<str1>:<str2>', methods=['GET'])
def display(str1=None, str2=None):
    regular_send_thread(str1=str1, str2=str2)
    print(f"Sent 2 lines to display. \"{str1 or '-nothing-'}\" on line 1 and \"{str2 or '-nothing-'}\" on line 2.")
    return f"Sent 2 lines to display. \"{str1 or '-nothing-'}\" on line 1 and \"{str2 or '-nothing-'}\" on line 2.", 200

# @app.route('/default/<str1>:<str2>', methods=['GET'])
# def entering(str1, str2):
#     set_default_state(str1, str2)
#     print(f"Set 2 lines as default on display. \"{str1 or '-nothing-'}\" on line 1 and \"{str2 or '-nothing-'}\" on line 2.")
#     return f"Set 2 lines as default on display. \"{str1 or '-nothing-'}\" on line 1 and \"{str2 or '-nothing-'}\" on line 2.", 200

@app.route('/test', methods=['GET'])
def test():
    with serial.Serial(config.tty, config.baudrate, timeout=config.timeout) as ser:
        print("Was able to connect to display!")
        regular_send_thread("hiii", ":3")
        ser.close()
    if config.defaultFadetime < 1 or config.defaultFadetime > 1000:
        return f"Your fadetime is {config.defaultFadeTime}. Please note that this value is in seconds and should be 1 or greater.", 200
    if len(config.defaultStateLine1) > config.columns:
        return f"One of your defaultStateLines is greater than the number of columns on your display as defined in the config. Your default state will not display correctly.", 200
        regular_send_thread("Check", "Config", 20)
    return f"If you saw some text on the display, you're all set!", 200

@app.route('/testscroll', methods=['GET'])
def testscroll():
    # scroll1("hello this is an example of scrolling text", "test", close=True)
    scrolltest()
    return f"pls", 200

@app.route('/testwrite', methods=['GET'])
def testwrite():
    blank()
    direct_write("distincttext8482939", "fuckitallsonnnnnnnnn", close=True)
    return f"pls", 200


if __name__ == '__main__':
    app.run(port=config.port, debug=True)
    default_state(fadetime=1)


