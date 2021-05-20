from flask import Flask, render_template, request, flash, jsonify, redirect, url_for
from backendapi.models import Client, License, Camera, CameraStation, Dataset, DatasetLabel, StationLabel
from flask_cors import CORS, cross_origin
from datetime import datetime

import uuid
import sys
import urllib
import helper
import re
from urllib.request import urlopen
import json

import boto3
from boto3.s3.transfer import S3Transfer
from botocore.exceptions import ClientError

from werkzeug.utils import secure_filename
from werkzeug.wrappers import Response

import os
from dotenv import load_dotenv

from backendapi import app
from backendapi import db

import cv2
import imutils
from imutils.video import VideoStream

CORS(app)

key         = os.getenv("S3_ACCESS_KEY")
secret      = os.getenv("S3_SECRET_ACCESS_KEY")
bucket      = os.getenv("S3_BUCKET_NAME")
s3 = boto3.resource('s3', aws_access_key_id=key, aws_secret_access_key=secret)

@app.route("/")
def home():
    return ("Welcome!")


@app.route("/client-add", methods=["POST"])
def clientAdd():
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
    u_name          = request.form['u_name']
    full_name       = request.form['full_name']
    email_address   = request.form['email_address']
    address         = request.form['address']
    city            = request.form['city']
    zipcode         = request.form['zipcode']
    country         = request.form['country']


    if (re.search(regex, email_address)):
        entry = Client(u_name, full_name, email_address, address, city, zipcode, country)
        db.session.add(entry)
        db.session.commit()
    else:
        print("Invalid Email")


    return render_template("index.html")


@app.route("/remove-client", methods = ['POST'])
def removeClient():
    user_name   = request.form['user_name']
    cl = db.session.query(Client).filter_by(user_name = user_name).first()
    db.session.delete(cl)
    db.session.commit()
    print(cl)
    return render_template("index.html")


@app.route("/license-add", methods=['POST'])
def licenseAdd():
    camera_mac      = request.form["camera_mac"]
    start_date      = request.form["start_date"]
    expiry_date     = request.form["expiry_date"]
    client_name     = request.form["client_name"]
    client_id       = db.session.query(Client).filter_by(user_name = client_name).first().id

    entry = License(camera_mac, start_date, expiry_date, client_id)
    db.session.add(entry)
    db.session.commit()

    return render_template("index.html")

@app.route("/camera-add", methods=["POST"])
def cameraAdd():
    u_name          = request.form['u_name']
    password        = request.form['password']
    ip_addr         = request.form['ip_addr']
    port            = request.form['port']
    channel         = request.form['channel']
    stream_type     = request.form['stream_type']
    mac_addr        = request.form['mac_addr']
    serial          = request.form['serial']
    license_id      = db.session.query(License).filter_by(camera_mac = mac_addr).first().id

    expired         = db.session.query(License).filter_by(camera_mac = mac_addr).first().expiry_date
    now             = datetime.today()
    if now > expired:
        print ("renew License")
    else:
        entry = Camera(u_name, password, ip_addr, port, channel, stream_type, mac_addr, serial, license_id)
        db.session.add(entry)
        db.session.commit()

    return render_template("index.html ")

@app.route("/get-camera", methods=['GET'])
def getCamera():
    cams = db.session.query(Camera).all()
    cam_list = []
    for cam in cams:
        cam_list.append(cam.id)
    return jsonify({'Camera' : cam_list})


def gen_frames(vs):
    while True:
        frame = vs.read()
        if frame is None:
            continue
        else:
            frame, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# @app.route("/feed/<int:id>")
@app.route('/rtsp_feed', methods=['GET'])
def gen_url():
    res = request.get_json()
    id = res['id']
    u = db.session.query(Camera).filter_by(id = id).first().u_name
    p = db.session.query(Camera).filter_by(id = id).first().password
    i = db.session.query(Camera).filter_by(id = id).first().ip_addr
    po = str(db.session.query(Camera).filter_by(id = id).first().port)
    c = str(db.session.query(Camera).filter_by(id = id).first().channel)
    s = str(db.session.query(Camera).filter_by(id = id).first().stream_type)

    rtsp_url = 'rtsp://' + u + ':' + p + '@' + i + ':' + po + '/ch0' + c + '/' + s
    vs = VideoStream(rtsp_url).start()

    return Response(gen_frames(vs), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/camera-station-add", methods=["POST"])
def stationAdd():
    s_name        = request.form['s_name']
    s_num         = request.form['s_num']
    camera_id     = db.session.query(Camera).filter_by(serial = s_num).first().id

    entry = CameraStation(s_name, s_num, camera_id)
    db.session.add(entry)
    db.session.commit()

@app.route("/station-label-add", methods=['POST'])
def stationtLabelAdd():

    if request.method == 'POST':
        res = request.get_json()
        sName = res['s_name']
        s_no = res['s_no']
        sId = db.session.query(CameraStation).filter_by(s_num = s_no).first().id

        d = res['data']
        im = []
        label = []
        annot = []
        i = 0
        for d in res['data']:
            im = d['img'].split(",")
            im = im[1]
            label = d['label']
            annot = d['annot'].split("=")
            annot = annot[1].split(">")
            annot = annot[0].split(" ")
            annot = annot[1:5]
            annot = ' '.join(annot)
            annot_file = sName + '/' + sName + '_' + label[i] + '.txt'
            img_file = sName + '/' + sName + '_' + label[i] + '.png'
            s3.Object(bucket, annot_file).put(Body=annot)
            annot_url = f"https://{bucket}.s3.amazonaws.com/{annot_file}"
            s3.Object(bucket, img_file).put(Body=im)
            img_url = f"https://{bucket}.s3.amazonaws.com/{img_file}"
            photoLocation = img_url
            annotationFileName = annot_url

            photoLocation = img_url
            annotationFileName = annot_url
            datasetId = sId

            entry = StationLabel(sName, s_no, photoLocation, annotationFileName, datasetId)

            db.session.add(entry)
            db.session.commit()

    return res


@app.route("/remove-dataset", methods = ['POST'])
def removeDataset():
    name   = request.form['name']
    d = db.session.query(Dataset).filter_by(name = name).first()
    db.session.delete(d)
    db.session.commit()
    return jsonify('success')

@app.route("/get-dataset", methods = ['GET'])
def getDataset():
        dataset = Dataset.query.all()
        d_l = []
        for d in dataset:
            d_l.append(d.name)
        return jsonify({'Dataset' : d_l})

@app.route("/dataset-label-add", methods=['POST'])
def datasetLabelAdd():

    if request.method == 'POST':
        res = request.get_json()
        name = res['name']
        a = bool(Dataset.query.filter_by(name = name).first())
        if a == False:
            entry = Dataset(name)
            db.session.add(entry)
            db.session.commit()
        else:
            print("There exists a dataset of this name")

        ###### AWS SEND, DATABASE SAVE #######
        dName = res['data'][0]['dName']
        print(dName)
        d = res['data']
        im = []
        label = []
        annot = []
        i = 0
        for d in res['data']:
            im = d['img'].split(",")
            im = im[1]
            label = d['label']
            annot = d['annot'].split("=")
            annot = annot[1].split(">")
            annot = annot[0].split(" ")
            annot = annot[1:5]
            annot = ' '.join(annot)

            annot_file = dName + '/' + dName + '_' + label[i] + '.txt'
            img_file = dName + '/' + dName + '_' + label[i] + '.png'
            s3.Object(bucket, annot_file).put(Body=annot)
            annot_url = f"https://{bucket}.s3.amazonaws.com/{annot_file}"
            s3.Object(bucket, img_file).put(Body=im)
            img_url = f"https://{bucket}.s3.amazonaws.com/{img_file}"
            photoLocation = img_url
            annotationFileName = annot_url
            dId = db.session.query(Dataset).filter_by(name = dName).first().id
            datasetId = dId

            entry = DatasetLabel(dName, label, photoLocation, annotationFileName, datasetId)

            db.session.add(entry)
            db.session.commit()



        i = i + 1

    return jsonify("success")


@app.route("/dataset-query", methods = ['GET'])
def datasetQuery():
    res = request.get_json()
    name = res['name']
    query = DatasetLabel.query.filter_by(dName = name).all()
    print(query)
    im = []
    anno = []
    for q in query:
        im.append(q.photoLocation)
        anno.append(q.annotationFileNname)

    return jsonify({'Image' : im}, {'Annotation' : anno})
