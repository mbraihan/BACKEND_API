from sqlalchemy.sql import expression
from datetime import datetime
from sqlalchemy import UniqueConstraint, exc
from sqlalchemy.orm import backref
from backendapi import db


class Client(db.Model):
    __tablename__       = 'client'
    id                  = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_name           = db.Column(db.String(120), nullable = False)
    full_name           = db.Column(db.String(120), nullable = False)
    email_address       = db.Column(db.String(120), unique = True, nullable = False)
    address             = db.Column(db.String(120), nullable = False)
    city                = db.Column(db.String(120), nullable = False)
    zipcode             = db.Column(db.Integer, nullable = False)
    country             = db.Column(db.String(120), nullable = False)
    licenses            = db.relationship('License', backref = 'owner', lazy = True)

    def __init__(self, user_name, full_name, email_address, address, city, zipcode, country):
        self.user_name          = user_name
        self.full_name          = full_name
        self.email_address      = email_address
        self.address            = address
        self.city               = city
        self.zipcode            = zipcode
        self.country            = country

    def __repr__(self):
        return f"Client('{self.user_name}', '{self.full_name}', '{self.email_address}', '{self.city}', '{self.zipcode}', '{self.country}')"

    def toString(self):
        return ({'user_name' : self.user_name, 'full_name' : self.full_name,
        'email_address' : self.email_address, 'city' : self.city,
        'zipcode' : self.zipcode, 'country' : self.country})


class License(db.Model):
    __tablename__       = 'license'
    id                  = db.Column(db.Integer, primary_key = True, autoincrement = True)
    camera_mac          = db.Column(db.String(120), nullable = False)
    start_date          = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    expiry_date         = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    client_id           = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    camera              = db.relationship('Camera', backref = 'licensee', lazy = True)

    def __init__(self, camera_mac, start_date, expiry_date, client_id):
        self.camera_mac     = camera_mac
        self.start_date     = start_date
        self.expiry_date    = expiry_date
        self.client_id      = client_id

    def __repr__(self):
        return f"License('{self.camera_mac}', '{self.start_date}', '{self.expiry_date}', '{self.client_id}')"

    def toString(self):
        return ({'camera_mac' : self.camera_mac, 'start_date' : self.start_date, 'expiry_date' : self.expiry_date})


class Camera(db.Model):
    __tablename__   = 'camera'
    id              = db.Column(db.Integer, primary_key = True, autoincrement = True)
    u_name          = db.Column(db.String(120), nullable = False)
    password        = db.Column(db.String(120), nullable = False)
    ip_addr         = db.Column(db.String(120), nullable = False)
    port            = db.Column(db.Integer, nullable = False)
    channel         = db.Column(db.String(120), nullable = False)
    stream_type     = db.Column(db.Integer, nullable = True)
    mac_addr        = db.Column(db.String(120), nullable = False)
    serial          = db.Column(db.Integer, nullable = False)
    license_id      = db.Column(db.Integer, db.ForeignKey('license.id'), nullable = False)
    station         = db.relationship('CameraStation', backref = 'station_id', lazy = True)

    def __init__(self, u_name, password, ip_addr, port, channel, stream_type, mac_addr, serial, license_id):
        self.u_name         = u_name
        self.password       = password
        self.ip_addr        = ip_addr
        self.port           = port
        self.channel        = channel
        self.stream_type    = stream_type
        self.mac_addr       = mac_addr
        self.serial         = serial
        self.license_id     = license_id

    def __repr__(self):
        return f"Camera('{self.u_name}', '{self.password}', '{self.ip_addr}', '{self.port}', '{self.channel}', '{self.stream_type}', '{self.mac_addr}', '{self.serial}')"

    def toString(self):
        return ({'u_name' : self.u_name, 'password' : self.password, 'ip_addr' : self.ip_addr,
        'port' : self.port, 'channel' : self.channel, 'stream_type' : self.stream_type,
        'mac_addr' : self.mac_addr, 'serial' : self.serial})


class CameraStation(db.Model):
    __tablename__   = 'station'

    id              = db.Column(db.Integer, primary_key = True, autoincrement = True)
    s_name          = db.Column(db.String(120), nullable = False)
    s_num           = db.Column(db.Integer, nullable = False)
    camera_id       = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable = False)
    stationLabel    = db.relationship('StationLabel', backref='station_label', lazy =  True)

    def __init__(self, s_name, s_num, camera_id):
        self.s_name     = s_name
        self.s_num      = s_num
        self.camera_id  = camera_id

    def __repr__(self):
        return f"CameraStation('{self.s_name}', '{self.s_num}')"


class StationLabel(db.Model):
    __tablename__ = 'stationlabel'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    sName = db.Column(db.String, nullable = False)
    s_no = db.Column(db.Integer, nullable = False)
    photoLocation = db.Column(db.String, nullable = False, unique = True)
    annotationFileNname = db.Column(db.String, nullable = False)
    stationId = db.Column(db.Integer, db.ForeignKey('station.id'), nullable = False)

    def __init__(self, sName, s_no, photoLocation, annotationFileName, stationId):
        # super().__init__()
        self.sName                  = sName
        self.s_no                   = s_no
        self.photoLocation          = photoLocation
        self.annotationFileNname    = annotationFileName
        self.stationId              = stationId

    def __repr__(self):
        return f"Dataset('{self.sName}', '{self.s_no}' '{self.photoLocation}', '{self.annotationFileNname}')"


    def toString(self):
        return ({'dname' : self.sName, 'label' : self.s_no, 'photoLocation' : self.photoLocation,
        'annotationFileNname' : self.annotationFileNname})


class Dataset(db.Model):
    __tablename__ = 'dataset'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    datasetTable = db.relationship('DatasetLabel', backref='datatset_label', lazy =  True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Dataset('{self.name}')"

    def toString(self):
        return ({'name' : self.name})


class DatasetLabel(db.Model):
    __tablename__ = 'datasetlabel'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    dName = db.Column(db.String, nullable = False)
    label = db.Column(db.String, nullable = False)
    photoLocation = db.Column(db.String, nullable = False, unique = True)
    annotationFileNname = db.Column(db.String, nullable = False)
    datasetId = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable = False)

    def __init__(self, dName, label, photoLocation, annotationFileName, datasetId):
        # super().__init__()
        self.dName                  = dName
        self.label                  = label
        self.photoLocation          = photoLocation
        self.annotationFileNname    = annotationFileName
        self.datasetId              = datasetId

    def __repr__(self):
        return f"Dataset('{self.dName}', '{self.label}' '{self.photoLocation}', '{self.annotationFileNname}')"


    def toString(self):
        return ({'dname' : self.dName, 'label' : self.label, 'photoLocation' : self.photoLocation,
        'annotationFileNname' : self.annotationFileNname})