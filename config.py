class config:
    #Flask settings
    port=8000
    debug = False
    #
    # ---- Display Params ----
    tty = '/dev/tty.usbmodemNT20091014001'
    baudrate = 19200
    timeout = 1
    columns = 20 #display columns, for scrolling behaviour. please note that this program only supports 2 rows
    row1columns = 19
    row2columns = 19 

    # ---- General Configuration ----
    blinkspeed = 0.5 
    scrollspeed = 0.35
    defaultFadetime = 10 #by default, how long is a message displayed on the screen before returning to default state?
    scrollTime = 30 #when a message has to scroll, how long should it scroll for?
    blankDefaultState = False #if this is set to true, the display's default state will be blank and the following two lines are not used for anything.
    dynamicDefaultState = False #a default state that can be periodically updated. cannot have blankdefaultstate set to true.
    defaultStateLine1 = "this is the"
    defaultStateLine2 = "default state"
    avaliableFeatures = "<fadetime>/<blink>"