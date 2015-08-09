# Introduction #
Client certificates are not very well supported on mobile devices like phones and tablets, but with the release of [Firefox 4 Mobile](http://www.mozilla.com/en-US/mobile/download/) we got a working solution at least for Android users. The setup is not very user friendly because Firefox doesn't include the usual certificate management interface on mobile (yet?), but it works with a little command line work or with the more recently added Cert Manager add-on. Unfortunately this solution stopped working again after Firefox 13 where the UI engine was completely rewritten. In Android 4.0+ the native browser supports client certificates, however. Apparently Google have also implemented it in the Chrome beta for Android, so it may arrive in the official release soon.
We have provided a couple of check boxes for touch screen use on the Files and Jobs pages to make them usable even from devices without traditional right and double click support.


# Instructions #
Instructions for each supported platform follows here. Feel free to add more if you know of other supported platforms.

## Android ##

### Native Android 4.0+ and Chrome Browser ###
Copy the cacert.pem and cert.p12 files to the phone and rename cacert.pem to cacert.crt. Install a file manager like OI File Manager from the app store and tap each of the files from it to launch the certificate import dialog. Afterwards the keys and certificates are available in the global credentials store used e.g. by the native browser. The same procedure should apply for versions of Chrome with user certificate support.


### Firefox + Cert Manager ###
Open Firefox and install the Cert Manager add-on from the list of official add-ons. You need a file manager like e.g. OI File manager on the device to select your p12 file. Go to Your Add-ons and open Options for Cert Manager where you can choose to import CA certificates and user certificates. Each of them will open a file manager where you select the file to import followed by a request for your optional Firefox master password and the certificate password.


### Firefox + Command Line ###
These step-by-step instructions were tested on a HTC Desire connected to a Linux box but they should work on other recent Android devices and computers with minor changes.

  * install Firefox from the market (may require Android 2.2 or later) and move it to SD card for write access
  * connect android device with a usb cable to e.g. a linux box with p12util and certutil installed (libnss3-tools package on deb based systems).
  * select disk drive mode on the device and mount it on the computer when it shows up (this example assumes mount at $MNT)
  * open a shell, change to firefox profile dir and import user and CA certificate directly on the device disk. Hit enter twice if you don't use master password or enter the master password once:
```
cd $MNT/Android/data/org.mozilla.firefox/files/mozilla/*.default/
pk12util -i ~/.mig/cert.p12 -d sql:.
[optional master password mentioned above and then your MiG certificate password]
certutil -A -d sql:. -n 'MiG CA' -t "CT,," -i ~/.mig/cacert.pem
```
or enter the Firefox master password once and your MiG certificate password if you enabled master password in your mobile Firefox.
  * optionally verify that certificates are now in the certificate store:
```
certutil -L -d sql:.
[lists all your certificates including MiG CA and user certificate]
```
  * write the changes and prepare for unmounting the device:
```
sync
cd
```
  * unmount the device on the computer and switch to charge only mode on the device before disconnecting the usb cable


## Maemo / Tizen ##
Untested but the procedure for Android should be usable again, only with a different profile path.


## Conclusion ##
Now you can fire up your browser on the device and surf to the certificate protected MiG pages. Enjoy!

Please note that old Firefox versions did _not_ support password protecting the certificate store, so you needed to leave the password empty there. With recent versions you can enable master password in Firefox and use it during import.
Hopefully Mozilla will include the full certificate management interface at some point, but until then the above should be a work around.

Please **beware** of the security implications of storing without a password and [report any potential abuse](ContactUs.md).


## Background ##
Additional information can be found at:
  * http://groups.google.com/group/migrid/browse_thread/thread/46d0ea995beb6904?hl=en
  * http://code.google.com/p/android/issues/detail?id=8196
  * http://code.google.com/p/chromium/wiki/LinuxCertManagement