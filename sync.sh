#!/bin/sh
rsync -i -e 'ssh' --exclude-from exclude.txt --stats -a mig jaws@amigos18:~ 