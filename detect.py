# YOLOv5 🚀 by Ultralytics, GPL-3.0 license
"""
Run inference on images, videos, directories, streams, etc.

Usage - sources:
    $ python path/to/detect.py --weights yolov5s.pt --source 0              # webcam
                                                             img.jpg        # image
                                                             vid.mp4        # video
                                                             path/          # directory
                                                             path/*.jpg     # glob
                                                             'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                             'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream

Usage - formats:
    $ python path/to/detect.py --weights yolov5s.pt                 # PyTorch
                                         yolov5s.torchscript        # TorchScript
                                         yolov5s.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                         yolov5s.xml                # OpenVINO
                                         yolov5s.engine             # TensorRT
                                         yolov5s.mlmodel            # CoreML (macOS-only)
                                         yolov5s_saved_model        # TensorFlow SavedModel
                                         yolov5s.pb                 # TensorFlow GraphDef
                                         yolov5s.tflite             # TensorFlow Lite
                                         yolov5s_edgetpu.tflite     # TensorFlow Edge TPU
"""
import cv2
import matplotlib.pyplot as plt
from PIL import Image
import torchvision
from torchvision.models import efficientnet_b2
from torchvision.transforms import transforms
from torchvision.transforms import ToTensor, Lambda
import torch
import torch.nn as nn
import os
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets
import numpy as np

class efficientnet_b2(nn.Module): #Resnet50
    def __init__(self, num_classes):
        super().__init__()
        self.model = torchvision.models.efficientnet_b2(pretrained=True) #50


        self.fc = nn.Linear(1000, num_classes) #1000

    def forward(self, x):
        x = self.model(x)
        return self.fc(x)




import argparse
import os
import sys
from pathlib import Path

import torch
import torch.backends.cudnn as cudnn

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.datasets import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, time_sync

save_dir1=r'E:\KyungHee\K-Fashion'
data_dir = r'C:/Users/toich/yolo/runs/detect/exp/crops'



@torch.no_grad()
def run(
        weights=ROOT / 'yolov5s.pt',  # model.pt path(s)
        source=ROOT / 'data/images',  # file/dir/URL/glob, 0 for webcam
        data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
        imgsz=(640,640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=True,  # show results
        save_txt=True,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=True,  # save cropped prediction boxes
        nosave=False,  # do not save images/videos
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=True,  # visualize features
        update=False,  # update all models
        project=ROOT / 'runs/detect',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=5,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
):
    source = str(source)
    save_img = not nosave and not source.endswith('.txt')  # save inference images
    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
    webcam = source.isnumeric() or source.endswith('.txt') or (is_url and not is_file)
    if is_url and is_file:
        source = check_file(source)  # download

    # Directories
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    #(save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir
    #(save_dir / 'labels').mkdir(parents=True, exist_ok=True)
    #(save_dir / 'images').mkdir(parents=True, exist_ok=True)

    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Dataloader
    if webcam:
        view_img = check_imshow()
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt)
        bs = len(dataset)  # batch_size
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt)
        bs = 1  # batch_size
    vid_path, vid_writer = [None] * bs, [None] * bs

    # Run inference
    model.warmup(imgsz=(1 if pt else bs, 3, *imgsz))  # warmup
    dt, seen = [0.0, 0.0, 0.0], 0
    save_c0 = 0
    save_c2 = 0
    save_c3 = 0
    pic = 0
    for path, im, im0s, vid_cap, s in dataset:
        t1 = time_sync()
        im = torch.from_numpy(im).to(device)
        im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim
        t2 = time_sync()
        dt[0] += t2 - t1

        # Inference
        visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
        pred = model(im, augment=augment, visualize=visualize)
        t3 = time_sync()
        dt[1] += t3 - t2

        # NMS
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
        dt[2] += time_sync() - t3

        # Second-stage classifier (optional)
        # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

        # Process predictions
        for i, det in enumerate(pred):  # per image
            seen += 1
            if webcam:  # batch_size >= 1
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            #save_path = str(save_dir / p.name)  # im.jpg
            #save_path = str(save_dir / 'images' / p.stem) + f'_{frame}' + '.jpg'
            #txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
            s += '%gx%g ' % im.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            imc = im0s[i].copy() #if save_crop else im0  # for save_crop
            annotator = Annotator(im0, line_width=2, example=str(names))
            save_img = False
            
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                # Write results
                for *xyxy, conf, cls in reversed(det):

                    #if save_img or save_crop or view_img:  # Add bbox to image
                    
                    if cls == 0:
                        save_c0 = save_c0 + 1
                    if cls == 2:
                        save_c2 = save_c2 + 1
                    if cls == 3:
                        save_c3 = save_c3 + 1

                    
                    if save_c0 >= 10 or save_c2 >= 10 or save_c3 >= 10:
                        #c = int(cls)  # integer class
                        #label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                        #annotator.box_label(xyxy, label, color=colors(c, True))out
                        #if save_crop:
                        #save_one_box(xyxy, imc, file=save_dir / 'crops' / names[c] / f'{p.stem}.jpg', BGR=True)
                        pic = pic + 1
                        save_one_box(xyxy, imc, file=save_dir / 'crops' / f'{pic}.jpg', BGR=True)
                        save_c0 = 0
                        save_c2 = 0
                        save_c3 = 0
                        
                        model1 = efficientnet_b2(num_classes=4)
                        device1 = torch.device('cpu')
                        
                        model1.load_state_dict(torch.load(f"{save_dir1}/best.pth", map_location=device1))
                        model1.eval()
                        
                        
                        list_j[]=os.listdir(data_dir)
                        #len_j=len(list_j)
                        #if len_j == pic:
                        img1 = Image.open(data_dir + '/' + list_j[pic-1])
                        img1 = transforms.ToTensor()(img1)
                        img1 = transforms.Normalize((0.1307,),(0.3081,))(img1)
                        img1 = transforms.Resize((224,224))(img1) #,Image.BILINEAR
                        img1 = img1.unsqueeze(dim=0)
                        out = model1(img1)
                        label1 = torch.argmax(out, dim=-1)
                        print(pic-1)
                        print(list_j[pic-1])
                        print(label1)
                            
                        #label1 = torch.tensor([4])    
                        #label_a = None
                        #c1 = None
                        #if pic > 0:    
                            
                    label_a = None
                    
                    if pic > 0:
                        
                    
                        if torch.eq(label1, torch.tensor([0])):
                            label_a = 'Water'
                            c1 = 0
                        if torch.eq(label1, torch.tensor([1])):
                            label_a = 'Wool'
                            c1 = 1
                        if torch.eq(label1, torch.tensor([2])):
                            label_a = 'Dry Cleaning'
                            c1 = 2
                        if torch.eq(label1, torch.tensor([3])):
                            label_a = 'etc'
                            c1 = 3
                        
                    
 
                    #c = int(cls)  # integer class
                    #label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                    if label_a != None:
                        annotator.box_label(xyxy, label_a, color=colors(c1, True))
            
                    #if pic > 10:
                    #    cv2.destroyAllWindows()
            
                    #data_dir = save_dir / 'crops' / f'{pic}.jpg'
                    #image_files = []
                    #for file in os.listdir(data_dir):
                    #    image_files.append(os.path.join(data_dir, file))
                    #print(len(image_files))


                    #out_list=[]
                    #file_list=[]
                    #for file in image_files:
                    #    file_list.append(file.split("\\")[-1])
                    #img = Image.open(f"{data_dir}")
                    #img = transforms.ToTensor()(img)
                    #img = transforms.Normalize((0.1307,),(0.3081,))(img)
                    #img = transforms.Resize((200,200))(img) #,Image.BILINEAR
                    #out_list.append(img)
                    #plt.imshow(out_list[0].permute(1,2,0))

                    #output = torch.stack(out_list, dim=0)
                    #print(output.shape)
                    #out = model(img)
                    #label = torch.argmax(out, dim=-1)
                    #print(file_list)
                    #print(label)
                    # output = torc


                    # print(img.shape)

            # Stream results
            im0 = annotator.result()
            if view_img:
                cv2.namedWindow(str(p), cv2.WINDOW_NORMAL)
                cv2.imshow(str(p), im0)
                cv2.waitKey(10)  # 1 millisecond
                
            
            
            
            # Save results (image with detections)
            '''if c0 or c2 or c3:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                else:  # 'video' or 'stream'
                    if vid_path[i] != save_path:  # new video
                        vid_path[i] = save_path
                        if isinstance(vid_writer[i], cv2.VideoWriter):
                            vid_writer[i].release()  # release previous video writer
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream
                            fps, w, h = 30, im0.shape[1], im0.shape[0]
                        #save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
                        #vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    #vid_writer[i].write(im0)
                    cv2.imwrite(save_path, im0)
                    c0 = False
                    c2 = False
                    c3 = False'''
                
                

        # Print time (inference-only)
        LOGGER.info(f'{s}Done. ({t3 - t2:.3f}s)')

    # Print results
    t = tuple(x / seen * 1E3 for x in dt)  # speeds per image
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}{s}")
    if update:
        strip_optimizer(weights)  # update model (to fix SourceChangeWarning)


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolov5s.pt', help='model path(s)')
    parser.add_argument('--source', type=str, default=ROOT / 'data/images', help='file/dir/URL/glob, 0 for webcam')
    parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='show results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--visualize', action='store_true', help='visualize features')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default=ROOT / 'runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=5, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    print_args(vars(opt))
    return opt


def main(opt):
    check_requirements(exclude=('tensorboard', 'thop'))
    run(**vars(opt))


if __name__ == "__main__":
    opt = parse_opt()
    main(opt)
