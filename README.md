# The Webcam Manager

This program
 - captures a video stream through opencv
 - detects and track motion
 - puts a bounding box around the detected foreign body
 - puts time stamps and status of the motion detection
 - if the motion is detected saves the first image, starts saving the video stream, and sends email to those who are in the contacts file
   - creates a smtp email server with gmail using ssl and 2-factor authentication service present
   - reads the recipients names andd address
   - prepare the content of the email 
   - sends email to the recipients to scare them
   - keeps log of everything
 - if the last email was sent less than SECONDSBEFORELASTEMAIL seconds ago, doesnot send anything

## Installation
```
git clone https://github.com/arindam-bose/the-webcam-manager
cd the-webcam-manager
virtualenv venv -p /usr/bin/python3
source venv/bin/activate
pip install -r requirements.txt
```

## Requirements
- opencv-python
- numpy
- google-api-python-client 
- google-auth-httplib2 
- google-auth-oauthlib


Run
```
python demo.py --img_path './images/' --vid_path './videos/' --contacts_filename './contacts.txt' --msg_filename './message.txt' --log_path './movements.log'
```

or simply
```python demo.py```
