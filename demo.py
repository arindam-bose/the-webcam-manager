#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 19:44:29 2020

@author: abose4
"""

import cv2
import logging
import argparse
from datetime import datetime
from configparser import ConfigParser


def initialize_capture():
    """
    Initializes the video capture and the output file handler
    
    Returns
    -------
    cap : opencv videocapture
        contains the capture handler.
    out : opencv videowriter
        contains the output file handler.

    """
    try:
        # capture video
        cap = cv2.VideoCapture(VIDNUM)
        
        timenow = datetime.now()
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
        outvidname = VIDEOFOLDER + 'movevid_{0}.avi'.format(timenow.strftime(STRFRMT)[:-3])
        out = cv2.VideoWriter(outvidname, fourcc, VIDEOFRAMERATE, (frame_width, frame_height))
    except Exception as e:
        logger.error(e)
        cv_exit(cap, out)
    return cap, out


def detect_motion(cap, out):
    """
    Does several things
        1. captures the video stream
        2. detects and track motion
        3. puts a bounding box around the detected foreign body
        4. puts time stamps and status of the motion detection
        5. if the motion is detected saves the first image, starts saving the video stream, and 
           sends email to those who are in the contacts file
        6. if the last email was sent less than SECONDSBEFORELASTEMAIL seconds ago, doesnot send anything
        
    Parameters
    ----------
    cap : opencv videocapture
        contains the capture handler.
    out : opencv videowriter
        contains the output file handler.

    Returns
    -------
    None.

    """
    import numpy as np
    import threading

    try:
        # always save the first frame as a black screen with starting time stamp
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        zeroframe = np.zeros((frame_height, frame_width, 3), dtype='uint8')

        if out:
            cv2.putText(zeroframe, 'Start recording', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(zeroframe, datetime.now().strftime(STRFRMT)[:-3], (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            for ii in range(VIDEOFRAMERATE):
                out.write(zeroframe)
            
		# discard first couple of frames for video stabilization
        for ii in range(10):
            ret, frame = cap.read()
			
        # next capture first two frames
        ret, frame1 = cap.read()
        ret, frame2 = cap.read()
        emailsent = False
        
        # continuos stream starts here
        while cap.isOpened():
            # finds motion
            diff = cv2.absdiff(frame1, frame2)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5,5), 0)
            _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
            dilated = cv2.dilate(thresh, None, iterations=3)
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            movestatus = False
        
            # put a bounding box
            for contour in contours:
                (x, y, w, h) = cv2.boundingRect(contour)
                
                # if blob area is smaller than 900 pixels, just ignore
                if cv2.contourArea(contour) < 900:
                    continue
                cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)
                movestatus = True
            
            # put time stamps and the status
            timenow = datetime.now()
            cv2.putText(frame1, 'Status:', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            cv2.putText(frame1, timenow.strftime(STRFRMT)[:-3], (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            if movestatus:
                logger.info('Movement detected')
                cv2.putText(frame1, "Movement detected", (70, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                out.write(frame1)
                
                # if an email hasn't been sent within SECONDSBEFORELASTEMAIL seconds
                if not emailsent:
                    timelastemail = datetime.now()
                    filename = IMAGEFOLDER + 'moveimg_{0}.png'.format(timenow.strftime(STRFRMT)[:-3])
                    cv2.imwrite(filename, frame1)
                    th = threading.Thread(target = send_email, args=(filename,))
                    th.start()
                    emailsent = True
                
                if (divmod((datetime.now() - timelastemail).total_seconds(), 60)[1] >= SECONDSBEFORELASTEMAIL):
                    emailsent = False
                    
            else:
                cv2.putText(frame1, 'Static', (70, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
            cv2.imshow('feed', frame1)
            frame1 = frame2
            ret, frame2 = cap.read()
            
            # press q to exit safely
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except Exception as e:
        logger.error(e)
        cv_exit(cap, out)
    
    cv_exit(cap, out)


def cv_exit(cap, out):
    """
    Exits all video handler safely

    Parameters
    ----------
    cap : opencv videocapture
        contains the capture handler.
    out : opencv videowriter
        contains the output file handler.

    Returns
    -------
    bool
        false if weird things happened, otherwise true

    """
    try:
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        return True
    except Exception as e:
        logger.error(e)
        return False
 
    
def get_contacts(filename):
    """
    Return two lists names, emails containing names and email addresses
    read from a file specified by filename.

    Parameters
    ----------
    filename : string
        full filename and path

    Returns
    -------
    names : list
        a list of names in order.
    emails : list
        a list of email addresses in the same order.

    """
    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails


def read_template(filename):
    """
    Returns a Template object comprising the contents of the 
    file specified by filename.    

    Parameters
    ----------
    filename : string
        full filename path.

    Returns
    -------
        a Template object

    """
    from string import Template

    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def send_email(filename):
    """
    1. creats a smtp email server with gmail using ssl and 2-factor authentication service present
    2. reads the recipients names andd address
    3. prepare the content of the email 
    4. sends email to the recipients to scare them
    5. keeps log of everything
    6. it's pretty spooky, one time it scared me at 3 o'clock in the morning during coronadays of 2020.
       I setup it for outside. No one was walking, yet I got the email and saw nothing in the ficture. 
	   It turned out the camera had a problem of switching left and right halves, and once it is corrected, 
	   the program sees it as a difference and thus motion 

    Parameters
    ----------
    filename : string
        file name of the image that should be in the attachment.

    Returns
    -------
    None.

    """
    import smtplib
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email import encoders

    logger.info('Email being sent to all the emails in contacts')
    try:
        names, emails = get_contacts(CONTACTSFILENAME) # read contacts
        message_template = read_template(MESSAGEFILENAME)
        server = smtplib.SMTP_SSL(EMAILHOST, port=EMAILPORT)
        server.ehlo()
        server.login(SENDERADDRESS, SENDERPASSWORD)
    except Exception as e:
        logger.error(e)
        
    # For each contact, send the email:
    for name, email in zip(names, emails):
        msg = MIMEMultipart()       # create a message

        # add in the actual person name to the message template
        message = message_template.substitute(PERSON_NAME=name.title(), SECONDS=SECONDSBEFORELASTEMAIL)

        # setup the parameters of the message
        msg['From'] = SENDERADDRESS
        msg['To'] = email
        msg['Subject'] = EMAILSUB
        
        # add in the message body
        msg_content = MIMEText(message, 'html')
        msg.attach(msg_content)
        # to add an attachment is just add a MIMEBase object to read a picture locally.
        with open(filename, 'rb') as f:
            # set attachment mime and file name, the image type is png
            mime = MIMEBase('image', 'png', filename = filename)
            # add required header data:
            mime.add_header('Content-Disposition', 'attachment', filename = filename)
            mime.add_header('X-Attachment-Id', '0')
            mime.add_header('Content-ID', '<0>')
            # read attachment file content into the MIMEBase object
            mime.set_payload(f.read())
            # encode with base64
            encoders.encode_base64(mime)
            # add MIMEBase object to MIMEMultipart object
            msg.attach(mime)
            logger.info(msg_content)
        
        # send the message via the server set up earlier.
        try:
            server.sendmail(msg['From'], msg["To"], msg.as_string())
        except Exception as e:
            logger.error(e)
        del msg
    
    # Terminate the SMTP session and close the connection
    server.quit()

    
def mkdir_p(mypath):
    """
    Creates a directory. equivalent to using mkdir -p on the command line

    Parameters
    ----------
    mypath : string
        folder path.

    Returns
    -------
    None.

    """
    from errno import EEXIST
    from os import makedirs, path

    try:
        makedirs(mypath)
    except OSError as exc:  # Python >2.5
        if exc.errno == EEXIST and path.isdir(mypath):
            pass
        else:
            raise
 
    
def main():
    """
    The main routine

    Returns
    -------
    None.

    """
    logger.info('Warming up camera...')
    cap, out = initialize_capture()
    
    logger.info('Capture started...')
    detect_motion(cap, out)



if __name__ == "__main__":
    # manage arguments   
    parser = argparse.ArgumentParser()
    parser.add_argument('--img_path',
                    default='./images/',
                    type=str, help='Save image path')
    parser.add_argument('--vid_path',
                    default='./videos/',
                    type=str, help='Save video path')
    parser.add_argument('--contacts_filename',
                    default='./contacts.txt',
                    type=str, help='Contacts file path')
    parser.add_argument('--msg_filename',
                    default='./message.txt',
                    type=str, help='Message file path')
    parser.add_argument('--log_path',
                    default='./movements.log',
                    type=str, help='log file path')
    args = parser.parse_args()
    
    # prepare the configs
    config = ConfigParser()
    config.read('config.ini')
    
    # prepare variables
    IMAGEFOLDER      = args.img_path
    VIDEOFOLDER      = args.vid_path
    CONTACTSFILENAME = args.contacts_filename
    MESSAGEFILENAME  = args.msg_filename
    LOGNAME          = args.log_path
    
    VIDEOFRAMERATE         = config.getint('settings', 'VideoFrameRate')
    VIDNUM                 = config.getint('settings', 'VideoNumber')
    SENDERADDRESS          = config.get('settings', 'SenderAddress')
    SENDERPASSWORD         = config.get('settings', 'SenderPassword')
    EMAILHOST              = config.get('settings', 'EmailHost')
    EMAILPORT              = config.getint('settings', 'EmailPort')
    EMAILSUB               = config.get('settings', 'EmailSubject')
    SECONDSBEFORELASTEMAIL = config.getint('settings', 'SecondsBeforeLastMail') 
    STRFRMT                = '%Y-%m-%d %H:%M:%S.%f'

    # prepare the folders
    mkdir_p(args.img_path)
    mkdir_p(args.vid_path)
    
    # set logs
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(LOGNAME)
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # call main now
    main()
  
    

