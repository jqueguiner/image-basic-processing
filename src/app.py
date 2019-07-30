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
from glob import glob
import imageio
from distutils.util import strtobool


try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    try:  # Python 3
        from http import client as HTTPStatus
    except ImportError:  # Python 2
        import httplib as HTTPStatus


app = Flask(__name__)

def rotate_image(mat, angle):
    """
    Rotates an image (angle in degrees) and expands image to avoid cropping
    """

    height, width = mat.shape[:2] # image shape has 3 dimensions
    image_center = (width/2, height/2) # getRotationMatrix2D needs coordinates in reverse order (width, height) compared to shape

    rotation_mat = cv2.getRotationMatrix2D(image_center, angle, 1.)

    # rotation calculates the cos and sin, taking absolutes of those.
    abs_cos = abs(rotation_mat[0,0]) 
    abs_sin = abs(rotation_mat[0,1])

    # find the new width and height bounds
    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)

    # subtract old image center (bringing image back to origo) and adding the new image center coordinates
    rotation_mat[0, 2] += bound_w/2 - image_center[0]
    rotation_mat[1, 2] += bound_h/2 - image_center[1]

    # rotate image with the new bounds and translated rotation matrix
    rotated_mat = cv2.warpAffine(mat, rotation_mat, (bound_w, bound_h))
    return rotated_mat

def compress_image(image, path_original):
    size = 1920, 1080
    width = 1920
    height = 1080

    name = os.path.basename(path_original).split('.')
    first_name = os.path.join(os.path.dirname(path_original), name[0] + '.jpg')

    if image.size[0] > width and image.size[1] > height:
        image.thumbnail(size, Image.ANTIALIAS)
        image.save(first_name, quality=85)
    elif image.size[0] > width:
        wpercent = (width/float(image.size[0]))
        height = int((float(image.size[1])*float(wpercent)))
        image = image.resize((width,height), PIL.Image.ANTIALIAS)
        image.save(first_name,quality=85)
    elif image.size[1] > height:
        wpercent = (height/float(image.size[1]))
        width = int((float(image.size[0])*float(wpercent)))
        image = image.resize((width,height), PIL.Image.ANTIALIAS)
        image.save(first_name, quality=85)
    else:
        image.save(first_name, quality=85)


def convertToJPG(path_original):
    img = Image.open(path_original)
    name = os.path.basename(path_original).split('.')
    first_name = os.path.join(os.path.dirname(path_original), name[0] + '.jpg')

    if img.format == "JPEG":
        image = img.convert('RGB')
        compress_image(image, path_original)
        img.close()

    elif img.format == "GIF":
        i = img.convert("RGBA")
        bg = Image.new("RGBA", i.size)
        image = Image.composite(i, bg, i)
        compress_image(image, path_original)
        img.close()

    elif img.format == "PNG":
        try:
            image = Image.new("RGB", img.size, (255,255,255))
            image.paste(img,img)
            compress_image(image, path_original)
        except ValueError:
            image = img.convert('RGB')
            compress_image(image, path_original)
        
        img.close()

    elif img.format == "BMP":
        image = img.convert('RGB')
        compress_image(image, path_original)
        img.close()



@app.route("/rotate", methods=["POST"])
def rotate():

    input_path = generate_random_filename(upload_directory,"jpg")
    output_path = generate_random_filename(upload_directory,"jpg")

    try:
        url = request.json["url"]
        angle = request.json["angle"]
        cropping = request.json["cropping"]
        
        download(url, input_path)

        convertToJPG(input_path)

        if cropping:
            img = Image.open(input_path)
            img = img.rotate(-1*int(angle))
            img.save(output_path)

        else:
            M = imageio.imread(input_path)
            img = rotate_image(M, int(angle))
            imageio.imwrite(output_path, img)

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

        convertToJPG(input_path)

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
