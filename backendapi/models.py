from sqlalchemy.sql import expression
from datetime import datetime
from sqlalchemy import UniqueConstraint, exc
from sqlalchemy.orm import backref
from backendapi import db

from sqlalchemy import inspect

import json
from json import JSONEncoder


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

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }


class License(db.Model):
    __tablename__       = 'license'
    id                  = db.Column(db.Integer, primary_key = True, autoincrement = True)
    camera_mac          = db.Column(db.String(120), unique = True, nullable = False)
    start_date          = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    expiry_date         = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    client_id           = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    camera              = db.relationship('Camera', uselist = False, backref = 'licensee', lazy = True)

    def __init__(self, camera_mac, start_date, expiry_date, client_id):
        self.camera_mac     = camera_mac
        self.start_date     = start_date
        self.expiry_date    = expiry_date
        self.client_id      = client_id

    # def __repr__(self):
    #     return f"License('{self.camera_mac}', '{self.start_date}', '{self.expiry_date}', '{self.client_id}')"

    def toString(self):
        return ({'camera_mac' : self.camera_mac, 'start_date' : self.start_date, 'expiry_date' : self.expiry_date})

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }



class Camera(db.Model):
    __tablename__   = 'camera'
    id              = db.Column(db.Integer, primary_key = True, autoincrement = True)
    u_name          = db.Column(db.String(120), nullable = False)
    password        = db.Column(db.String(120), nullable = False)
    ip_addr         = db.Column(db.String(120), nullable = False)
    port            = db.Column(db.Integer, nullable = False)
    rtsp_url        = db.Column(db.String(200), nullable=False)
    mac_addr        = db.Column(db.String(120), unique = True, nullable = False)
    license_id      = db.Column(db.Integer, db.ForeignKey('license.id'), nullable = False)
    station         = db.relationship('CameraStation', uselist = False, backref = 'station_id', lazy = True)

    def __init__(self, u_name, password, ip_addr, port, rtsp_url, mac_addr, license_id):
        self.u_name         = u_name
        self.password       = password
        self.ip_addr        = ip_addr
        self.port           = port
        self.rtsp_url       = rtsp_url
        self.mac_addr       = mac_addr
        self.license_id     = license_id

    def __repr__(self):
        return f"Camera('{self.u_name}', '{self.password}', '{self.ip_addr}', '{self.port}', '{self.rtsp_url}', '{self.mac_addr}')"

    def toString(self):
        return ({'u_name' : self.u_name, 'password' : self.password, 'ip_addr' : self.ip_addr,
        'port' : self.port, 'rtsp_url' : self.rtsp_url, 'mac_addr' : self.mac_addr})

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }


class CameraStation(db.Model):
    __tablename__   = 'station'

    id              = db.Column(db.Integer, primary_key = True, autoincrement = True)
    s_name          = db.Column(db.String(120), unique = True, nullable = False)
    camera_id       = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable = False)
    stationLabel    = db.relationship('StationLabel', backref='station_label', lazy =  True)

    def __init__(self, s_name, camera_id):
        self.s_name     = s_name
        self.camera_id  = camera_id

    def __repr__(self):
        return f"CameraStation('{self.s_name}')"

    def toString(self):
        return ({'s_name' : self.s_name})

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }


class StationLabel(db.Model):
    __tablename__ = 'stationlabel'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    sName = db.Column(db.String, nullable = False)
    photoLocation = db.Column(db.String, nullable = False, unique = True)
    annotationFileNname = db.Column(db.String, nullable = False)
    stationId = db.Column(db.Integer, db.ForeignKey('station.id'), nullable = False)

    def __init__(self, sName, photoLocation, annotationFileName, stationId):
        # super().__init__()
        self.sName                  = sName
        self.photoLocation          = photoLocation
        self.annotationFileNname    = annotationFileName
        self.stationId              = stationId

    def __repr__(self):
        return f"Dataset('{self.sName}', '{self.photoLocation}', '{self.annotationFileNname}')"


    def toString(self):
        return ({'sName' : self.sName, 'photoLocation' : self.photoLocation,
        'annotationFileNname' : self.annotationFileNname})

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }


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

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }


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
        return f"Dataset('{self.dName}', '{self.label}', '{self.photoLocation}', '{self.annotationFileNname}')"


    def toString(self):
        return ({'dName' : self.dName, 'label' : self.label, 'photoLocation' : self.photoLocation,
        'annotationFileNname' : self.annotationFileNname})

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }


class CustomerEntity(db.Model):
    __tablename__ = 'customerentity'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    ce_name = db.Column(db.String, nullable = False)
    photoLocation = db.Column(db.String, nullable = False, unique = True)
    transactionTable = db.relationship('Transactions', backref='datatset_label', lazy =  True)
    shopliftingalertsTable = db.relationship('ShopLiftingAlerts', backref='datatset_label', lazy =  True)

    def __init__(self, ce_name, photoLocation):
        # super().__init__()
        self.ce_name                = ce_name
        self.photoLocation          = photoLocation

    def __repr__(self):
        return f"CustomerEntity('{self.ce_name}', '{self.photoLocation}')"


    def toString(self):
        return ({'ce_name' : self.ce_name, 'photoLocation' : self.photoLocation})

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }


class Transactions(db.Model):
    __tablename__ = 'transactions'
    id                  = db.Column(db.Integer, primary_key = True, autoincrement = True)
    start_time          = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    end_time            = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    videoLocation       = db.Column(db.String, nullable = False, unique = True)
    customerEntityId    = db.Column(db.Integer, db.ForeignKey('customerentity.id'), nullable = False)
    alertsTable         = db.relationship('Alerts', backref='transaction_label', lazy =  True)


    def __init__(self, start_time, end_time, videoLocation, customerEntityId):
        # super().__init__()
        self.start_time             = start_time
        self.end_time               = end_time
        self.videoLocation          = videoLocation
        self.customerEntityId       = customerEntityId

    def __repr__(self):
        return f"Transactions('{self.start_time}', '{self.end_time}', '{self.videoLocation}'), '{self.customerEntityId}')"


    def toString(self):
        return ({'start_time' : self.start_time, 'end_time' : self.end_time,
        'videoLocation' : self.videoLocation, 'customerEntityId' : self.customerEntityId})

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }


class Alerts(db.Model):
    __tablename__ = 'alerts'
    id                  = db.Column(db.Integer, primary_key = True, autoincrement = True)
    photoLocation       = db.Column(db.String, nullable = False, unique = True)
    timeStamps          = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    transactionId       = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable = False)


    def __init__(self, photoLocation, timeStamps, transactionId):
        # super().__init__()
        self.photoLocation          = photoLocation
        self.timeStamps             = timeStamps
        self.transactionId          = transactionId

    def __repr__(self):
        return f"Alerts('{self.photoLocation}', '{self.timeStamps}')"


    def toString(self):
        return ({'photoLocation' : self.photoLocation,
        'timeStamps' : self.timeStamps})

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }


class ShopLiftingAlerts(db.Model):
    __tablename__ = 'shopliftingalerts'
    id                  = db.Column(db.Integer, primary_key = True, autoincrement = True)
    photoLocation       = db.Column(db.String, nullable = False, unique = True)
    timeStamps          = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    customerEntityId    = db.Column(db.Integer, db.ForeignKey('customerentity.id'), nullable = False)


    def __init__(self, photoLocation, timeStamps, customerEntityId):
        # super().__init__()
        self.photoLocation          = photoLocation
        self.timeStamps             = timeStamps
        self.customerEntityId       = customerEntityId

    def __repr__(self):
        return f"ShopLiftingAlerts('{self.photoLocation}', '{self.timeStamps}')"


    def toString(self):
        return ({'photoLocation' : self.photoLocation,
        'timeStamps' : self.timeStamps})

    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }