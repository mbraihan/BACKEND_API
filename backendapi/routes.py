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
from PIL import Image,ImageEnhance
import base64
from io import BytesIO, StringIO
import numpy as np
import io

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
    res = request.get_json()
    full_name           = res['full_name']
    u_name              = res['u_name']
    email_address       = res['email_address']
    address             = res['address']
    city                = res['city']
    zipcode             = res['zipcode']
    country             = res['country']

    if (re.search(regex, email_address)):
        entry = Client(u_name, full_name, email_address,
                       address, city, zipcode, country)
        db.session.add(entry)
        db.session.commit()
    else:
        return jsonify('Invalid Email', error_code)

    status_code = 200
    return jsonify('Client Added', status_code)


@app.route("/show-client", methods=['GET'])
def showClient():
    clients     = Client.query.all()
    c_l         = []
    for c in clients:
        c_l.append(c.full_name._asdict())
    return jsonify({'Client': c_l})



@app.route("/remove-client", methods=['POST'])
def removeClient():
    res         = request.get_json()
    user_name   = res['user_name']
    cl          = db.session.query(Client).filter_by(user_name=user_name).first()
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
    if client_id is not None:
        entry = License(camera_mac, start_date, expiry_date, client_id)
        db.session.add(entry)
        db.session.commit()
        return jsonify('License Added', status_code)
    else:
        return jsonify('Invalid client name', error_code)



@app.route("/show-license", methods=['GET'])
def showLicense():
    licenses = License.query.all()
    l_l = []
    for l in licenses:
        l_l.append(l.camera_mac)
        # l_l.append(l.toDict())
    return jsonify({'License': l_l})



@app.route("/remove-license", methods=['POST'])
def removeLicense():
    res = request.get_json()
    error_code = 404
    camera_mac = res['camera_mac']
    camer_mac = str(camera_mac)
    cl = db.session.query(License).filter_by(camera_mac=camera_mac).first()
    if cl is not None:
        db.session.delete(cl)
        # db.session.query(License).filter_by(camera_mac=camera_mac).delete()
        db.session.commit()
        print(cl)
        status_code = 200
        return jsonify('License Removed', status_code)
    else:
        return jsonify("License Doesn't Exist", error_code)



@app.route("/camera-add", methods=["POST"])
def cameraAdd():
    res         = request.get_json()
    u_name      = res['u_name']
    password    = res['password']
    ip_addr     = res['ip_addr']
    port        = res['port']
    rtsp_url    = res['rtsp_url']
    mac_addr    = res['mac_addr']
    duplicate   = bool(Camera.query.filter_by(mac_addr=mac_addr).first())
    if duplicate:
        return jsonify ({'Message':'A camera is already registered with this mac address'}, {'Code' : error_code})
    else:

        license_id  = db.session.query(License).filter_by(
        camera_mac=mac_addr).first().id

        expired = db.session.query(License).filter_by(
        camera_mac=mac_addr).first().expiry_date
        now = datetime.today()
        # error_code = 404
        if now > expired:
            print("renew License")
            return jsonify({'Message' : 'Please renew License'}, {'Code' : error_code})
        else:
            entry = Camera(u_name, password, ip_addr, port,
                       rtsp_url, mac_addr, license_id)
            db.session.add(entry)
            db.session.commit()

            return jsonify({'Code' : status_code})



@app.route("/camera-info", methods=['GET'])
def getCameraInfo():
    cams    = Camera.query.all()
    cam_list= []
    for cam in cams:
        cam_list.append(cam.toDict())
    return jsonify({'Camera': cam_list})



@app.route("/remove-camera", methods=['POST'])
def removeCamera():
    res = request.get_json()
    mac_addr = str(res['mac_addr'])
    cl = db.session.query(Camera).filter_by(mac_addr=mac_addr).first()
    if cl is not None:
        db.session.delete(cl)
        db.session.commit()
    print(cl)

    return jsonify('Camera Removed', status_code)




@app.route("/camera-station-add", methods=["POST"])
def stationAdd():
    res         = request.get_json()
    s_name      = res['s_name']
    camera_id   = res ['camera_id']
    duplicate   = bool(CameraStation.query.filter_by(camera_id=camera_id).first())
    if duplicate:
        return jsonify ({'Message':'This camera is already registered with a station'}, {'Code' : error_code})
    else:
        if camera_id is not None:
            entry   = CameraStation(s_name, camera_id)
            db.session.add(entry)
            db.session.commit()
            s_id = CameraStation.query.filter_by(s_name = s_name).first().id
            print(s_id)
            return jsonify({'station_id': s_id}, {'Code' : status_code})
        else:
            return jsonify({'Message' : 'Please provide a correct mac address'}, {'Code' : error_code})



@app.route("/get-camera-station", methods=['GET'])
def getCameraStation():
    stations = db.session.query(CameraStation).all()
    s_list = []
    for s in stations:
        s_list.append(s.toDict())
    return jsonify({'Camera_Station': s_list})



@app.route("/remove-camera-station", methods=['POST'])
def removeCameraStation():
    res = request.get_json()
    id = res['id']
    s = db.session.query(CameraStation).filter_by(id=id).first()
    if s is not None:
        db.session.delete(s)
        db.session.commit()
    print(s)

    return jsonify('Camera Removed', status_code)


@app.route('/rtsp_feed', methods=['POST'])
def gen_url():
    res = request.get_json()
    id = res['id']

    rtsp_url = db.session.query(Camera).filter_by(id=id).first().rtsp_url

    return jsonify({'RTSP_URL' : rtsp_url}, status_code)


@app.route("/station-label-add", methods=['POST'])
def stationtLabelAdd():

    if request.method == 'POST':
        res = request.get_json()
        sId = res ['id']
        sName = CameraStation.query.filter_by(id = sId).first().s_name
        # d = res['data']
        im = []
        label = []
        annot = []
        i = 0
        for d in res['annotationData']:
            im = d['img'].split(",")
            im = im[1]
            im = Image.open(BytesIO(base64.b64decode(im)))
            image = cv2.cvtColor(np.array(im), cv2.COLOR_BGR2RGB)

            img = Image.fromarray(image).convert('RGB')
            out_img = BytesIO()
            img.save(out_img, format='png')
            out_img.seek(0)

            label = d['label']
            print(label)


            annot = d['annot'].split("=")
            annot = annot[1].split(">")
            annot = annot[0].split(" ")
            annot = annot[1:5]
            # annot = d['annot']
            annot = ' '.join(annot)
            # print(annot)

            annot_file = 'Station' + '/' + sName + '_' + label[i] + '.txt'
            img_file = 'Station' + '/' + sName + '_' + label[i] + '.png'


            s3.Object(bucket, annot_file).put(Body=annot)
            annot_url = f"https://{bucket}.s3.amazonaws.com/{annot_file}"


            s3.Bucket(bucket).put_object(Key = img_file, Body = out_img, ContentType = 'image/PNG')
            img_url = f"https://{bucket}.s3.amazonaws.com/{img_file}"


            photoLocation = img_url
            annotationFileName = annot_url

            photoLocation = img_url
            annotationFileName = annot_url
            stationId = sId

            entry = StationLabel(sName, photoLocation,
                                 annotationFileName, stationId)

            db.session.add(entry)
            db.session.commit()
            print(i)
        i = i + 1
    status_code = 200
    print(i)
    return res, status_code


@app.route("/remove-station-dataset", methods=['POST'])
def removeSDataset():
    res = request.get_json()
    sName = res['name']
    d = db.session.query(StationLabel).filter_by(sName=sName).first()
    db.session.delete(d)
    db.session.commit()

    status_code = 200
    return jsonify('Dataset removed', status_code)


@app.route("/station-query", methods=['GET'])
def stationQuery():
    query = StationLabel.query.all()
    print(query)
    data_label = []
    for q in query:
        data_label.append(q.toDict())

    return jsonify({'Station_info': data_label})


@app.route("/get-dataset", methods=['GET'])
def getDataset():
    dataset = Dataset.query.all()
    d_l = []
    for d in dataset:
        d_l.append(d.name)
    return jsonify({'Dataset': d_l})


@app.route("/get-data", methods=['GET'])
def getData():
    data = Dataset.query.all()
    r_data = []
    for d in data:
        f_data = {}
        dd = DatasetLabel.query.filter_by(datasetId = d.id)
        f_data["name"] = d.name
        f_data["id"] = d.id
        all_image = []
        for img in dd:
            image = {}
            image["id"] = img.id
            image["label"] = img.label
            image["image"] = img.photoLocation
            all_image.append(image)
        f_data["iamges"] = all_image
        r_data.append(f_data)
    return jsonify(r_data)


@app.route("/get-data/<int:dataset_id>", methods=['GET'])
def getSData(dataset_id):
    data = Dataset.query.filter_by(id=dataset_id)
    r_data = []
    for d in data:
        f_data = {}
        dd = DatasetLabel.query.filter_by(datasetId = d.id)
        f_data["name"] = d.name
        f_data["id"] = d.id
        all_image = []
        for img in dd:
            image = {}
            image["id"] = img.id
            image["label"] = img.label
            image["image"] = img.photoLocation
            all_image.append(image)
        f_data["iamges"] = all_image
        r_data.append(f_data)
    return jsonify(r_data)


@app.route("/remove-data", methods = ['POST'])
def removeData():
    res = request.get_json()
    rem = res['id']
    for r in rem:
        # print(r['id'])
        id = r['id']
        d = db.session.query(DatasetLabel).filter_by(id=id).first()
        db.session.delete(d)
        db.session.commit()
    return jsonify('Images removed', status_code)


@app.route("/remove-dataset", methods=['POST'])
def removeDataset():
    res = request.get_json()
    name = res['name']
    d = db.session.query(Dataset).filter_by(name=name).first()
    db.session.delete(d)
    db.session.commit()

    status_code = 200
    return jsonify('Dataset removed', status_code)



@app.route("/dataset-label-add", methods=['POST'])
def datasetLabelAdd():

    if request.method == 'POST':
        res = request.get_json()
        name = res['name']
        a = bool(Dataset.query.filter_by(name=name).first())
        if a == False:
            entry = Dataset(name)
            db.session.add(entry)
            db.session.commit()
        else:
            print("There exists a dataset of this name")
            return jsonify('Please use update api to update', error_code)

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
            im = Image.open(BytesIO(base64.b64decode(im)))
            image = cv2.cvtColor(np.array(im), cv2.COLOR_BGR2RGB)

            img = Image.fromarray(image).convert('RGB')
            out_img = BytesIO()
            img.save(out_img, format='png')
            out_img.seek(0)



            label = d['label']
            print(label)


            annot = d['annot'].split("=")
            annot = annot[1].split(">")
            annot = annot[0].split(" ")
            annot = annot[1:5]
            annot = ' '.join(annot)
            print(annot)

            annot_file = 'Dataset' + '/' + dName + '_' + label + '.txt'
            img_file = 'Dataset' + '/' + dName + '_' + label + '.png'


            s3.Object(bucket, annot_file).put(Body=annot)
            annot_url = f"https://{bucket}.s3.amazonaws.com/{annot_file}"


            s3.Bucket(bucket).put_object(Key = img_file, Body = out_img, ContentType = 'image/PNG')
            img_url = f"https://{bucket}.s3.amazonaws.com/{img_file}"


            photoLocation = img_url
            annotationFileName = annot_url
            dId = db.session.query(Dataset).filter_by(name=dName).first().id
            datasetId = dId

            entry = DatasetLabel(dName, label, photoLocation,
                                 annotationFileName, datasetId)

            db.session.add(entry)
            db.session.commit()
            print(i)

        i = i + 1
        print('I22 = ', i)
    status_code = 200
    # print(i)
    return res, status_code


@app.route("/dataset-label-update", methods=['POST'])
def datasetLabelUpdate():

    if request.method == 'POST':
        res = request.get_json()
        name = res['name']
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
            im = Image.open(BytesIO(base64.b64decode(im)))
            image = cv2.cvtColor(np.array(im), cv2.COLOR_BGR2RGB)

            img = Image.fromarray(image).convert('RGB')
            out_img = BytesIO()
            img.save(out_img, format='png')
            out_img.seek(0)


            label = d['label']


            annot = d['annot'].split("=")
            annot = annot[1].split(">")
            annot = annot[0].split(" ")
            annot = annot[1:5]
            annot = ' '.join(annot)

            annot_file = 'Dataset' + '/' + dName + '_' + label + '.txt'
            img_file = 'Dataset' + '/' + dName + '_' + label + '.png'

            s3.Object(bucket, annot_file).put(Body=annot)
            annot_url = f"https://{bucket}.s3.amazonaws.com/{annot_file}"

            s3.Bucket(bucket).put_object(Key = img_file, Body = out_img, ContentType = 'image/PNG')
            img_url = f"https://{bucket}.s3.amazonaws.com/{img_file}"

            photoLocation = img_url
            annotationFileName = annot_url
            dId = db.session.query(Dataset).filter_by(name=dName).first().id
            datasetId = dId

            entry = DatasetLabel(dName, label, photoLocation,
                                 annotationFileName, datasetId)

            db.session.add(entry)
            db.session.commit()

        i = i + 1
    status_code = 200
    return res, status_code


@app.route("/dataset-query", methods=['GET'])
def datasetQuery():
    query = DatasetLabel.query.all()
    print(query)
    data_label = []
    for q in query:
        data_label.append(q.toDict())

    return jsonify({'Dataset_info': data_label})



@app.route("/transaction-query", methods=['GET'])
def transactionQuery():
    query = Transactions.query.order_by(Transactions.id.desc()).limit(10)
    # print(query)
    t_q = []
    for q in query:
        t_q.append(q.toDict())
    return jsonify({'Transactions': t_q})



@app.route("/alerts-query", methods=['GET'])
def alertsQuery():
    query = Alerts.query.all()
    print(query)
    a_q = []
    for q in query:
        a_q.append(q.toDict())
    return jsonify({'Alerts': a_q})



@app.route("/alert-query", methods=['POST'])
def alertQuery():
    res     = request.get_json()
    t_id    = res ['t_id']
    query   = Alerts.query.filter_by(transactionId = t_id)
    checker = bool(Transactions.query.filter_by(id = t_id).first())
    if checker:
        # print(query)
        a_q = []
        for q in query:
            a_q.append(q.toDict())
        return jsonify({'Alerts': a_q})
    else:
        return jsonify('Invalid Transaction ID', error_code)


@app.route("/shoplift-query", methods=['GET'])
def shopLiftQuery():
    res = request.get_json()
    query = ShopLiftingAlerts.query.order_by(
        ShopLiftingAlerts.id.desc()).limit(50)
    print(query)
    im = []
    s_time = []
    for q in query:
        im.append(q.photoLocation)
        s_time.append(q.timeStamps)

    return jsonify({'Image': im}, {'Time Stamps': s_time})