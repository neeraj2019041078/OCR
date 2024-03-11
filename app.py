from gevent import pywsgi
from flask import Flask, request, jsonify
from flask_sockets import Sockets
import json
import cv2
import base64
from flask_cors import CORS
from geventwebsocket.handler import WebSocketHandler
from flask_sockets import Sockets
import threading 
import time
import datetime
from flask_socketio import SocketIO,emit
import numpy as np
# from flask_sqlalchemy import SQLAlchemy
# from flask_jwt_extended import JWTManager,create_access_token, jwt_required
import psycopg2


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/jsw'
app.config['JWT_SECRET_KEY'] = 'qwertyuiop' 
# app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'  
# socketio = SocketIO(app, cors_allowed_origins="*")
sockets = Sockets(app)
# db = SQLAlchemy(app)

CORS(app)
# jwt=JWTManager(app)




def get_cam1_rtsp():
    try:
        
        with open('cameras.json','r') as file:
            cameras=json.load(file)
            cam1_rtsp=cameras.get('Cam1')
            cam2_rtsp=cameras.get('Cam2')
            print(cam1_rtsp)
            print(cam2_rtsp)
            return cam1_rtsp,cam2_rtsp
    except FileNotFoundError:
        return None
    

class TextRecognition:
    def __init__(self):
        pass
    
    def recognize_text(self):
        global mode_select_flag
        global slab_waiting_flag
        global slab_id_flag
        slab_id=None

        global global_slab_id


        model = your_ocr_model.load_model("path/to/model")

        while True:
            frame=frame_generator.curr_frame

            if slab_waiting_flag is True:
                slab_id = model.genrate_slab_id(frame)
                if slab_id is not None:
                    global_slab_id=slab_id
                    slab_id_flag=True
                    slab_waiting_flag = False
                    print(f"Slab ID: {slab_id}")
                else:
                    slab_waiting_flag = True
            else:
                continue
            time.sleep(0.01)
              
    def get_mode(self):
        global errorOccur
        global global_slab_id
        global slab_id_flag
        global manual_slab_id
        with open('mode.json', 'r') as file:
            mode_data = json.load(file)

        mode = mode_data.get('mode')

        if mode == 'auto':
            self.recognize_text()
            slab_id_flag = True

            while True:
                if len(global_slab_id)==14:
                    self.sharing_details_l3(global_slab_id, mode)
                    break
                else:
                    errorOccur=True
                    print("change the mode to backend")
                    if len(manual_slab_id) == 14 and mode == 'manual':
                        self.sharing_details_l3(manual_slab_id,mode)
                    else:
                         errorOccur=True
                         print("Check your Slab Id Length it should be of 14 length of characters")
                         time.sleep(0.01)
        else:
            while True:
                if len(manual_slab_id)==14:
                    self.sharing_details_l3(manual_slab_id, mode)
                    break
                else:
                    print("Check your Slab Id Length it should be of 14 characters")
                    time.sleep(0.01) 

    def sharing_details_l3(self, slab_id, mode):
        global receive_data_flag
        global share_data_flag
        global data_stored_flag

        try:
            connection = psycopg2.connect(
                user="your_username",
                password="your_password",
                host="your_host",
                port="your_port",
                database="your_database"
            )

            cursor = connection.cursor()
            query = "SELECT EXISTS(SELECT 1 FROM your_table WHERE actual_slab_id = %s);"
            cursor.execute(query, (slab_id,))
            flag = cursor.fetchone()[0]
            receive_data_flag = True

            if flag:
                share_data_flag = True
                insert_query = "INSERT INTO your_table (slab_id, datetime, username, mode, remarks) VALUES (%s, %s, %s, %s, %s);"
                cursor.execute(insert_query, (slab_id, datetime.datetime.now(), "your_username", mode, flag))
                connection.commit()
                data_stored_flag = True
            else:
                print("Nothing to commit")

            cursor.close()
            connection.close()

        except Exception as error:
            print("Error while fetching data from PostgreSQL:", error)
            return False
        
text_recoginizer=TextRecognition()

# class User(db.Model):
#     __tablename__ = 'users'
   
#     username = db.Column(db.String(100), primary_key=True, nullable=False)
#     name = db.Column(db.String(100), nullable=False)  
#     password = db.Column(db.String(100), nullable=False)
#     user_type = db.Column(db.String(20), default='regular')  

# with app.app_context():
#     db.create_all()



# @app.route('/users', methods=['POST','GET'])
# @jwt_required
# def create_user():
#     try:
#         data = request.json['user_data']
        
#         username = data.get('userId')
#         password = data.get('password')
#         name = data.get('name') 
#         user_type = data.get('user_type')  

#         existing_user=User.query.filter_by(username=username).first()
#         if existing_user:
#             return jsonify({"error": "Username already exists"}), 200

#         new_user = User(username=username, name=name, password=password, user_type=user_type)
#         db.session.add(new_user)
#         db.session.commit()

#         return jsonify({"message": "New user created successfully",'status':True}), 200
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# @app.route('/edit_user', methods=['POST','GET'])
# @jwt_required
# # def edit_user():
#     try:
#         data = request.json['user_data']
        
#         username = data.get('userId')
#         oldpassword = data.get('old_password')
#         newpassword = data.get('new_password') 
#         user_type = data.get('user_type')  

#         existing_user=User.query.filter_by(username=username).first()
#         if existing_user:
#             if existing_user.password==oldpassword:
#                 existing_user.password=newpassword
#                 db.session.commit()
#                 return jsonify({"message": "Password updated successfully", 'status': True}), 200
#             else:
#                 return jsonify({"error": "Old password doesn't match", 'status': False}), 200
            
#         else:
#             return jsonify({"error": "User not found", 'status': False}), 200

    
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

class FrameGenerator:
    def __init__(self, rtsp_url,rtsp_url1):
        self.curr_frame = None
        self.curr_frame1=None
        self.cap = cv2.VideoCapture(rtsp_url)
        self.cap1=cv2.VideoCapture(rtsp_url1)
        self.camera_connected=True
        if not self.cap.isOpened():
            print("Error: Couldn't open the camera.")
            self.camera_connected = False
        else:
            self.camera_connected = True
        
    

    def generate_frames(self):
        try:
            while True:
                if self.camera_connected:
                    
                    ret, frame = self.cap.read()
                    if not ret:
                        print("Error: Couldn't read frame from the camera.")
                        self.camera_connected = False
                        continue
                    
                    else:
                        self.curr_frame = frame          
                else:
                    self.cap.release()
                    self.cap = cv2.VideoCapture(rtsp_url)
                    if self.cap.isOpened():
                        print("Camera reconnected.")
                        self.camera_connected = True
                    else:
                        print('unable to reconnect')
                

        except Exception as e:
            print("Error in generating frame:", e)

        

    def generate_frames1(self):
        try:
            while True:
                if self.camera_connected:
                    ret,frame=self.cap1.read()

                    if not ret:
                        print("Error : Couldnt read frame from the camera")
                        self.camera_connected=False
                        continue
                    else:
                        self.curr_frame1=frame
                       
                        
                else:
                    self.cap1.release()
                    self.cap1=cv2.VideoCapture(rtsp_url1)
                    if self.cap1.isOpened():
                        print("Camera Reconnected")
                        self.camera_connected=True
                    else:
                        print("Error in generating frame:", e)

                        
        except Exception as e:
             print("Error in generating frame:", e)
       
rtsp_url,rtsp_url1=get_cam1_rtsp()
frame_generator = FrameGenerator(rtsp_url,rtsp_url1)


                
# @socketio.on('connect')
# def handle_connect():
#     print('Client connected')
#     res = json.dumps('Hello from the server')
#     socketio.emit('server_message',res)

# def emit_continuous_data():
#     while True:
#         frame = frame_generator.curr_frame
#         frame1 = frame_generator.curr_frame1
        

#         if frame is not None and frame1 is not None:
#             cv2.namedWindow('frame',cv2.WINDOW_NORMAL)
#             cv2.imshow('frame',frame)
#             if cv2.waitKey(1) & 0xFF==ord('q'):
#                 break
#             _, buffer = cv2.imencode('.jpg', frame)
#             _, buffer1 = cv2.imencode('.jpg', frame1)
#             image_64_encode = base64.b64encode(buffer).decode('ascii')
#             image_64_encode1 = base64.b64encode(buffer1).decode('ascii')
#             result = json.dumps({'image_1': image_64_encode, 'cam_status_1': True,
#                                     'image_2': image_64_encode1, 'cam_status_2': True})
#             socketio.emit('server_data', result)
#         time.sleep(0.001)
    
# @sockets.route('/video_feed')
# def video_feed_socket(ws):
#     while True:
#         frame = frame_generator.curr_frame
#         frame1=frame_generator.curr_frame1
#         if frame is not None and frame1 is not None :
#             outFrame = cv2.imencode('.jpg', frame)[1].tobytes()
#             outframe1 = cv2.imencode('.jpg', frame1)[1].tobytes()
#             image_64_encode = base64.b64encode(outFrame).decode('ascii')
#             image_64_encode1 = base64.b64encode(outframe1).decode('ascii')
#             result = json.dumps({'image_1': image_64_encode,'cam_status_1':True,'image_2': image_64_encode1,'cam_status_2':True})
#             if not ws.closed:
#                 ws.send(result)
#         time.sleep(0.01)

# @sockets.route('/process_feed')
# def flags_socket(ws):
#     global slab_waiting_flag
#     global mode_select_flag
#     global slab_id_flag
#     while not ws.closed:
#         flag_data = {
#             'slab_waiting_flag': slab_waiting_flag,
#             'mode_select_flag': mode_select_flag,
#             'slab_id_flag': slab_id_flag,
#             'share_data_flag': share_data_flag,
#             'receive_data_flag': receive_data_flag,
#             'data_stored_flag': data_stored_flag
#         }
#         ws.send(json.dumps(flag_data))
#         time.sleep(1)


# @app.route('/login',methods=['POST'])
# def login():
#     data = request.json
#     login_details = data.get('login_data',{})
  
#     username=login_details.get('userId')
#     password=login_details.get('password')


#     hardcoded_username='admin'
#     hardcoded_password='password123'
#     if username == hardcoded_username and password == hardcoded_password:
#         access_token = create_access_token(identity=username)
#         return jsonify(access_token=access_token,status=True), 200
#     #  return jsonify(status=True), 200
#     else:
#         return jsonify({'status':False,'Message':'Invalid Username or Password'}), 200
# @app.route('/change_mode', methods=['POST'])
# # @jwt_required
# def changemode():
 
#     data = request.json
#     mode_details = data.get('curr_mode', {})

#     if mode_details:
#         try:
#             with open('mode.json', 'r') as file:
#                 mode = json.load(file)
              
#         except FileNotFoundError:
#             mode = {}

#         mode = mode_details

#         with open('mode.json', 'w') as file:
#             json.dump(mode, file)
#         return jsonify({'message': f'mode changed successfully', 'status': True}), 200
#     else:
#         return jsonify({'error': 'Invalid request data'}), 400
    

# @app.route('/add_db', methods=['POST']) 
# # @jwt_required  
# def add_database():
#     data = request.json
#     db_details = data.get('dbDetails', {})

#     if db_details:
#         try:
#             with open('database.json', 'r') as file:
#                 database = json.load(file)
#         except FileNotFoundError:
#             database = {}

#         database = db_details

#         with open('database.json', 'w') as file:
#             json.dump(database, file)
        
#         return jsonify({'message': f'PLC added successfully', 'status': True}), 200
#     else:
#         return jsonify({'error': 'Invalid request data'}), 400
    
# @app.route('/add_cam', methods=['POST'])
# # @jwt_required
# def add_camera():
#     data = request.json
#     cam_details = data.get('camDetails', {})
#     cam_name = cam_details['cam_name']
#     port=cam_details['port']
#     password=cam_details['password']
#     userId=cam_details['userId']
#     ip=cam_details['ip']
#     rtsp="rtsp://"+ userId +":"+password + "@"+ip + ":"+port +"/?h264x=4" 
    
#     if cam_name:
#         try:
#             with open('cameras.json', 'r') as file:
#                 cameras = json.load(file)
#         except FileNotFoundError:
#             cameras = {}

#         cameras[cam_name] = rtsp

#         with open('cameras.json', 'w') as file:
#             json.dump(cameras, file)
        
#         return jsonify({'message': f'Camera details for {cam_name} added successfully', 'status': True}), 200
#     else:
#         return jsonify({'error': 'Invalid request data'}), 400
    
@app.route('/manual_slab_entry',methods=['POST'])
# @jwt_required
def slabid():
     global manual_slab_id
     data = request.json
     slab_id = data.get('slab_id')
     manual_slab_id=slab_id
     return jsonify({'slab_number':manual_slab_id})



if __name__ == '__main__':

    global errorOccur
    global global_slab_id
    global manual_slab_id
    global slab_waiting_flag 
    global mode_select_flag
    global slab_id_flag
    global share_data_flag
    global  receive_data_flag
    global data_stored_flag
    

    errorOccur=False
    global_slab_id=None
    manual_slab_id=None
    slab_waiting_flag =False
    mode_select_flag=False
    slab_id_flag=False
    share_data_flag=False
    receive_data_flag=False
    data_stored_flag=False


    
    t1 = threading.Thread(target=frame_generator.generate_frames)
    t1.start()
    t2 = threading.Thread(target=frame_generator.generate_frames1)
    t2.start()
    thread = threading.Thread(target=text_recoginizer.get_mode)
    thread.start()
    t3=threading.Thread(target=text_recoginizer.recognize_text)
    t3.start()
    # t4=threading.Thread(target=text_recoginizer.recognize_text,args=(frame_generator.curr_frame1,))
    # t4.start()
    server = pywsgi.WSGIServer(('0.0.0.0', 5008), app, handler_class=WebSocketHandler)
    print ("Server running...")
    server.serve_forever()
    # update_flags()

   

  
  
  