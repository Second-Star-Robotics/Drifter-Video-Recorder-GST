#Driftcam Video Capture
#
#Second Star Robotics
#August 25, 2020
#to Launch:
#/usr/bin/python3 /home/ssr/Desktop/pyPro/opencv/Driftcam_Video_Recorder.py

# organize imports
import numpy as np
import cv2
import time
import csv
import math
import RPi.GPIO as GPIO

#GPIO SETUP
# Pin Definitions
idle_flag_out = 6  # BOARD pin 31, BCM pin 6, Output True if Jetson is idle
record_enable_in = 13  # BCM pin 13, BOARD pin 33, Input True if Record requested

# Board pin-numbering scheme
GPIO.setmode(GPIO.BCM)

# set pin as an output pin with optional initial state of HIGH
GPIO.setup(idle_flag_out, GPIO.OUT, initial=GPIO.HIGH)
GPIO.output(idle_flag_out, GPIO.HIGH)
GPIO.setup(record_enable_in, GPIO.IN)  # set pin as an input pin

#Set up camera
path_str = "/media/9d84029e-f1ef-4e7b-adb1-4f0848d37785/captures/"

capW = 1920
capH = 1080
dispW = 960
dispH = 570
flip = 2
camSet='nvarguscamerasrc !  video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1 ! nvvidconv flip-method='+str(flip)+' ! video/x-raw, width='+str(capW)+', height='+str(capH)+', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'

pre_Record_Enable = 0

#Main Loop
while True:
    #Check for Record Enable
    Record_Enable = GPIO.input(record_enable_in)
    GPIO.output(idle_flag_out, GPIO.LOW)

    if Record_Enable:
        pre_Record_Enable = 1


        #Set up Camera
        cam=cv2.VideoCapture(camSet)

        #Display Status Information
        filename_str = time.strftime("%Y%m%d-%H%M%S-Capture")
        print("Recording Video : " + path_str + filename_str + ".avi")

        #Set up Output Video
        #outVid = cv2.VideoWriter(path_str + filename_str + ".avi", cv2.VideoWriter_fourcc(*'XVID'), 30, (capW, capH))
        outVid = cv2.VideoWriter(path_str + filename_str + ".avi", cv2.VideoWriter_fourcc(*'XVID'), 30, (dispW, dispH))

        #Video Capture Loop
        frameCount = 0

        while Record_Enable:
            #Read a frame from camera 
            ret, frame=cam.read()

            #Add text to frame
            frame_str1 = filename_str + ".avi"
            frameBurnin1 = cv2.putText(frame, frame_str1, (10, 1000), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,255), 1, cv2.LINE_AA)
            frame_str2 =  time.strftime("%Y/%m/%d %H:%M:%S Frame:") + str(frameCount)
            frameBurnin2 = cv2.putText(frameBurnin1, frame_str2, (10, 1030), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,255), 1, cv2.LINE_AA)
            frame_str3 =  time.strftime("Depth: 0.0 m Temp: 22.7 C")
            frameOut = cv2.putText(frameBurnin2, frame_str3, (10, 1060), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,255), 1, cv2.LINE_AA)
    
            #Resize preview frame
            frameSmall = cv2.resize(frameOut,(dispW, dispH))

            #Display frame
            #cv2.imshow("Capture", frameSmall)

            #Write a frame
            outVid.write(frameSmall)

            frameCount = frameCount + 1

            #Poll record line from Driftcam controller
            Record_Enable = GPIO.input(record_enable_in)
    
            if cv2.waitKey(1)==ord('q'):
                break
    else:
        time.sleep(0.1)
        if pre_Record_Enable==1:
            pre_Record_Enable = 0
            print("Stopping Video and Camera")
            cam.release()
            outVid.release()
            cv2.destroyAllWindows()
            GPIO.output(idle_flag_out, GPIO.HIGH)

