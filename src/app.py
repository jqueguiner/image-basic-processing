import os
import sys
import subprocess
import requests
import ssl
import random
import string
import json

from flask import jsonify
from flask import Flask
from flask import request
from flask import send_file
import traceback

from app_utils import blur
from app_utils import download
from app_utils import generate_random_filename
from app_utils import clean_me
from app_utils import clean_all
from app_utils import create_directory
from app_utils import get_model_bin
from app_utils import get_multi_model_bin

from PIL import Image
import cv2
import numpy as np



try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    try:  # Python 3
        from http import client as HTTPStatus
    except ImportError:  # Python 2
        import httplib as HTTPStatus


app = Flask(__name__)


@app.route("/rotate", methods=["POST"])
def rotate():


    input_path = generate_random_filename(upload_directory,"jpg")
    output_path = generate_random_filename(upload_directory,"jpg")

    try:
        url = request.json["url"]
        angle = request.json['angle']
        
        download(url, input_path)

        img = Image.open(input_path)
        img = img.rotate(-1*int(angle))

        img.save(output_path)

        callback = send_file(output_path, mimetype='image/jpeg')

        return callback, 200

    except:
        traceback.print_exc()
        return {'message': 'input error'}, 400

    finally:
        clean_all([
            input_path,
            output_path
            ])

# flip filename 'vertical' or 'horizontal'
@app.route("/flip", methods=["POST"])
def flip():

    input_path = generate_random_filename(upload_directory,"jpg")
    output_path = generate_random_filename(upload_directory,"jpg")

    try:
        url = request.json["url"]
        mode = request.json["mode"]

        download(url, input_path)

        img = Image.open(input_path)

        if mode == 'horizontal':
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        else:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)

        img.save(output_path)

        callback = send_file(output_path, mimetype='image/jpeg')

        return callback, 200

    except:
        traceback.print_exc()
        return {'message': 'input error'}, 400

    finally:
        clean_all([
            input_path,
            output_path
            ])

# crop filename from (x1,y1) to (x2,y2)
@app.route("/crop", methods=["POST"])
def crop():

    input_path = generate_random_filename(upload_directory,"jpg")
    output_path = generate_random_filename(upload_directory,"jpg")

    try:
        url = request.json["url"]

        x1 = int(request.form['x1'])
        y1 = int(request.form['y1'])
        x2 = int(request.form['x2'])
        y2 = int(request.form['y2'])

        download(url, input_path)

        img = Image.open(input_path)

        # check for valid crop parameters
        width = img.size[0]
        height = img.size[1]

        crop_possible = True
        if not 0 <= x1 < width:
            crop_possible = False
        if not 0 < x2 <= width:
            crop_possible = False
        if not 0 <= y1 < height:
            crop_possible = False
        if not 0 < y2 <= height:
            crop_possible = False
        if not x1 < x2:
            crop_possible = False
        if not y1 < y2:
            crop_possible = False

        # crop image and show
        if crop_possible:
            img = img.crop((x1, y1, x2, y2))

            # save and return image
            img.save(output_path)
        else:
            traceback.print_exc()
            return {'message': 'unable to croput error'}, 400

    except:
        traceback.print_exc()
        return {'message': 'input error'}, 400


    finally:
        clean_all([
            input_path,
            output_path
            ])


if __name__ == '__main__':
    global upload_directory

    upload_directory = '/src/upload/'
    create_directory(upload_directory)

    port = 5000
    host = '0.0.0.0'

    app.run(host=host, port=port, threaded=True)
