from flask import Flask
from config import config
import serial
import time
import threading


app = Flask(__name__)
lock = threading.Lock()
is_running = False
stop_loop = False
defaultstateline1 = config.defaultStateLine1
defaultstateline2 = config.defaultStateLine2

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
        ser.write(f'\r{str1}\r'.encode())
        if str2:
            ser.write(str2.encode())
        if close == True:
                ser.close()

def default_state():
    global stop_loop, defaultstateline1, defaultstateline2
    stop_loop=True
    if config.blankDefaultState == True: #blank the display
        blank()
        print("Blanked the display.")
    elif config.dynamicDefaultState == True:
        direct_write(defaultstateline1, defaultstateline2)
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

def scroll(str1, str2, close, *args, **kwargs): #there's gotta be a better way to do this right? tk 
    if not len(str1) > config.columns and len(str2) > config.columns:
        scrollboth(str1, str2, close=close)
    elif len(str1) > config.columns:
        scroll1(str1, str2, close=close)
    elif len(str2) > config.columns:
        scroll2(str1, str2, close=close)


def scroll0(str1, str2, close, *args, **kwargs):
    global stop_loop
    stop_loop = False
    str1len = len(str1)
    str1list = list(str1)
    wrapped_str1 = str1 + str1[:config.columns]
    while not stop_loop:
        for i in range(len(str1) + config.columns - 1):
            str1_slice = wrapped_str1[i:i + config.columns - 1]
            direct_write(str1=str1_slice, str2=str2, close=False)
            print(str1_slice)
            time.sleep(config.scrollspeed)

def scroll1(str1, str2, close, *args, **kwargs):
    global stop_loop
    stop_loop = False
    str1len = len(str1)
    str1 = " " + str1 + " "
    while not stop_loop:
        for i in range(len(str1)):
            str1_slice = str1[i:i + config.columns - 1]
            direct_write(str1=str1_slice, str2=str2, close=False)
            print(str1_slice)
            time.sleep(config.scrollspeed)






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

@app.route('/default/<str1>:<str2>', methods=['GET'])
def entering(str1, str2):
    set_default_state(str1, str2)
    print(f"Set 2 lines as default on display. \"{str1 or '-nothing-'}\" on line 1 and \"{str2 or '-nothing-'}\" on line 2.")
    return f"Set 2 lines as default on display. \"{str1 or '-nothing-'}\" on line 1 and \"{str2 or '-nothing-'}\" on line 2.", 200

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
    scroll1("onetwothreefourfivesixseveneightnine", "test", close=True)
    return f"pls", 200

if __name__ == '__main__':
    app.run(port=config.port, debug=True)
    default_state(fadetime=1)


