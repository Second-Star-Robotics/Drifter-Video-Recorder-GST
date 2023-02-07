import RPi.GPIO as GPIO
import sys
import traceback
import argparse
import time

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject  # noqa:F401,F402

def on_message(bus: Gst.Bus, message: Gst.Message, loop: GObject.MainLoop):
    mtype = message.type
    """
        Gstreamer Message Types and how to parse
        https://lazka.github.io/pgi-docs/Gst-1.0/flags.html#Gst.MessageType
    """
    if mtype == Gst.MessageType.EOS:
        print("End of stream")
        loop.quit()

    elif mtype == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(err, debug)
        loop.quit()

    elif mtype == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        print(err, debug)

    return True

#GPIO SETUP
# Pin Definitions
#print("Setup GPIO ports")
#idle_flag_out = 6  # BOARD pin 31, BCM pin 6, Output True if Jetson is idle
#record_enable_in = 13  # BCM pin 13, BOARD pin 33, Input True if Record requested

# Board pin-numbering scheme
#GPIO.setmode(GPIO.BCM)

# set pin as an output pin with optional initial state of HIGH
#print("Set Idle Flag = HIGH")
#GPIO.setup(idle_flag_out, GPIO.OUT, initial=GPIO.HIGH)
#GPIO.output(idle_flag_out, GPIO.HIGH)
#GPIO.setup(record_enable_in, GPIO.IN)  # set pin as an input pin

# FIELD TEST CODE START
#time.sleep(30)
# END OF FIELD TEST CODE

TEST_VID_LENGTH = 120

# Initializes Gstreamer, it's variables, paths
print("Initialize GStreamer")
Gst.init(sys.argv)

# Generate GStreamer Pipeline String
path_str = "/media/ssr/usb-drive/capture/"
#filename_str = path_str + time.strftime("%Y%m%d-%H%M%S-Capture") + ".avi"
left_filename_str = path_str + time.strftime("%Y%m%d-%H%M%S-left")
right_filename_str = path_str + time.strftime("%Y%m%d-%H%M%S-right")
print("Left Output File : " + left_filename_str)
print("Right Output File : " + right_filename_str)
#capW = 1920
#capH = 1080
#dispW = 960
#dispH = 570
#flip = 2
#DEFAULT_PIPELINE="nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1 ! omxh264enc ! video/x-h264, stream-format=(string)byte-stream ! h264parse ! qtmux ! filesink location=" + filename_str
#DEFAULT_PIPELINE="nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1 ! omxh264enc ! video/x-h264, stream-format=(string)byte-stream ! h264parse ! splitmuxsink location=" + filename_str + "%05d.mp4 max-size-time=300000000000"
#vDEFAULT_PIPELINE="v4l2src device=/dev/video2 ! video/x-h264, width=1920, height=1080, framerate=30/1, format=H264 ! splitmuxsink location=" + filename_str + "%05d.mp4 max-size-time=300000000000"
DEFAULT_PIPELINE="v4l2src device=/dev/video3 ! videorate  ! image/jpeg,framerate=30/1,width=1920,height=1080 ! jpegparse ! avimux name=muxer1 ! filesink location=" + left_filename_str + ".avi v4l2src device=/dev/video1 ! videorate  ! image/jpeg,framerate=30/1,width=1920,height=1080 ! jpegparse ! avimux name=muxer2 ! filesink location=" + right_filename_str + ".avi"

ap = argparse.ArgumentParser()
ap.add_argument("-p", "--pipeline", required=False,
                default=DEFAULT_PIPELINE, help="Gstreamer pipeline without gst-launch")

args = vars(ap.parse_args())

# original on_message HERE

command = args["pipeline"]

# Gst.Pipeline https://lazka.github.io/pgi-docs/Gst-1.0/classes/Pipeline.html
# https://lazka.github.io/pgi-docs/Gst-1.0/functions.html#Gst.parse_launch
pipeline = Gst.parse_launch(command)

# https://lazka.github.io/pgi-docs/Gst-1.0/classes/Bus.html
bus = pipeline.get_bus()

# allow bus to emit messages to main thread
bus.add_signal_watch()

# Start pipeline
pipeline.set_state(Gst.State.PLAYING)
print("pipeline.set_state(Gst.State.PLAYING)")

# Init GObject loop to handle Gstreamer Bus Events
loop = GObject.MainLoop()

# Add handler to specific signal
# https://lazka.github.io/pgi-docs/GObject-2.0/classes/Object.html#GObject.Object.connect
bus.connect("message", on_message, loop)

#Send Idle Flag Low
print("Send idle_flag_out = LOW")

#While recording, poll record signal line and wait until signal goes LOW
print("Wait for Stop Signal")
Record_Enable = 1
while Record_Enable:
    time.sleep(TEST_VID_LENGTH)
    Record_Enable = 0
print("Stop Signal Recieved")

#Generate an EOS Message
print("pipeline.send_event(Gst.Event.new_eos())")
pipeline.send_event(Gst.Event.new_eos())
#Let the stream shut down

#Loop until shutdown
try:
    print("loop.run()")
    loop.run()
except Exception:
    traceback.print_exc()
    print("loop.quit()")
    loop.quit()

# Stop Pipeline
print("pipeline.set_state(Gst.State.NULL)")
pipeline.set_state(Gst.State.NULL)

#Send Idle Flag HIGH
print("Send idle_flag_out = HIGH")
GPIO.output(idle_flag_out, GPIO.HIGH)


