# Intended Audience #
Some MiG sub projects require access to a partial or complete MiG server
environment. Those of you who need access to such a setup can apply for
a developer account on one of the MiG test servers. If granted, you will
be given a normal user account at one or more of the servers with access
to a personal Apache web server.
Please [contact us](ContactUs.md) if you think you need a developer account.

Alternatively you can download and install the MiG source code from the [Downloads section](http://code.google.com/p/migrid/downloads/list). This is not the simplest of tasks yet so this is not
recommended unless you are comfortable with getting your hands into
some linux command line tasks.


# SSH Access #
For security reasons, the MiG servers require ssh logins to use public key encryption instead of passwords only. When your request an account on a development server, please provide a ssh public key.

## Dedicated key ##
If you haven't got a ssh key that you would like to use for this purpose you can simply create a new one:

```
ssh-keygen -b 2048
```

You will be prompted for a passphrase and a location for the generated key file(s). Please use a nontrivial passphrase to avoid spoiling the point of using public key encryption. Obviously it's not a good idea to leave your private key lying around on untrusted computers either.

The public key is the file which is by default saved to ~/.ssh/id\_rsa.pub during the key generation.

We need a public key in OpenSSH format, so if you use another SSH client (e.g. Putty) with another key format, you can use ssh-keygen from the OpenSSH suite to convert it:
```
ssh-keygen -i -f ssh2key.pub > opensshkey.pub
```


## Existing key from MiG user certificate ##
Alternatively you can use your MiG user key as your SSH key. If you unpacked your certificate and key to ~/.mig/ you can generate the corresponding public key with:

```
ssh-keygen -y -f ~/.mig/key.pem > ~/.mig/key.pub
```

Then you can send us the generated public key, ~/.mig/key.pub , and use you MiG key for login (ssh -i ~/.mig/key.pem ...).


# Server specs #
Our developer servers run Debian Stable on AMD64 systems:

  * AMD Athlon(tm) 64 Processor 3000+
  * 1 GB RAM
  * 300 GB disk
  * Gigabit ethernet