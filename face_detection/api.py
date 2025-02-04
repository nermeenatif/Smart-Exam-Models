from flask import Flask
from flask_restful import Api, Resource, reqparse
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'

import numpy as np
from PIL import Image, ImageDraw
import os
import cv2
import base64
from face_detector import FaceDetector

import filecmp

import argparse

app = Flask(__name__)
api = Api(app)  

class Face_Detector():
    def __init__(self):
        self.MODEL_PATH = 'model.pb'
        self.face_detector = FaceDetector(self.MODEL_PATH, gpu_memory_fraction=0.25, visible_device_list='0')
    
    def decode_image(self, image_b64encode):
        # if len(img2) > 11 and img2[0:11] == "data:image/":
		# 		validate_img2 = True

        _, _, image_b64encode = image_b64encode.partition(',')
        im_bytes = base64.b64decode(image_b64encode)
        # im_bytes = base64.decodestring(image_b64encode)

        im_arr = np.frombuffer(im_bytes, dtype=np.uint8)  # im_arr is one-dim Numpy array
        img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # image = Image.fromarray(img)
        # image.show()
        return img

    def encode_image(self, image):
        image = np.array(image)
        _, im_arr = cv2.imencode('.jpg', image)  # im_arr: image in Numpy one-dim array format.
        im_bytes = im_arr.tobytes()
        image_encode = base64.b64encode(im_bytes)
        # image_encode = base64.encodestring(im_bytes)        
        return image_encode

    def draw_boxes_on_image(self, image, boxes, scores):
        image_copy = image.copy()
        draw = ImageDraw.Draw(image_copy, 'RGBA')
        width, height = image.size
        number_of_faces = 0

        for b, s in zip(boxes, scores):
            number_of_faces += 1
            ymin, xmin, ymax, xmax = b
            fill = (255, 0, 0, 45)
            outline = 'red'
            draw.rectangle(
                [(xmin, ymin), (xmax, ymax)],
                fill=fill, outline=outline
            )
            draw.text((xmin, ymin), text='{:.3f}'.format(s))

        return image_copy, number_of_faces

    def detect(self, image_array):
        boxes, scores = self.face_detector(image_array, score_threshold=0.3)
        annotated_image, number_of_faces = self.draw_boxes_on_image(Image.fromarray(image_array), boxes, scores)
        # annotated_image.show()
        return annotated_image, number_of_faces

    def run(self, img_encode):
        img = self.decode_image(img_encode)
        annotated_image, number_of_faces = self.detect(img)
        annotated_image_encoded = ""
        if number_of_faces > 1:
            annotated_image_encoded = self.encode_image(annotated_image)
        return annotated_image_encoded, number_of_faces

########################################################################3

Face_put_args = reqparse.RequestParser()
Face_put_args.add_argument("image_encode", type=str, help="Encode of image is required", required=True)

class Face_Detector_API(Resource):
    def post(self):
        args = Face_put_args.parse_args()
        image_encode = args['image_encode']
        fd = Face_Detector()
        annotated_image_encoded, number_of_faces = fd.run(image_encode)
        if number_of_faces <= 1:
            return {"number_of_faces": number_of_faces}
        else:
            return {"number_of_faces": number_of_faces, "image_encode": annotated_image_encoded.decode("utf-8") }


api.add_resource(Face_Detector_API, "/detect")

if __name__ == "__main__":
    # app.run(debug = False) 
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-p', '--port',
		type=int,
		default=5000,
		help='Port of serving api')
	args = parser.parse_args()
	app.run(host='0.0.0.0', port=args.port)

    # with open("correct_result.txt") as f:
    #     text = f.read()

    # fd = Face_Detector()
    # annotated_image_encoded, number_of_faces = fd.run(text)
    # fd.decode_image(annotated_image_encoded)


    # fd = Face_Detector()
    # di = Detection_Interface()
    # path ="images/3.jpg"


    # img = di.decode_image(text)
    # annotated_image, number_of_faces = fd.run(img)

    # img = di.encode_image(annotated_image)
    # # output = io.BytesIO()
    # with open('encode_ann_result.txt', 'w') as f:
    #     f.write(str(img))

    # img = di.decode_image(img)

    # image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # image = Image.fromarray(image)
    # # image.save("ff.jpg")
    # image.show()

    # f1 = "encode_ann_result.txt"
    # f2 = "correct_ann_result.txt"
    
    # # shallow comparison
    # result = filecmp.cmp(f1, f2)
    # print(result)
    # # deep comparison
    # result = filecmp.cmp(f1, f2, shallow=False)
    # print(result)