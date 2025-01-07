#TODO top line doesnt take 20char. make this configurable. update default state occasionally
#TODO later move all the send commands to their own file so that various send commands will be supported

from flask import Flask
from config import config
import serial
import time
import threading
import sys
import asyncio
import traceback


app = Flask(__name__)
defaultstateline1 = config.defaultStateLine1
defaultstateline2 = config.defaultStateLine2

class AsyncThread(threading.Thread):
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.task = None
        super().__init__(target=self.loop.run_forever)


        # def custom_exception_handler(loop, context):
        #     print('hi!')
        #     exception = context.get("exception", "Unknown error")
        #     message = context.get("message", "")

        #     if exception:
        #         traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
        #     if message:
        #         print(f"Message: {message}", file=sys.stderr)

        # self.loop.set_exception_handler(custom_exception_handler)

        self.loop.call_soon_threadsafe(lambda: asyncio.set_event_loop(self.loop))

    def run_task(self, coro):
        if self.task:
            self.task.cancel()
        self.task = asyncio.run_coroutine_threadsafe(coro, self.loop)

        def task_handler(task):
            if exc := task.exception():
                raise exc
                # traceback.print_exception(exc)

        self.task.add_done_callback(task_handler)

    def runin(self, coro):
        def wraps(*args, **kwargs):
            print('run_task', coro, args, kwargs)
            self.run_task(coro(*args, **kwargs))
        return wraps

renderthread = AsyncThread()
renderthread.start()

# ---- Write Pipelines ----

@renderthread.runin
async def regular_send(*args, fadetime=config.defaultFadetime, **kwargs):
    try:
        with asyncio.timeout(fadetime):
            await write_pipeline(*args, fadetime=fadetime, **kwargs) #kk
    finally:
        default_state()

async def write_pipeline(str1, str2, close=True, scroll=False, blink=False, *args, **kwargs): #tk change default of scroll when its implemented
    if scroll == False and blink == False: #if it doesnt use special features, we can just write it directly
        direct_write(str1=str1, str2=str2, close=close) 
        await asyncio.Event().wait()  # run forever (until cancelled)
    elif scroll == True and blink == True:
        direct_write(str1="Err", str2="2", close=close) #Error 2, scroll and blink are both enabled. can't do this atm sorry!
        await asyncio.sleep(2)
        raise(Exception, "Error 2, scroll and blink cannot both be enabled.")
    elif scroll == True:
        await scroll(str1=str1, str2=str2, args=args, kwargs=kwargs)
    elif blink == True:
        await blink(str1=str1, str2=str2, args=args, kwargs=kwargs)

def direct_write(str1, str2, close=True):
    with serial.Serial(config.tty, config.baudrate, timeout=config.timeout) as ser: 
        if str2:
            ser.write(f'\r{str1}\r{str2}'.encode())
        else: 
            ser.write(f'\r{str1}\r'.encode())
        if close == True:
                ser.close()

def default_state():
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

async def blink(str1, str2, close, blinkspeed=config.blinkspeed, *args, **kwargs):
    while True:
        direct_write(str1, str2, close=False)
        await asyncio.sleep(blinkspeed)
        blank(close=False)
        await asyncio.sleep(blinkspeed)


@renderthread.runin
async def scrolltest():
    await scroll(str1="i got the scrolling working guys :)", str2="two lines tooooooooooooo")

async def scroll(str1, str2):
    scroll1, scroll2 = scrollstr(str1, config.row1columns), scrollstr(str2, config.row2columns)
    for line1, line2 in zip(scroll1, scroll2):
        direct_write(str1, str2, close=False)
        await asyncio.sleep(config.scrollspeed)

from itertools import repeat
def scrollstr(s: str, rowlen: int):
    if len(s) < rowlen:
        yield from repeat(s)   #maybe make it wiggle if it doesnt need to scroll but not right now
    while True:
        for window in range(0, len(s) - rowlen):
            yield s[window:window+rowlen]
        for window in range(len(s) - rowlen, 0, -1):
            yield s[window:window+rowlen]

# ---- Flask Paths ----

@app.route('/entering/<str2>', methods=['GET'])
def entering(str2):
    str1 = "Now Entering:"
    regular_send(str1, str2, config.defaultFadetime)
    print(f"Sent 2 lines to display. \"{str1 or '-nothing-'}\" on line 1 and \"{str2 or '-nothing-'}\" on line 2.")
    return f"Sent 2 lines to display. \"{str1 or '-nothing-'}\" on line 1 and \"{str2 or '-nothing-'}\" on line 2.", 200

@app.route('/display/<str1>', methods=['GET'])
@app.route('/display/<str1>:<str2>', methods=['GET'])
def display(str1=None, str2=None):
    regular_send(str1=str1, str2=str2)
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
        regular_send("hiii", ":3")
        ser.close()
    if config.defaultFadetime < 1 or config.defaultFadetime > 1000:
        return f"Your fadetime is {config.defaultFadeTime}. Please note that this value is in seconds and should be 1 or greater.", 200
    if len(config.defaultStateLine1) > config.columns:
        return f"One of your defaultStateLines is greater than the number of columns on your display as defined in the config. Your default state will not display correctly.", 200
        regular_send("Check", "Config", 20)
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


