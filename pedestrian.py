import numpy as np
import math
import cv2

#cap = cv2.VideoCapture('IMG_4268.mp4')
# fgbg = cv2.createBackgroundSubtractorMOG2(history=5, varThreshold=150)
cap = cv2.VideoCapture('1.mp4')
print cap.get(cv2.CAP_PROP_FRAME_WIDTH)
#cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640.0)
vidw = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
vidh = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
vidar = vidw/vidh
show_height=300

#settings here
PEOPLE_HEIGHT_MIN = 90
PEOPLE_WIDTH_MIN  = 40

MIDDLE_ZONE_HEIGHT = 100
DELTA_Y = 0
LINE_1_P1_X=int(0)
LINE_1_P1_Y=int(400)
LINE_1_P2_X=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
LINE_1_P2_Y=int(LINE_1_P1_Y+DELTA_Y)

LINE_2_P1_X=int(0)
LINE_2_P1_Y=int(LINE_1_P1_Y+MIDDLE_ZONE_HEIGHT)
LINE_2_P2_X=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
LINE_2_P2_Y=int(LINE_2_P1_Y+DELTA_Y)
LINE_SLOP=(float(LINE_1_P2_Y) - float(LINE_1_P1_Y))/(float(LINE_1_P2_X) - float(LINE_1_P1_X))
print LINE_SLOP
fgbg = cv2.bgsegm.createBackgroundSubtractorMOG(history=150, backgroundRatio=0.3)

def line1(x,y):
    #return y - (29*x)/96.0 - LINE_1_P1_Y
    return y - LINE_SLOP*x - LINE_1_P1_Y

def line2(x,y):
    #return y - (29*x)/96.0 - LINE_2_P1_Y
    return y - LINE_SLOP*x - LINE_2_P1_Y

crossedAbove = 0
crossedBelow = 0
points = set()
pointFromAbove = set()
pointFromBelow = set()

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('pedestrianOutput.avi',fourcc, 25.0, (1920,1080))
font = cv2.FONT_HERSHEY_SIMPLEX
while(1):
    # step 1 
    # get last frame points 
    pointInMiddle = set()
    prev = points
    points = set()
    ret, frame = cap.read()
    if frame is None:
        print 'Meet last frame'
        break;
    fgmask = frame
    fgmask = cv2.blur(frame, (10,10))
    fgmask = fgbg.apply(fgmask)
    fgmask = cv2.medianBlur(fgmask, 7)
    oldFgmask = fgmask.copy()
    image, contours, hierarchy = cv2.findContours(fgmask, cv2.RETR_EXTERNAL,1)
    # step 2 
    # get all points this frame
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        # caculate center point of all people in this frame
        if w>PEOPLE_WIDTH_MIN  and h>PEOPLE_HEIGHT_MIN:
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2, lineType=cv2.LINE_AA)
            point = (int(x+w/2.0), int(y+h/2.0))
            points.add(point)

    for point in points:
        (xnew, ynew) = point
        # add all center point into set
        if line1(xnew, ynew) > 0 and line2(xnew, ynew) < 0:
            pointInMiddle.add(point)
        # step 3 tracking and counting 
        # 'A' person in last frame is (xold,yold)
        # 'A' in this frame is (xnew, ynew) and dist(old ,new) < 120
        for prevPoint in prev:
            (xold, yold) = prevPoint
            dist = cv2.sqrt((xnew-xold)*(xnew-xold)+(ynew-yold)*(ynew-yold))
            # if dist<120 ,prevPoint and point are the same people 
            if dist[0] <= 120: 
                # in the middle
                if line1(xnew, ynew) >= 0 and line2(xnew, ynew) <= 0:
                    # from above
                    if line1(xold, yold) < 0: # Point entered from line above
                        pointFromAbove.add(point)
                    # from below 
                    elif line2(xold, yold) > 0: # Point entered from line below
                        pointFromBelow.add(point)
                    # last frame in the middle
                    else:   # Point was inside the block
                        # update the position of pointfromblew
                        if prevPoint in pointFromBelow:
                            pointFromBelow.remove(prevPoint)
                            pointFromBelow.add(point)
                        # update the position of pointfromabove
                        elif prevPoint in pointFromAbove:
                            pointFromAbove.remove(prevPoint)
                            pointFromAbove.add(point)
                # step 4
                # counting 
                if line1(xnew, ynew) < 0 and prevPoint in pointFromBelow: # Point is above the line
                    print 'One Crossed Above'
                    print point
                    crossedAbove += 1
                    pointFromBelow.remove(prevPoint)

                if line2(xnew, ynew) > 0 and prevPoint in pointFromAbove: # Point is below the line
                    print 'One Crossed Below'
                    print point
                    crossedBelow += 1
                    pointFromAbove.remove(prevPoint)

    for point in points:
        if point in pointFromBelow:
            cv2.circle(frame, point, 3, (255,0,255),6)
        elif point in pointFromAbove:
            cv2.circle(frame, point, 3, (0,255,255),6)
        else:
            cv2.circle(frame, point, 3, (0,0,255),6)
    #cv2.line(frame, (0,300), (1920,880), (255, 0, 0), 4)
    #cv2.line(frame, (0,500), (1920,1080), (255, 0, 0), 4)
    cv2.line(frame, (LINE_1_P1_X,LINE_1_P1_Y), (LINE_1_P2_X,LINE_1_P2_Y), (255, 0, 0), 4)
    cv2.line(frame, (LINE_2_P1_X,LINE_2_P1_Y), (LINE_2_P2_X,LINE_2_P2_Y), (255, 0, 0), 4)
    cv2.putText(frame,'People Going Above = '+str(crossedAbove),(50,50), font, 1,(255,255,255),2,cv2.LINE_AA)
    cv2.putText(frame,'People Going Below = '+str(crossedBelow),(50,100), font, 1,(255,255,255),2,cv2.LINE_AA)
    #cv2.imshow('a',oldFgmask)
    to_draw = cv2.resize(frame, (int(show_height*vidar), int(show_height)))

    cv2.imshow('frame',to_draw)

    
    out.write(frame)
    l = cv2.waitKey(1) & 0xff
    if l == 27:
        break
cap.release()
cv2.destroyAllWindows()
