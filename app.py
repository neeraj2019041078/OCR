from gevent import pywsgi, monkey
monkey.patch_all()
from flask import Flask, request, jsonify
from flask_sockets import Sockets
import json
import cv2
import base64
from flask_cors import CORS
from geventwebsocket.handler import WebSocketHandler
import threading 
import time
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_jwt_extended import JWTManager,create_access_token

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:root@localhost:5432/jsw'
db=SQLAlchemy(app)
sockets = Sockets(app)
CORS(app)
app.config['JWT_SECRET_KEY'] = 'qwertyuiop'
jwt = JWTManager(app)

def get_cam1_rtsp():
    try:
        # print("hello json")
        with open('cameras.json','r') as file:
            cameras=json.load(file)
            cam1_rtsp=cameras.get('Cam1')
            cam2_rtsp=cameras.get('Cam2')
            print(cam1_rtsp)
            print(cam2_rtsp)
            return cam1_rtsp,cam2_rtsp
    except FileNotFoundError:
        return None
    
@app.route('/login',methods=['POST'])
def login():
    data=request.json
    login_details=data.get('login_data',{})
  
    username=login_details.get('userId')
    password=login_details.get('password')

    hardcoded_username='admin'
    hardcoded_password='password123'
    if username == hardcoded_username and password == hardcoded_password:
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token,status=True), 200
    else:
        return jsonify(status=False, error="Invalid username or password"), 401

class SlabTable(db.Model):
    __tablename__ = 'slab_table'
    current_slab = db.Column(db.Integer, primary_key=True, autoincrement=True)
    actual_slab = db.Column(db.Integer, nullable=False)
    result = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    mode = db.Column(db.String(20), default='active')

with app.app_context():
    db.create_all()

@app.route('/tasks')
def get_slab():
    try:
        slabs = SlabTable.query.all()
        slab_list = [{
            'current_slab': slab.current_slab,
            'actual_slab': slab.actual_slab,
            'result': slab.result,
            'timestamp': slab.timestamp.isoformat(), 
            'mode': slab.mode
        } for slab in slabs]
        return jsonify({"slabs": slab_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/tasks', methods=['POST'])
def create_slab():
    try:
        data = request.get_json()
        current_slab = data.get('current_slab')
        actual_slab = data.get('actual_slab')
        result = data.get('result', True)
        timestamp = datetime.utcnow()  
        mode = data.get('mode', 'active')  

        new_slab = SlabTable(current_slab=current_slab, actual_slab=actual_slab, result=result,
                             timestamp=timestamp, mode=mode)
        db.session.add(new_slab)
        db.session.commit()

        return jsonify({"message": "New slab created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

class User(db.Model):
    __tablename__ = 'users'
   
    username = db.Column(db.String(100), primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)  
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(20), default='regular')  

with app.app_context():
    db.create_all()

@app.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        user_list = [{
            'username': user.username,
            'name': user.name,  
            'password': user.password,
            'user_type': user.user_type
        } for user in users]
        return jsonify({"users": user_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        name = data.get('name') 
        user_type = data.get('user_type', 'regular')  

        existing_user=User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        new_user = User(username=username, name=name, password=password, user_type=user_type)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "New user created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

class FrameGenerator:
    def __init__(self, rtsp_url, rtsp_url1):
        self.curr_frame = None
        self.curr_frame1 = None
        self.cap = cv2.VideoCapture(rtsp_url)
        self.cap1 = cv2.VideoCapture(rtsp_url1)
        if not self.cap.isOpened():
            print("Error: Couldn't open the camera.")
            # exit()
        if not self.cap1.isOpened():
            print("Error: Couldn't open camera 2.")
            # exit()

    def generate_frames(self):
        # print("hello 2")
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
               
                self.curr_frame = frame

                time.sleep(0.01)
        except Exception as e:
            print("Error in generate frame:", e)

    def generate_frames1(self):
        # print("hello 3")
        try:
            while True:
                ret, frame = self.cap1.read()
                if not ret:
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
               
                self.curr_frame1 = frame

                time.sleep(0.01)
        except Exception as e:
            print("Error in generate frame:", e)


rtsp_url,rtsp_url1 = get_cam1_rtsp()
frame_generator = FrameGenerator(rtsp_url, rtsp_url1)

@app.route('/add_cam', methods=['POST'])
def add_camera():
    data = request.json
    cam_details = data.get('camDetails', {})
    cam_name = cam_details['cam_name']
    port=cam_details['port']
    password=cam_details['password']
    userId=cam_details['userId']
    ip=cam_details['ip']
    rtsp="rtsp://"+ userId +":"+password + "@"+ip + ":"+port +"/?h264x=4" 
    
    if cam_name:
        try:
            with open('cameras.json', 'r') as file:
                cameras = json.load(file)
        except FileNotFoundError:
            cameras = {}

        cameras[cam_name] = rtsp

        with open('cameras.json', 'w') as file:
            json.dump(cameras, file)
        
        return jsonify({'message': f'Camera details for {cam_name} added successfully', 'status': True}), 200
    else:
        return jsonify({'error': 'Invalid request data'}), 400

@app.route('/add_db', methods=['POST'])
def add_database():
    data = request.json
    db_details = data.get('dbDetails', {})

    if db_details:
        try:
            with open('database.json', 'r') as file:
                database = json.load(file)
        except FileNotFoundError:
            database = {}

        database = db_details

        with open('database.json', 'w') as file:
            json.dump(database, file)
        
        return jsonify({'message': f'PLC added successfully', 'status': True}), 200
    else:
        return jsonify({'error': 'Invalid request data'}), 400

@app.route('/add_plc', methods=['POST'])
def add_plc():
    data = request.json
    plc_details = data.get('plcDetails', {})

    if plc_details:
        try:
            with open('plc.json', 'r') as file:
                plc = json.load(file)
        except FileNotFoundError:
            plc = {}

        plc = plc_details

        with open('plc.json', 'w') as file:
            json.dump(plc, file)
        
        return jsonify({'message': f'PLC added successfully', 'status': True}), 200
    else:
        return jsonify({'error': 'Invalid request data'}), 400

@sockets.route('/video_feed')
def video_feed(ws):
    print("hello1")
    while True:

        frame = frame_generator.curr_frame
        frame1=frame_generator.curr_frame1
        outFrame = cv2.imencode('.jpg', frame)[1].tobytes()
        outFrame1 = cv2.imencode('.jpg', frame1)[1].tobytes()
        image_64_incode = base64.b64encode(outFrame).decode('ascii')
        image_64_incode1= base64.b64encode(outFrame1).decode('ascii')
        result = json.dumps({'image_1': image_64_incode, 'cam_status_1': True , 'image_2': image_64_incode1, 'cam_status_2': True})
        if ws.closed == False:
            ws.send(result)
        time.sleep(0.01)

def server():
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=WebSocketHandler)
    print("Server running...")
    server.serve_forever()

if __name__ == '__main__':
 
    t1 = threading.Thread(target=frame_generator.generate_frames)
    t1.start()
    t3 = threading.Thread(target=frame_generator.generate_frames1)
    t3.start()
    t2 = threading.Thread(target=server)
    t2.start()
    
