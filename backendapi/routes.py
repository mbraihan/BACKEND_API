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
        print("Invalid Email")

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
    mac_addr = res['mac_addr']
    cl = db.session.query(Camera).filter_by(mac_addr=mac_addr).first()
    if cl is not None:
        db.session.delete(cl)
        db.session.commit()
    print(cl)

    return jsonify('Camera Removed', status_code)



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



@app.route("/camera-station-add", methods=["POST"])
def stationAdd():
    res         = request.get_json()
    s_name      = res['s_name']
    camera_id   = res ['camera_id']
    if camera_id is not None:
        entry   = CameraStation(s_name, camera_id)
        db.session.add(entry)
        db.session.commit()
        return jsonify({'Camera': camera_id}, {'Code' : status_code})
    else:
        return jsonify({'Message' : 'Please provide a correct mac address'}, {'Code' : error_code})


@app.route("/get-camera-station", methods=['GET'])
def getCameraStation():
    stations = db.session.query(CameraStation).all()
    s_list = []
    for s in stations:
        s_list.append(s.id)
        s_list.append(s.mac_addr)
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
    u = db.session.query(Camera).filter_by(id=id).first().u_name
    p = db.session.query(Camera).filter_by(id=id).first().password
    i = db.session.query(Camera).filter_by(id=id).first().ip_addr
    po = str(db.session.query(Camera).filter_by(id=id).first().port)
    c = str(db.session.query(Camera).filter_by(id=id).first().channel)
    s = str(db.session.query(Camera).filter_by(id=id).first().stream_type)

    rtsp_url = 'rtsp://' + u + ':' + p + '@' + i + ':' + po + '/ch0' + c + '/' + s
    # vs = VideoStream(rtsp_url).start()

    # return Response(gen_frames(vs), mimetype='multipart/x-mixed-replace; boundary=frame')
    # id = str(id)
    return jsonify({'RTSP_URL' : rtsp_url}, status_code)


@app.route("/station-label-add", methods=['POST'])
def stationtLabelAdd():

    if request.method == 'POST':
        res = request.get_json()
        sName = res['sName']
        sId = res ['id']

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

            entry = StationLabel(sName, s_no, photoLocation,
                                 annotationFileName, datasetId)

            db.session.add(entry)
            db.session.commit()

    status_code = 200
    return res, status_code


@app.route("/station-query", methods=['GET'])
def stationQuery():
    res = request.get_json()
    name = res['name']
    query = StationLabel.query.filter_by(sName=name).all()
    print(query)
    im = []
    anno = []
    for q in query:
        im.append(q.photoLocation)
        anno.append(q.annotationFileNname)

    return jsonify({'Image': im}, {'Annotation': anno})


@app.route("/get-dataset", methods=['GET'])
def getDataset():
    dataset = Dataset.query.all()
    d_l = []
    for d in dataset:
        d_l.append(d.name)
    return jsonify({'Dataset': d_l})


@app.route("/remove-dataset", methods=['POST'])
def removeDataset():
    name = request.form['name']
    d = db.session.query(Dataset).filter_by(name=name).first()
    db.session.delete(d)
    db.session.commit()

    status_code = 200
    return jsonify('Dataset removed', 200)



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
    res = request.get_json()
    name = res['name']
    query = DatasetLabel.query.filter_by(dName=name).all()
    print(query)
    im = []
    anno = []
    for q in query:
        im.append(q.photoLocation)
        anno.append(q.annotationFileNname)

    return jsonify({'Image': im}, {'Annotation': anno})



@app.route("/customer-entity-add", methods=['POST'])
def customerEntity():
    face_cascade = cv2.CascadeClassifier(
        '.../cascades/data/haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(
        '.../cascades/data//haarcascade_eye.xml')
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(".../recognizers/face-trainner.yml")

    labels = {"Customer": 1}
    with open(".../pickles/face-labels.pickle", 'rb') as f:
        og_labels = pickle.load(f)
        labels = {v: k for k, v in og_labels.items()}

    font = cv2.FONT_HERSHEY_SIMPLEX

    id = 0
    p = 0
    save_value = 0

    current_id = 0
    label_ids = {}
    y_labels = []
    x_train = []
    a = []

    id = 1
    u = db.session.query(Camera).filter_by(id=id).first().u_name
    p = db.session.query(Camera).filter_by(id=id).first().password
    i = db.session.query(Camera).filter_by(id=id).first().ip_addr
    po = str(db.session.query(Camera).filter_by(id=id).first().port)
    c = str(db.session.query(Camera).filter_by(id=id).first().channel)
    s = str(db.session.query(Camera).filter_by(id=id).first().stream_type)

    camera = 'rtsp://' + u + ':' + p + '@' + i + ':' + po + '/ch0' + c + '/' + s

    capture = VideoStream(camera).start()
    while True:
        if capture.isOpened():
            (status, frame) = capture.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.5,
                minNeighbors=5,
                minSize=(64, 48))
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                id_, conf = recognizer.predict(gray[y:y+h, x:x+w])
                if conf > 0:
                    if conf > 40 and conf <= 85:
                        names = labels[id_]
                        cv2.putText(frame, str(names), (x+5, y-5),
                                    font, 1, (255, 255, 255), 2)
                    else:
                        count = 0
                        img_count = 1
                        while(True):
                            count += 1
                            image = rgb[y:y+h, x:x+w]

                            ce_name = labels
                            img_file = 'customer' + '/' + ce_name + '.png'
                            s3.Object(bucket, img_file).put(Body=image)
                            img_url = f"https://{bucket}.s3.amazonaws.com/{img_file}"
                            photoLocation = img_url

                            entry = CustomerEntity(ce_name, photoLocation)
                            db.session.add(entry)
                            db.session.commit()

                            img_count += 1
    return jsonify("Success")


@app.route("/checkout-area-transaction-alerts", methods=['POST'])
def transactionAlerts():

    id = 1
    u = db.session.query(Camera).filter_by(id=id).first().u_name
    p = db.session.query(Camera).filter_by(id=id).first().password
    i = db.session.query(Camera).filter_by(id=id).first().ip_addr
    po = str(db.session.query(Camera).filter_by(id=id).first().port)
    c = str(db.session.query(Camera).filter_by(id=id).first().channel)
    s = str(db.session.query(Camera).filter_by(id=id).first().stream_type)

    camera = 'rtsp://' + u + ':' + p + '@' + i + ':' + po + '/ch0' + c + '/' + s

    cap = VideoStream(camera).start()
    if cap.isOpened():
        rval, frame = cap.read()
    else:
        rval = False
    while rval:
        rval, frame = cap.read()
        key = cv2.waitKey(20)
        if key == 27:
            break
        else:
            cv2.line(img=frame, pt1=(10, 10), pt2=(100, 10), color=(
                255, 0, 0), thickness=5, lineType=8, shift=0)
            start_time = datetime.now()
            writer = cv2.VideoWriter(cap, cv2.VideoWriter_fourcc(*'DIVX'), 20)
            customerEntityId = 3
            while True:
                ret, frame = cap.read()

                writer.write(frame)
                writer.release()
                end_time = datetime.now()
                vid_file = 'transactions' + '/' + 'customer' + customerEntityId + '.png'
                s3.Object(bucket, vid_file).put(Body=writer)
                img_url = f"https://{bucket}.s3.amazonaws.com/{vid_file}"
                videoLocation = img_url
                entry = Transactions(start_time, end_time,
                                     videoLocation, customerEntityId)
                db.session.add(entry)
                db.session.commit()

    return jsonify("Success")


@app.route("/shoplift-alerts", methods=['POST'])
def shopliftAlerts():

    id = 1
    u = db.session.query(Camera).filter_by(id=id).first().u_name
    p = db.session.query(Camera).filter_by(id=id).first().password
    i = db.session.query(Camera).filter_by(id=id).first().ip_addr
    po = str(db.session.query(Camera).filter_by(id=id).first().port)
    c = str(db.session.query(Camera).filter_by(id=id).first().channel)
    s = str(db.session.query(Camera).filter_by(id=id).first().stream_type)

    camera = 'rtsp://' + u + ':' + p + '@' + i + ':' + po + '/ch0' + c + '/' + s

    cap = VideoStream(camera).start()
    if cap.isOpened():
        rval, frame = cap.read()
    else:
        rval = False
    while rval:
        rval, frame = cap.read()
        key = cv2.waitKey(20)
        if key == 27:
            break
        else:
            cv2.line(img=frame, pt1=(10, 10), pt2=(100, 10), color=(
                255, 0, 0), thickness=5, lineType=8, shift=0)
            start_time = datetime.now()
            writer = cv2.VideoWriter(cap, cv2.VideoWriter_fourcc(*'DIVX'), 20)
            customerEntityId = 3
            while True:
                ret, frame = cap.read()

                writer.write(frame)
                writer.release()
                end_time = datetime.now()
                vid_file = 'shoplift' + '/' + 'customer' + customerEntityId + '.png'
                s3.Object(bucket, vid_file).put(Body=writer)
                img_url = f"https://{bucket}.s3.amazonaws.com/{vid_file}"
                videoLocation = img_url
                entry = ShopLiftingAlerts(
                    start_time, end_time, videoLocation, customerEntityId)
                db.session.add(entry)
                db.session.commit()

    return jsonify("Success")



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