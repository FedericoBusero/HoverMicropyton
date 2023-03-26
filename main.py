from machine import Timer, PWM
from microdot_asyncio import Microdot, Response, send_file
from microdot_asyncio_websocket import with_websocket
from microDNSSrv import MicroDNSSrv
import logging

# ----------------------------------------------------------------------------
domainsList = {
  "h.be" : "192.168.4.1"
 }

#servopin, motorpin and led_pin are defined in boot.py

#configuration of servo
SERVO_DUTYCYCLE_MIN=const(30)  # 0 (0 ms) .. 1023 (20 ms)
SERVO_DUTYCYCLE_MAX=const(123) # 0 (0 ms) .. 1023 (20 ms)
servo = PWM(servopin, freq=50, duty=(SERVO_DUTYCYCLE_MIN + SERVO_DUTYCYCLE_MAX) // 2)

servo_duty=(SERVO_DUTYCYCLE_MIN + SERVO_DUTYCYCLE_MAX) // 2
joystick_x=0  # -180 .. 180
servo_trim_slider=0 # -180 .. 180

#configuration of motor
MOTOR_FREQ=const(400) # frequency of (sound of) motor signal
TIMEOUT_MS_MOTORS=const(2500) # motor will shut down after x ms no data received²
PWM_RANGE=const(1023)

motor_speed=0
max_motor_speed=(300*PWM_RANGE)//360;
motors_halt=False
motor_pwm = PWM(motorpin)
motor_pwm.freq(MOTOR_FREQ)

#configuration of led pin
led_timer = Timer(0)
TIMEOUT_MS_LED=const(1) # led will go high for x ms after reception of a message

connection_timer = Timer(2)

# ----------------------------------------------------------------------------
# led_on, led_off, led_toggle are defined in boot.py

def led_start_blinking():
    global led_timer
    led_timer.init(mode=Timer.PERIODIC,period=500,callback=led_toggle)
    
def led_stop_blinking():
    global led_timer
    led_timer.init(mode=Timer.ONE_SHOT,period=0,callback=lambda t: led_off())

def led_ping():
    global led_timer
    led_on()
    led_timer.init(mode=Timer.ONE_SHOT,period=TIMEOUT_MS_LED,callback=lambda t: led_off())
    
# ----------------------------------------------------------------------------

def connection_timeout(t):
    global motors_halt
    
    logger.debug("connection timeout")
    motors_halt = True
    updateMotors()
    led_start_blinking()

def start_connection_timer():
    global connection_timer
    connection_timer.init(mode=Timer.ONE_SHOT,period=TIMEOUT_MS_MOTORS,callback=connection_timeout)


# ----------------------------------------------------------------------------
def _acceptWebSocketCallback(webSocket, httpClient) :
    logger.debug("WS ACCEPT")
    webSocket.RecvTextCallback = _recvTextCallback
    ## webSocket.RecvBinaryCallback = _recvBinaryCallback
    webSocket.ClosedCallback = _closedCallback
    led_stop_blinking()
    start_connection_timer()

def map_int(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def updateMotors():
    global servo_duty
    global motors_halt
    
    logger.debug("updateMotors")
    if motors_halt:
        logger.debug("motor stopped")
        motor_pwm.duty(0)
    else:
        servo_duty = map_int(joystick_x + servo_trim_slider, -360, 360, SERVO_DUTYCYCLE_MIN, SERVO_DUTYCYCLE_MAX)
        logger.debug("servo_duty: %d",servo_duty)
        logger.debug("motor_speed: %d",motor_speed)
        motor_pwm.duty(motor_speed)
        servo.duty(servo_duty)

def handleJoystick(x, y):
    global joystick_x
    global motor_speed
    
    logger.debug("handleJoystick %d,%d",x,y)
    joystick_x = x
    if (y <= 0):
        motor_speed = map_int(-y, 0, 180, 0, max_motor_speed)
    else:
        motor_speed = 0
    updateMotors()

def handleSliderMaxSpeed(maxspeed):
    global max_motor_speed
    logger.debug("handleSliderMaxSpeed %d",maxspeed)
    max_motor_speed=map_int(maxspeed,0,360,PWM_RANGE//2,PWM_RANGE)
    updateMotors()

def handleSliderTrimServo(servotrim):
    global servo_trim_slider
    
    logger.debug("handleSliderTrimServo %d",servotrim)
    servo_trim_slider = servotrim
    updateMotors()

def handleMessage(msg) :
    global motors_halt
    
    start_connection_timer()
    msgspl = msg.split(":")
    motors_halt = False
    if (msgspl[0]=="0"):
        logger.debug("ping")
        updateMotors()
    elif (msgspl[0]=="1"):
        params=msgspl[1].split(",")
        handleJoystick(int(params[0]),int(params[1]))
    elif (msgspl[0]=="2"):
        params=msgspl[1].split(",")
        handleSliderMaxSpeed(int(params[0]))
    elif (msgspl[0]=="3"):
        params=msgspl[1].split(",")
        handleSliderTrimServo(int(params[0]))   

def _closedCallback(webSocket) :
    logger.info("WS CLOSED")
    led_start_blinking()
    
# ----------------------------------------------------------------------------
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)
logger.info("Hover micropython start microdot server")

# Initialize MicroDot
app = Microdot()
Response.default_content_type = 'text/html'

# root route
@app.route('/')
async def index(request):
    return send_file('/www/index.html')

@app.route('/ws')
@with_websocket
async def read_socket(request, ws):
    while True:
        data = await ws.receive()
        logger.debug("WS RECV TEXT : %s",data)
        handleMessage(data)
        led_ping()

# Start DNS server
mds = MicroDNSSrv.Create(domainsList)
if mds.Start() :
    logger.info("MicroDNSSrv started.")
else :
    logger.error("Error to starts MicroDNSSrv...")

led_start_blinking()
try:
    app.run(port=80)
except KeyboardInterrupt:
    pass
