---
title: Reconfiguring the Kinect
date: 2013-02-10
---

Having finished restructuring my code I decided to try the whole unit out, only to find that I had been developing my code using a Kinect for Windows, however the Kinect that had been soldered to the Roomba is a Kinect for XBox.

Thankfully the OpenNI drivers support both (if anything the Kinect for XBox is better supported), however I had some trouble making it work with my code (or indeed the provided samples). After much searching I replaced the camera configuration XML file that I had been using. Another thing I had not realised is that the Kinect has two powered-on modes, one a standby mode where the front green light flashes but it does not respond to queries, and another where it is fully on. As far as I can tell these modes are indistinguishable. The way that the Kinect is wired to the Roomba means that when the Roomba is charging only enough power for the Kinect to enter the first standby mode is provided.

Once I had figured this out and recompiled with the new configuration XML the camera worked perfectly and was identical to the Kinect for Windows one. The results are shown below:

![](images/roomba_kinect_first.jpg)
