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


key         = os.getenv("S3_ACCESS_KEY")
secret      = os.getenv("S3_SECRET_ACCESS_KEY")
bucket      = os.getenv("S3_BUCKET_NAME")

@app.route("/")
def home():
    return ("Welcome!")


@app.route("/client-add", methods=["POST"])
@cross_origin(supports_credentials=True)
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
@cross_origin(supports_credentials = True)
def removeClient():
    user_name   = request.form['user_name']
    cl = db.session.query(Client).filter_by(user_name = user_name).first()
    db.session.delete(cl)
    db.session.commit()
    print(cl)
    return render_template("index.html")


@app.route("/license-add", methods=['POST'])
@cross_origin(supports_credentials=True)
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
@cross_origin(supports_credentials = True)
def cameraAdd():
    # datet           = '2021-04-09'
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
    # print(expired)
    # expired         = datetime.strptime(expired, "%Y-%m-%d")
    # print(expired)
    now             = datetime.today()
    # print(now)
    if now > expired:
        print ("renew License")
    else:
        entry = Camera(u_name, password, ip_addr, port, channel, stream_type, mac_addr, serial, license_id)
        db.session.add(entry)
        db.session.commit()

    return render_template("index.html ")

@app.route("/camera-station-add", methods=["POST"])
@cross_origin(supports_credentials = True)
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
        sName = request.form["sName"]
        s_no = request.form["s_no"]
        sId = db.session.query(CameraStation).filter_by(s_num = s_no).first().id

        request_data = {}
        # res = request.get_json()
        res = request.form["img"]
        # base64_string = res['img']
        # print(res)
        base64_string = res
        file = 'test/' + sName + '.png'
        s3 = boto3.resource('s3', aws_access_key_id=key, aws_secret_access_key=secret)
        s3.Object(bucket, file).put(Body=base64_string)
        url = f"https://{bucket}.s3.amazonaws.com/{file}"
        print(url)

        photoLocation = url
        annotationFileName = url
        datasetId = sId

        entry = StationLabel(sName, s_no, photoLocation, annotationFileName, datasetId)

        db.session.add(entry)
        db.session.commit()

    return 'success'


@app.route("/dataset-add", methods=['POST'])
@cross_origin(supports_credentials=True)
def datasetAdd():
    name = request.form["name"]

    entry = Dataset(name)

    db.session.add(entry)
    db.session.commit()

    return render_template("index.html")

@app.route("/remove-dataset", methods = ['POST'])
@cross_origin(supports_credentials = True)
def removeDataset():
    name   = request.form['name']
    d = db.session.query(Dataset).filter_by(name = name).first()
    db.session.delete(d)
    db.session.commit()
    return render_template("index.html")

@app.route("/dataset-label-add", methods=['POST'])
def datasetLabelAdd():

    if request.method == 'POST':
        dName = request.form["dName"]
        label = request.form["label"]
        dId = db.session.query(Dataset).filter_by(name = dName).first().id

        request_data = {}
        # res = request.get_json()
        res = request.form["img"]
        # base64_string = res['img']
        # print(res)
        base64_string = res
        file = 'test/' + dName + '.png'
        s3 = boto3.resource('s3', aws_access_key_id=key, aws_secret_access_key=secret)
        s3.Object(bucket, file).put(Body=base64_string)
        url = f"https://{bucket}.s3.amazonaws.com/{file}"
        print(url)

        photoLocation = url
        annotationFileName = url
        datasetId = dId

        entry = DatasetLabel(dName, label, photoLocation, annotationFileName, datasetId)

        db.session.add(entry)
        db.session.commit()

    return 'success'
