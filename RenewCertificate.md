# Renewing You Certificate #
Our certificate policy dictates that user certificates are valid for a year and then expire to automatically stop working.
When your MiG user certificate is just about to expire (which you may notice if you use the certificate countdown widget) or when it already expired you can request certificate renewal.

## Renewing Valid Certificates ##
If your certificate is still valid, renewing is just a matter of using it to auto-fill most of the fields on the
[certificate renewal](https://dk-cert.migrid.org/cgi-bin/reqcert.py) page and submit with either the old or a new password. Then you receive a new certificate to install like mentioned on GettingStarted. In case you chose a new password you also receive a new key along with the certificate. You only need to worry about the key if you use the advanced access methods like the user scripts and source code repositories.

## Renewing Expired Certificates ##
If your certificate already expired or if you lost it, you need to find out the exact certificate field values for the renewal to work. If you don't remember the request field values you can find them by viewing the certificate details in your browser preferences or with openssl. More details can be found in the following sections.

When you know your certificate field values, open up the usual certificate request page as mentioned on GettingStarted and fill in the exact same field details as those on your old certificate. Importantly this includes the password you used.

If you submit a request with different fields it will result in a new account and thus no access to your old jobs, files and permissions.

### Certificate Info in Browser ###
You will likely need to dig into your browser settings or preferences and find certificates under security or advanced settings. Please refer to the documentation for your particular browser.


### Certificate Info from cert.pem File ###
Just look at the output from:
```
openssl x509 -in ~/.mig/cert.pem -noout -subject
```

As an example the line
```
subject= /C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Jonas Bardino/emailAddress=bardino@nbi.ku.dk
```
translates to:
```
Full name: Jonas Bardino
Organisation: NBI
Email address: bardino@nbi.ku.dk
State: 
Two letter country-code: DK
```


### Password Notes ###
Currently we only support changing passwords when renewing still valid certificates, so unless you use that procedure, the password you enter must be identical to the one you used on your last certificate. That is, if you use the same fields but a different password we will have to reject the request.
You can of course still change the password yourself as soon as you receive the new certificate. This is covered in the [MiG user scripts documentation](http://dk.migrid.org/public/doc/user_scripts/MiG-user-scripts.html).

Please refer to the standard procedure in case you [forgot your original password](ForgottenPassword.md).