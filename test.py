from flask import Flask, jsonify,json
import cv2
import base64
from flask_cors import CORS
import threading 
import time
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

class FrameGenerator():
    def __init__(self):
        self.frame_1 = None
        self.frame_2 = None
        self.cap_1 = None
        self.cap_2 = None

    def generate_frames_1(self, video_file):
        self.cap_1 = cv2.VideoCapture(video_file)
        while True:
            try:
                ret, frame = self.cap_1.read()
                if not ret:
                    print("Error: Couldn't read frame from the camera.")
                    continue
                else:
                    self.frame_1 = frame

            except Exception as e:
                print("Error in generating frame:", e)
            # cv2.imshow('frame_1', self.frame_1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.cap_1.release()
        cv2.destroyAllWindows()


    def generate_frames_2(self, video_file):
        self.cap_2 = cv2.VideoCapture(video_file)
        while True:
            try:
                ret, frame = self.cap_2.read()
                if not ret:
                    print("Error: Couldn't read frame from the camera.")
                    continue
                else:
                    self.frame_2 = frame

            except Exception as e:
                print("Error in generating frame:", e)
            # cv2.imshow('frame_2', self.frame_2)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.cap_2.release()
        cv2.destroyAllWindows()


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    res = json.dumps('Hello from the server')
    socketio.emit('server_message', res)

def emit_continuous_data():
    while True:
        frame = frame_generator.frame_1
        frame1 = frame_generator.frame_2

        if frame is not None and frame1 is not None:
            # cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
            # cv2.imshow('frame', frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
            _, buffer = cv2.imencode('.jpg', frame)
            _, buffer1 = cv2.imencode('.jpg', frame1)
            image_64_encode = base64.b64encode(buffer).decode('ascii')
            image_64_encode1 = base64.b64encode(buffer1).decode('ascii')
            result = json.dumps({'image_1': image_64_encode, 'cam_status_1': True,
                                    'image_2': image_64_encode1, 'cam_status_2': True})
            socketio.emit('server_data', result)
        time.sleep(0.001)

def get_cam_rtsp():
    try:
        with open('cameras.json', 'r') as file:
            cameras = json.load(file)
            cam1_rtsp = cameras.get('Cam1')
            cam2_rtsp = cameras.get('Cam2')
            return cam1_rtsp, cam2_rtsp
    except FileNotFoundError:
        return None

def run_server():
    socketio.run(app, host='0.0.0.0', port=5001)

if __name__ == '__main__':
    frame_generator = FrameGenerator()
    rtsp_url, rtsp_url1 = get_cam_rtsp()
    print(rtsp_url, ' ', rtsp_url1)
    socket_thread = threading.Thread(target=run_server)
    socket_thread.start()
    
    t1 = threading.Thread(target=frame_generator.generate_frames_1, args=(rtsp_url,))
    t1.start()
    t2 = threading.Thread(target=frame_generator.generate_frames_2, args=(rtsp_url1,))
    t2.start()

    thread = threading.Thread(target=emit_continuous_data)
    thread.start()