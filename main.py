#todo threading

from flask import Flask
from config import config
import serial
import time
import threading


app = Flask(__name__)
lock = threading.Lock()
is_running = False

def bootup():
    print("Erecting a dispenser here.")
    with serial.Serial(config.tty, config.baudrate, timeout=config.timeout) as ser:
        print("Was able to connect to display!")
        regular_send_thread("hiii", ":3")
        ser.close()
    if config.fadetime < 1 or config.fadetime > 1000:
        print("Your fadetime is " + config.fadetime +". Please note that this value is in seconds and should be 1 or greater.")
    if len(config.defaultStateLine1) > config.columns or len(config.defaultStateLine2) > config.columns:
        print("One of your defaultStateLines is greater than the number of columns on your display as defined in the config. Your default state will not display correctly.")
        regular_send("Check", "Config", 20)

def regular_send_thread(*args, **kwargs):
    thread = threading.Thread(target=regular_send, args=args, kwargs=kwargs)
    thread.start()


def regular_send(str1, str2, fadetime=config.defaultFadetime):
    global is_running
    while True:
        with lock:
            if not is_running:
                is_running = True
                break
    direct_write(str1, str2, False) 
    time.sleep(fadetime)
    default_state(fadetime)
    with serial.Serial(config.tty, config.baudrate, timeout=config.timeout) as ser:
        ser.close()
        
def direct_write(str1, str2, close):
    with serial.Serial(config.tty, config.baudrate, timeout=config.timeout) as ser: 
        ser.write(f'\r{str1} \r'.encode())
        if str2:
            ser.write(str2.encode())
        if close == True:
            ser.close()

def default_state(fadetime=0):
    if fadetime == 0:
        errorout("Fadetime is zero! Fadetime wasn't passed along somewhere, was set to zero in the URL, or there was some sort of other fuckup.")
    if config.blankDefaultState == True: #blank the display
        direct_write("\r\r\r\r")
        print("Blanked the display.")
    else:
        direct_write(config.defaultStateLine1, config.defaultStateLine2, True)


# ---- Flask Paths ----

@app.route('/entering/<str2>', methods=['GET'])
def entering(str2):
    str1 = "Now Entering:"
    print(fadetime + blink)
    regular_send_thread(str1, str2, config.defaultFadetime)
    print(f"Sent 2 lines to display. {str1 or '-nothing-'} on line 1 and {str2 or '-nothing-'} on line 2.")
    return f"Sent 2 lines to display. {str1 or '-nothing-'} on line 1 and {str2 or '-nothing-'} on line 2.", 200

@app.route('/display/<str1>', methods=['GET'])
@app.route('/display/<str1>:<str2>', methods=['GET'])
def display(str1=None, str2=None):
    regular_send_thread(str1, str2)
    print(f"Sent 2 lines to display. {str1 or 'nothing'} on line 1 and {str2 or '-nothing-'} on line 2.")
    return f"Sent 2 lines to display. {str1 or 'nothing'} on line 1 and {str2 or '-nothing-'} on line 2.", 200

if __name__ == '__main__':
    app.run(port=config.port, debug=True)



# ---- Other Funcs ----


def errorout(str1="Unknown Error Thrown!"):
    raise Exception(str1)
    direct_write("Exception Thrown", "Check Console")

# ---- Startup ----
bootup() #shit dont work son tk