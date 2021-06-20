from flask import Flask, render_template, request, flash, jsonify, redirect, url_for
from backendapi.models import Client, License, Camera, CameraStation, Dataset, DatasetLabel, StationLabel, CustomerEntity, Alerts, Transactions, ShopLiftingAlerts
from flask_cors import CORS, cross_origin
from datetime import datetime

import uuid
import sys
import urllib
# import helper
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
s3          = boto3.resource('s3', aws_access_key_id=key, aws_secret_access_key=secret)
status_code = 200
error_code  = 404

@app.route("/")
def home():
    return ("Welcome!")


@app.route("/client-add", methods=["POST"])
def clientAdd():
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
    res                 = request.get_json()
    full_name           = res['full_name']
    u_name              = res['u_name']
    email_address       = res['email_address']
    address             = res['address']
    city                = res['city']
    zipcode             = res['zipcode']
    country             = res['country']


    if (re.search(regex, email_address)):
        entry = Client(u_name, full_name, email_address, address, city, zipcode, country)
        db.session.add(entry)
        db.session.commit()
    else:
        print("Invalid Email")


    return jsonify('Client Added', status_code)


@app.route("/show-client", methods=['GET'])
def showClient():
    clients = Client.query.all()
    c_l = []
    for c in clients:
        c_l.append(c.full_name)
    return jsonify({'Client': c_l})

@app.route("/remove-client", methods=['POST'])
def removeClient():
    res = request.get_json()
    user_name = res['user_name']
    cl = db.session.query(Client).filter_by(user_name=user_name).first()
    if cl is not None:
        db.session.delete(cl)
        db.session.commit()
        return jsonify('Client Removed', status_code)
    else:
        return jsonify("Client Dosen't Exist", error_code)
    print(cl)


@app.route("/license-add", methods=['POST'])
def licenseAdd():
    res             = request.get_json()
    camera_mac      = res['camera_mac']
    start_date      = res['start_date']
    expiry_date     = res['expiry_date']
    client_name     = res['client_name']
    client_id       = db.session.query(Client).filter_by(user_name = client_name).first().id

    entry = License(camera_mac, start_date, expiry_date, client_id)
    db.session.add(entry)
    db.session.commit()

    return jsonify('License Added', status_code)

@app.route("/show-license", methods=['GET'])
def showLicense():
    # user_name   = request.form['user_name']
    licenses = License.query.all()
    l_l = []
    for l in licenses:
        l_l.append(l.camera_mac)
    return jsonify({'License': l_l})

@app.route("/remove-license", methods=['POST'])
def removeLicense():
    res = request.get_json()
    camera_mac = res['camera_mac']
    cl = db.session.query(License).filter_by(camera_mac=camera_mac).first()
    if cl is not None:
        db.session.delete(cl)
        db.session.commit()
        print(cl)
        return jsonify('License Removed', status_code)
    else:
        return jsonify("License Doesn't Exist", error_code)


@app.route("/camera-add", methods=["POST"])
def cameraAdd():
    res             = request.get_json()
    u_name          = res['u_name']
    password        = res['password']
    ip_addr         = res['ip_addr']
    port            = res['port']
    channel         = res['channel']
    stream_type     = res['stream_type']
    mac_addr        = res['mac_addr']
    serial          = res['s_num']
    s_name          = res['s_name']
    license_id      = db.session.query(License).filter_by(camera_mac = mac_addr).first().id

    expired         = db.session.query(License).filter_by(camera_mac = mac_addr).first().expiry_date
    now             = datetime.today()
    if now > expired:
        print ("renew License")
    else:
        entry = Camera(u_name, password, ip_addr, port, channel, stream_type, mac_addr, serial, license_id)
        db.session.add(entry)
        db.session.commit()

    camera_id = db.session.query(Camera).filter_by(serial=serial).first().id
    s_num = serial

    entry = CameraStation(s_name, s_num, camera_id)
    db.session.add(entry)
    db.session.commit()
    return jsonify({'Camera': camera_id}, status_code)

@app.route("/get-camera", methods=['GET'])
def getCamera():
    cams = db.session.query(Camera).all()
    cam_list = []
    for cam in cams:
        cam_list.append(cam.id)
    return jsonify({'Camera' : cam_list})

@app.route("/remove-camera", methods=['POST'])
def removeCamera():
    res = request.get_json()
    mac_addr = res['mac_addr']
    cl = db.session.query(Camera).filter_by(mac_addr=mac_addr).first()
    if cl is not None:
        db.session.delete(cl)
        db.session.commit()
        return jsonify('Camera Removed', status_code)
    else:
        return jsonify("No such camera Exist", error_code)


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


@app.route("/transaction-query", methods = ['GET'])
def datasetQuery():
    res = request.get_json()
    query = Transactions.query.order_by(Transactions.id.desc()).limit(10)
    print(query)
    vid = []
    s_time = []
    e_time = []
    for q in query:
        vid.append(q.videoLocation)
        s_time.append(q.start_time)
        e_time.append(q.end_time)

    return jsonify({'Video' : vid}, {'Start Time' : s_time}, {'End Time' : e_time})


@app.route("/alerts-query", methods = ['GET'])
def datasetQuery():
    res = request.get_json()
    t_id = res['id']
    query = Alerts.query.filter_by(transactionId = t_id).all()
    print(query)
    im = []
    s_time = []
    for q in query:
        im.append(q.photoLocation)
        s_time.append(q.timeStamps)

    return jsonify({'Image' : im}, {'Time Stamps' : s_time})


@app.route("/transaction-query", methods = ['GET'])
def datasetQuery():
    res = request.get_json()
    query = ShopLiftingAlerts.query.order_by(ShopLiftingAlerts.id.desc()).limit(50)
    print(query)
    im = []
    s_time = []
    for q in query:
        im.append(q.photoLocation)
        s_time.append(q.timeStamps)

    return jsonify({'Image' : im}, {'Time Stamps' : s_time})
