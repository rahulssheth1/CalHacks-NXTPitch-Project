# NXTPitch

## Background
NXTPitch is a continuation project that my partner and I developed at Cal Hacks 2017, which enables students to upload videos/pdf documents and receive feedback regarding how effective the content within that medium is. We present our feedback in three main areas: emotional, professional, and highlighted content. Through this feedback students can better tailor their professional content to capture who they truly are, and get that job at their dream company. For this project, my partner and I won the PWC Tech Challenge Sponsorship prize. To see our project in action, please check out our DevPost: https://devpost.com/software/nxtpitch

## Dependencies
To run the software first use the requirements.txt file to install all the python packages. You will also need the command line tool ffmpeg, which can be found at their website http://www.ffmpeg.org/. Finally you will need API keys for the various APIS: Microsoft Azure, Watson Developer Cloud, and Eyeris.

## Setup
After collecting all the dependencies, open your directory and copy a video file called "new.mov" into it. This is the video file that the analysis will be performed on. Then run "python run.py", and you can then navigate to http://127.0.0.1:5000/ in your browser to see the feedback.
