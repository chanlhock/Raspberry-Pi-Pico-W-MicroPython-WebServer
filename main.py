# Simple HTTP Server Example
# Control an LED and read sensors using a web browser

from machine import Pin, I2C, PWM
from ssd1306 import SSD1306_I2C
from dht import DHT11, InvalidChecksum  # Temperature & Humidity sensor library
import time
import network, ntptime, utime
from ntptime import settime
import urequests # handles making and servicing network requests
import os, socket
from machine import Pin
from machine import WDT
from time import sleep_ms, sleep
from utime import sleep, sleep_ms
import os as uos
# from wavePlayer import wavePlayer
# player = wavePlayer()
import framebuf
import sdcard

# Board Pin assignment for this program
# P28 - DHT temperature and humidity sensor
# P27 - sound sensor module (ADC)
# P16 - servo motor control (PWM)
# P22 - buzzer (PWM)
# P20 & P21 - oled display (I2C0)
# P03 & P02 - ultrasonic distance sensor (P03 - Trigger, P02 - Echo)

logfile = open('/public_html/log.txt', 'a')
# duplicate stdout and stderr to the log file for debugging
os.dupterm(logfile)

led = Pin("LED", Pin.OUT)
ledState = 'LED State Unknown'

# button = Pin(16, Pin.IN, Pin.PULL_UP)
# DHT11 temperature and humidity sensor
pin = Pin(28, Pin.OUT, Pin.PULL_DOWN)

# sound sensor module
sound_value = analog_value = machine.ADC(27)

# ultrasonic distance sensor (P03 - Trigger, P02 - Echo)
trigger = Pin(3, Pin.OUT)
echo = Pin(2, Pin.IN)

def ultra():
   trigger.low()
   utime.sleep_us(2)
   trigger.high()
   utime.sleep_us(5)
   trigger.low()
   while echo.value() == 0:
       signaloff = utime.ticks_us()
   while echo.value() == 1:
       signalon = utime.ticks_us()
       
   timepassed = signalon - signaloff
   distance = (timepassed * 0.0343) / 2
   distance = "{:.1f}".format(distance)  
   print(distance + " cm")   
   return str(distance)

# servo motor pin set up
servoPin = PWM(Pin(16))
servoPin.freq(50)

def servo(degrees):
    # limit degrees beteen 0 and 180
    if degrees > 180: degrees=180
    if degrees < 0: degrees=0
    # set max and min duty
    maxDuty=9000
    minDuty=1000
    # new duty is between min and max duty in proportion to its value
    newDuty=minDuty+(maxDuty-minDuty)*(degrees/180)
    # servo PWM value is set
    servoPin.duty_u16(int(newDuty))
 
servo(0)
sleep(0.001)
  
# Set up connection to WiFi
ssid = 'your own wifi ssid'
password = 'your own wifi password'

# Set up I2C connection to oled display module
i2c=I2C(0,sda=Pin(20), scl=Pin(21), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

sensor = DHT11(pin)

# Buzzer pin assignment P22
buzzer = PWM(Pin(22))

rtc = machine.RTC()
web_query_delay = 600000
update_time = utime.ticks_ms() - web_query_delay
timezone_hour = 8 # timezone offset (hours)
      
#web server basic settings
public_folder='/public_html'
index_page='/index.html'
not_found_page='/notfound.html'

def path(request):
    try:
        decoded_req = request.decode()
        get_req = decoded_req.partition('\n')[0]
        print(get_req)
        path = get_req.split(" ")[1]
        path=path.rsplit('/', 1) #path[0]->folder, path[1]->filename
        path[1]='/'+path[1]
    except:
        print("folder path error!")
        get_req = "GET /test.html HTTP/1.1"
        path = get_req.split(" ")[1]
        path=path.rsplit('/', 1) #path[0]->folder, path[1]->filename
        path[1]='/'+path[1]
    return path
    
LOGO = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00|?\x00\x01\x86@\x80\x01\x01\x80\x80\x01\x11\x88\x80\x01\x05\xa0\x80\x00\x83\xc1\x00\x00C\xe3\x00\x00~\xfc\x00\x00L'\x00\x00\x9c\x11\x00\x00\xbf\xfd\x00\x00\xe1\x87\x00\x01\xc1\x83\x80\x02A\x82@\x02A\x82@\x02\xc1\xc2@\x02\xf6>\xc0\x01\xfc=\x80\x01\x18\x18\x80\x01\x88\x10\x80\x00\x8c!\x00\x00\x87\xf1\x00\x00\x7f\xf6\x00\x008\x1c\x00\x00\x0c \x00\x00\x03\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
fb = framebuf.FrameBuffer(LOGO,32,32, framebuf.MONO_HLSB)
oled.fill(0)
oled.text("Booting", 8, 56)
for i in range(-64,128,5):
     oled.blit(fb,i,16)
     if i < -32:  oled.text(".", 64, 56)
     if i >= -32 and i < 0:  oled.text(".", 72, 56)
     if i >= 0 and i <32: oled.text(".", 80, 56)
     if i >= 32 and i <64: oled.text(".", 88, 56)
     if i >= 64: oled.text(".", 96, 56)
     oled.show()
fb = framebuf.FrameBuffer(LOGO,32,32, framebuf.MONO_HLSB)
oled.fill(0)

# Blit the image from the framebuffer to the oled display
oled.blit(fb, 96, 0)
    
# Display main OLED screen title
oled.text("  Pi Pico W", 0, 0)
oled.text("  Webserver", 0, 8)
oled.text("   Project", 0, 16)
oled.show()

##CS = machine.Pin(17, machine.Pin.OUT)
##spi = machine.SPI(0,sck=machine.Pin(18),mosi=machine.Pin(19),miso=machine.Pin(16))

# baudrate=1000000,polarity=0,phase=0,bits=8,firstbit=machine.SPI.MSB,
##sd = sdcard.SDCard(spi,CS)

##vfs = uos.VfsFat(sd)
##uos.mount(vfs, "/sd")
# Get the list of all files and directories
##dir_list = os.listdir("/sd")
 
##print("Files and directories in /sd :")
 
# prints all files
##print(dir_list)

##def test2_file_found():
##    try:
##        os.stat('/public_html/test2.txt')
##        return True
##    except OSError:
##        return False
    
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm = 0xa11140) # disable active power saving mode
wlan.connect(ssid, password)

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)
    
# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('Connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )
    
# Function to load in html page    
# def get_html(html_name):
#    with open(html_name, 'r') as file:
#        html = file.read()        
#    return html

# Open socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #avoids errors for address in use on reconnection
s.bind(addr)
# s.setblocking(False) # set to non-blocking mode
s.listen(1) # allow 1 client
print('listening on', addr)

toggle = 0
# Create and send response
# update web clock time
if utime.ticks_ms() - update_time >= web_query_delay:
            
     try:
         ntptime.settime()
         update_time = utime.ticks_ms()
         date_time = list(rtc.datetime())
         print(date_time)
         date_time[4] = date_time[4] + 8
         if date_time[4] >= 24:
             date_time[4] - 24
         date_time = tuple(date_time)
         print(date_time)
         rtc.datetime(date_time)
         #print(time.localtime())
         #timestamp_start = time.localtime()
         timestamp_start = date_time
         print(timestamp_start)
         timestring_start = "%04d-%02d-%02d %02d:%02d:%02d"%(timestamp_start[0:3] + timestamp_start[4:7])
         print("Start time " + timestring_start)
     except:
         print("NTP server query failed.")
         timestamp_start = rtc.datetime()
         timestring_start = "%04d-%02d-%02d %02d:%02d:%02d"%(timestamp_start[0:3] + timestamp_start[3:6])
         
# Listen for connections, serve client
while True:     
    try:
        # s.settimeout(5.0)
        cl, addr = s.accept()
        print('client connected from', addr)

        
        cl_file = cl.makefile('rwb', 0)

        # recv can throw socket.timeout
        cl.settimeout(5.0)
        request = cl.recv(1024)
        cl.settimeout(None)

        # print(request)
        url=path(request)
        if url[0]=="" and (url[1]=="/" or url[1]=="/?led=on" or url[1]=="/?led=off" or url[1]=="/?sensor=read" or url[1]=="/?file=copy" ): url[1] = index_page
        # print(url)
        print(url[1])
        if url[1]=="/test.html":
            no_temp_sensor = 1
            print("test.html")
        else:
            no_temp_sensor = 0
            servo(0)
            sleep(0.001)

        if url[1][1:] not in os.listdir(public_folder+url[0]):
            url[0]=''
            url[1]=not_found_page
            header='HTTP/1.0 404 Object Not Found\r\n\r\n'
        else:
            header='HTTP/1.0 200 OK\r\n\r\n'
                        
        request = str(request)
    
        # response = get_html('index.html')
        
        led_on = request.find('led=on')
        led_off = request.find('led=off')
        file_read = request.find('file=copy')
              
        if led_on == 8:
            print("led on")
            led.value(1)
#             player.play('/sound/wav-8k_r2d2-shocked.wav')
#             player.stop()
            buzzer.freq(500)
            buzzer.duty_u16(1000)
            sleep(0.5)
            buzzer.duty_u16(0)
        if led_off == 8:
            print("led off")
            led.value(0)
        
        ledState = "LED is OFF" if led.value() == 0 else "LED is ON" # a compact if-else statement
        
        # Load log.txt file to log_copy.txt
        if file_read == 8:
              try:
                  logfile.close()
                  with open('/public_html/log.txt', 'r') as file:
                      read_file = file.read()
                  print("open log.txt successful")
                  if test2_file_found():
                      os.remove("/public_html/test2.txt")
              except:
                print("remove test2.txt file error")
                file_read = 0
                  
              try:    
                  write_logfile = open('/public_html/test2.txt', 'w')
                  write_logfile.write(str(read_file) + "\n")
                  write_logfile.flush()
                  write_logfile.close()
                  print("open test2.txt successful")
                  logfile = open('/public_html/log.txt', 'a')
                  # duplicate stdout and stderr to the log file for debugging
                  os.dupterm(logfile)                 
                  file_read = 0
              except:
                print("open log file or remove test2 file error")
                file_read = 0
        else:
              file_read = 0
              
        timestring = rtc.datetime()
        timestamp = rtc.datetime()   
        # Create and send response
        # update web clock time
        update_time = utime.ticks_ms() - web_query_delay
        if utime.ticks_ms() - update_time >= web_query_delay:
            
            try:
                ntptime.settime()
                update_time = utime.ticks_ms()
                local_time_sec = utime.time()+timezone_hour * 3600
                local_time = utime.localtime(local_time_sec)
                time_str = "{3:02d}:{4:02d}:{5:02d}".format(*local_time)
                timestamp = list(rtc.datetime())
                # timestamp = time.localtime()
                timestamp[4] = timestamp[4] + 8
                if timestamp[4] >= 24:
                     timestamp[4] - 24
                timestamp = tuple(timestamp)

                timestring = "%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7])
                print("Current time " + timestring)
            except:
                print("NTP server query failed.")
                timestring = rtc.datetime()
                
        if no_temp_sensor == 0:
            try:
                time.sleep(1.2)
                sound = sound_value.read_u16()
                print("Sound_ADC: ",sound)
                temp  = (sensor.temperature)
                humidity = (sensor.humidity)
                print("Temperature: {}C".format(temp))
                print("Humidity: {}%".format(humidity))
                oled.fill_rect(0, 32, 128, 64, 0)
                oled.text("Temp: {}C".format(temp), 0, 32)
                oled.text("Humi: {}%".format(humidity), 0, 40)
                oled.text(ledState, 0, 56)
                oled.show()
                # start increasing loop
                #for degree in range(0,180,10):
                if toggle == 0:
                    degree = 180
                    toggle = 1
                else:
                    degree = 0
                    toggle = 0
                servo(degree)
                sleep(0.001)
                print("increasing -- "+str(degree))
                # start decreasing loop
                #for degree in range(180, 0, -10):
                #    servo(degree)
                #    sleep(0.001)
                #    print("decreasing -- "+str(degree))
                distance = ultra()
            except:
                print("Temp sensor read failure!")
                temp = 0
                humidity = 0
                distance = 0
                sound = 0
        else:
            temp = 0
            humidity = 0
            distance = 0
            sound = 0
            
        f = open(public_folder+url[0]+url[1], 'r')
        response = f.read()
        # response = response.replace('%s', time_str)
        response = response.replace('%pop', ledState)
        response = response.replace('%temp', "Temperature: {}C".format(temp))
        response = response.replace('%humidity', "Humidity: {}%".format(humidity))
        response = response.replace('%time_current', "Current time: {}".format(timestring))
        response = response.replace('%time_start', "Start time: {}".format(timestring_start))
        time_str_current = "%02d:%02d:%02d"%(timestamp[4:7])
        response = response.replace('%s', time_str_current)
        response = response.replace('%detectsound', "Sound ADC level: "+str(sound))
        response = response.replace('%distance', "Distance of Object: "+str(distance)+"cm")
        #print(timestamp - timestamp_start)
        f.close()
        # cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(header+response)
        cl.close()
        
    except OSError as e:
        cl.close()
        print('connection closed')
 