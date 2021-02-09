#!/bin/bash
echo "Starting my app."
cd  /home/ubuntu/flaskProject
source menv/bin/activate
sudo /home/ubuntu/flaskProject/menv/bin/gunicorn --workers=20 --bind 0.0.0.0:443 --certfile=micertificado.pem --keyfile=llaveprivada.pem wsgi:application