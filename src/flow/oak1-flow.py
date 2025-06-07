#!/usr/bin/env python3
from pathlib import Path

import cv2
import depthai as dai
import numpy as np
import time

pipeline = dai.Pipeline()

# Create the nodes
camera = pipeline.create(dai.node.ColorCamera)
detectionNetwork = pipeline.create(dai.node.YoloDetectionNetwork)
#objectTracker = pipeline.create(dai.node.ObjectTracker)
#sync = pipeline.create(dai.node.Sync)
detections = pipeline.create(dai.node.XLinkOut)
frame = pipeline.create(dai.node.XLinkOut)

# Name the output
detections.setStreamName("detections")
frame.setStreamName("frame")

# Properties
camera.setPreviewSize(320, 320)
camera.setVideoSize(2024, 1520)
camera.setResolution(dai.ColorCameraProperties.SensorResolution.THE_12_MP)
camera.setInterleaved(False)
camera.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
#camera.initialControl.setManualFocus(50)

detectionNetwork.setBlobPath(Path("/models/insect-detect-yolo11.blob"))
detectionNetwork.setConfidenceThreshold(0.5)
detectionNetwork.setNumClasses(1)
detectionNetwork.input.setBlocking(False)

#objectTracker.setDetectionLabelsToTrack([0])  # insect
#objectTracker.setTrackerType(dai.TrackerType.ZERO_TERM_COLOR_HISTOGRAM)
#objectTracker.setTrackerIdAssignmentPolicy(dai.TrackerIdAssignmentPolicy.SMALLEST_ID)

# Linking
camera.preview.link(detectionNetwork.input)  # camera -> network in
#detectionNetwork.out.link(objectTracker.inputDetections)
detectionNetwork.passthrough.link(frame.input)
detectionNetwork.out.link(detections.input)

#camera.video.link(sync.inputs["frame"])
#objectTracker.out.link(sync.inputs["track"])

# Connect to device and start pipeline
with dai.Device(pipeline) as device:
    print(device.getConnectedCameraFeatures())

    #device.setLogLevel(dai.LogLevel.DEBUG)
    #device.setLogOutputLevel(dai.LogLevel.DEBUG)
    detections = device.getOutputQueue("detections", 4, False)
    frame = device.getOutputQueue("frame", 4, False)

    startTime = time.monotonic()
    counter = 0
    fps = 0
    color = (255, 255, 255)

    while(True):
        dets = detections.get()
        frm = frame.get()
        cvFrame = frm.getCvFrame()

        cv2.imwrite("frame.jpg", cvFrame)
        i = 0
        for det in dets.detections :
            if det.confidence > 6.5:
                xmax = int(det.xmax * 320)
                xmin = int(det.xmin * 320)
                ymax = int(det.ymax * 320)
                ymin = int(det.ymin * 320)
                #print("confidence = ", det.confidence, " xmax = ", xmax, " ymax = ", ymax, " xmin = ",xmin, " xmin = ", xmin , " ymin = ", ymin)
                crop = cvFrame[ymin:ymax, xmin:xmax]
                file = f"crop{i}.jpg"
                cv2.imwrite(file, crop)
                i = i+1

        #counter+=1
        #current_time = time.monotonic()
        #if (current_time - startTime) > 1 :
        #    fps = counter / (current_time - startTime)
        #    counter = 0
        #    startTime = current_time

        #frame = imgFrame.getCvFrame()
        #trackletsData = track.tracklets
        #for t in trackletsData:
        #    roi = t.roi.denormalize(frame.shape[1], frame.shape[0])
        #    x1 = int(roi.topLeft().x)
        #    y1 = int(roi.topLeft().y)
        #    x2 = int(roi.bottomRight().x)
        #    y2 = int(roi.bottomRight().y)

        #    try:
        #        label = labelMap[t.label]
        #    except:
        #        label = t.label

            #cv2.putText(frame, str(label), (x1 + 10, y1 + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            #cv2.putText(frame, f"ID: {[t.id]}", (x1 + 10, y1 + 35), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            #cv2.putText(frame, t.status.name, (x1 + 10, y1 + 50), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            #cv2.rectangle(frame, (x1, y1), (x2, y2), color, cv2.FONT_HERSHEY_SIMPLEX)

            #cv2.putText(frame, f"X: {int(t.spatialCoordinates.x)} mm", (x1 + 10, y1 + 65), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            #cv2.putText(frame, f"Y: {int(t.spatialCoordinates.y)} mm", (x1 + 10, y1 + 80), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            #cv2.putText(frame, f"Z: {int(t.spatialCoordinates.z)} mm", (x1 + 10, y1 + 95), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)

        #cv2.putText(frame, "NN fps: {:.2f}".format(fps), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color)

        #cv2.imshow("tracker", frame)

        #if cv2.waitKey(1) == ord('q'):
        #    break
