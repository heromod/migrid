# Introduction #
These install notes are based on Simon A.F. Lund's experiences from [installation of a virtualized MiG site](http://www.safl.dk/mig/setup/). They should not be very version-specific but they have been updated to refer to the current release.


# Minimum Intrusion Grid - Installation and Configuration #
This is note of following the documentation for installation of a MiG-server from the documentation sources in the References section. With added information on operating system installation and additional tools used in the process.

# Environment #

  * A Lenovo x200 laptop running Xubuntu 10.4 with [VirtualBox](http://www.virtualbox.org)
  * Ubuntu 10.4 64-bit was the chosen operating system and installed in a virtual machine


## Virtual Machine ##
512MB ram, bridged network.


## Basic OS installation ##
Used the latest ubuntu-server-amd64 iso from ubuntu.com and during installation i chose to create the "mig" user, installed a base system with OpenSSH and selected "without automatic updates".

After installation and rebooted then did:
```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install postfix mailutils apache2-mpm-prefork openssh-server screen
```


## Firewall notes ##
  * 443 allow ingoing is required
  * 22 allow ingoing is useful for ssh
  * 80 allow ingoing can be useful for unspecified purposes


# Following the Installation Guide #
A default installation will have a user-account on the system named 'mig', the Apache webserver will run under this user account and the homedirectory /home/mig will exist. A default directory layout will look like:

```
/home/mig/mig           - Server code
/home/mig/state         - User-files, and other state-files
/home/mig/certs         - MiG certificate-files
```

MiG is state-machine with logic in /home/mig/mig and state represented as the set of files in /home/mig/state. Without the proper set of directories MiG will complain and not behave properly.

```
/home/mig/state/user_home
/home/mig/state/user_home/.settings
/home/mig/state/user_home/.widgets
/home/mig/state/user_pending
/home/mig/state/user_cache
/home/mig/state/mrsl_files
/home/mig/state/resource_home
/home/mig/state/resource_pending
/home/mig/state/webserver_home
/home/mig/state/gridstat_files
/home/mig/state/vgrid_home
/home/mig/state/vgrid_home/Generic
/home/mig/state/mig_system_files
```


### Configuration ###
This example is for 1.4.3 but you should generally use the latest stable release avilable.
```
VERSION=1.4.3
wget http://migrid.googlecode.com/files/mig-$VERSION.tgz
tar xzf mig-$VERSION.tgz
mv mig-$VERSION/* .
rmdir mig-$VERSION/
rm mig-$VERSION.tgz
chmod -R 700 ~mig
cd mig/install
./generateconfs.py
cd ~
cp mig/install/MiGserver.conf mig/server/
```

Modified "~/mig/server/MiGserver.conf":
```
server_fqdn = migserver
admin_email = mig
auto_add_cert_user = True
```

### SSH keys on MiG server ###
```
cd ~
ssh-keygen -t dsa
```


### Certificates - TinyCA-gui ###

I attempted using manual creating as can be inspected in the appendix but using the TinyCA gui is just so much faster... for me at least...

  * Create a CA
  * Create a Host certificate sign with your CA

  * Create certificates for users sign it with your CA

  * Export CA to cacert.pem
  * Export Host certificate to server.pem and server.key
  * Export Client certificate to client.p12

When done I had the following files:

```
~/certs/cacert.pem
~/certs/crl.pem
~/certs/server.crt
~/certs/server.key
```


## Apache ##
```
sudo /etc/init.d/apache2 stop
sudo mv apache2.conf /etc/apache2/
sudo mv httpd.conf   /etc/apache2/
sudo mv ports.conf /etc/apache2/
sudo mv envvars /etc/apache2/
sudo cp mig/install/MiG.conf /etc/apache2/sites-available/MiG
```
Modified "/etc/apache2/sites-available/MiG":
```
ServerName localhost -> ServerName migserver
localhost: -> *:
```
Modified "/etc/apache2/ports.conf":
```
localhost: -> *:
```

Enable required apache modules and start it:
```
sudo a2enmod ssl
sudo a2enmod actions
sudo a2enmod rewrite
sudo a2dissite 000-default
sudo a2ensite MiG
sudo /etc/init.d/apache2 start
```


### Invoking MiG ###
It is convenient to run MiG in screen, the commands below runs the grid\_script and grid\_monitor in screen so you can attach to them later on.
```
cd ~/mig/server && screen -S grid_script -d -m ./grid_script.py
cd ~/mig/server && screen -S grid_monitor -d -m ./grid_monitor.py
```
Attaching is done by running "screen -x grid\_monitor", "screen -x grid\_script". When attached the hotkey combination: "Ctrl-a Ctrl-d", detaches the screen.


## MiG error output ##
When debugging the MiG installation these are the places to look for information:
```
/var/log/apache2            - Apache errors, especially SSL-errors can be determined there.
/home/mig/mig/server/mig.log    - Application error messages
```


# References #
  1. http://code.google.com/p/migrid/source/browse/trunk/mig/install/README.Debian
  1. http://code.google.com/p/migrid/source/browse/trunk/README


### Certificates - Manually ###
```
mkdir ~certs
cd ~certs

openssl genrsa -des3 -out cacert.key 4096
openssl req -new -x509 -days 365 -key cacert.key -out cacert.crt
openssl x509 -in cacert.crt -out cacert.der -outform DER
openssl x509 -in cacert.der -inform DER -out cacert.pem -outform PEM

openssl genrsa -des3 -out server.key 4096
openssl req -new -key server.key -out server.csr
openssl x509 -req -days 365 -in server.csr -CA cacert.crt -CAkey cacert.key -set_serial 01 -out server.crt

openssl rsa -in server.key -out server.key.insecure
mv server.key server.key.secure
mv server.key.insecure server.key

openssl genrsa -des3 -out client.key 4096
openssl req -new -key client.key -out client.csr
openssl x509 -req -days 365 -in client.csr -CA cacert.crt -CAkey cacert.key -set_serial 01 -out client.crt

openssl rsa -in client.key -out client.key.insecure
mv client.key client.key.secure
mv client.key.insecure client.key
```


### Certificates with Script ###
```
cd ~
svn export http://grid-dk.googlecode.com/svn/trunk/tinyCA certs
make init
make hostcert HOST=migserver
make usercert USER="Simon A. F. Lund" FILE="SimonAFLundCert"
ln -s ca-cert.pem cacert.pem
ln -s host.cert server.crt
ln -s host.key server.key
```