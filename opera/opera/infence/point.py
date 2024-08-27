import copy
import cv2
import csv
import glob
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon, Circle
import numpy as np

import mmcv
from mmdet.core.visualization import imshow_det_bboxes, color_val_matplotlib
from opera.apis import init_detector, inference_detector


def distance(x, y):
    return (x[0] - y[0]) * (x[0] - y[0]) + (x[1] - y[1]) * (x[1] - y[1])


def point(model, ori_img, file_name):
    """

    :param model:
    :param ori_img:
    :param file_name:
    :return:
    num, [img, path], [imgwith, path_with], stu
    学生人数，[红点图片，路径]， [照片+红点，路径]，学生抬头(n*3)
    """
    img = ori_img[150:, ...]
    result = inference_detector(model, img)
    score_thr = 0.04
    thr = 0.04
    width, height = img.shape[1], img.shape[0]
    new_img = np.ones((height, width, 3), dtype=np.uint8)
    new_img *= 255
    img = new_img
    img = img.astype(np.uint8)
    img = mmcv.bgr2rgb(img)

    bbox_result, keypoint_result = result
    bboxes = np.vstack(bbox_result)
    keypoints = np.vstack(keypoint_result)
    scores = bboxes[:, -1]
    inds = scores > score_thr
    real_inds = scores > thr
    bboxes = bboxes[inds, :]
    real_keypoints = keypoints[real_inds, ...]
    keypoints = keypoints[inds, ...]

    num = real_keypoints.shape[0]
    if num == 0:
        return None
    num = keypoints.shape[0]
    colors_hp = [(236, 6, 124), (236, 6, 124), (236, 6, 124),
                 (236, 6, 124), (236, 6, 124), (169, 209, 142),
                 (255, 255, 0), (169, 209, 142), (255, 255, 0),
                 (169, 209, 142), (255, 255, 0), (0, 176, 240),
                 (252, 176, 243), (0, 176, 240), (252, 176, 243),
                 (0, 176, 240), (252, 176, 243), (252, 176, 243)]
    colors_hp = [color[::-1] for color in colors_hp]
    colors_hp = [color_val_matplotlib(color) for color in colors_hp]

    img = np.ascontiguousarray(img)
    EPS = 1e-2
    fig = plt.figure('', frameon=False)
    plt.title('')
    canvas = fig.canvas
    dpi = fig.get_dpi()
    # add a small EPS to avoid precision lost due to matplotlib's truncation
    # (https://github.com/matplotlib/matplotlib/issues/15363)
    fig.set_size_inches((width + EPS) / dpi, (height + EPS) / dpi)

    # remove white edges by set subplot margin
    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax = plt.gca()
    ax.axis('off')
    stu = []
    nn = 0
    back = 0
    for i, kpt in enumerate(keypoints):
        # ax.add_patch(
        #     Circle(
        #         xy=(kpt[0, 0], kpt[0, 1]),
        #         radius=5,
        #         color=colors_hp[nn]))
        if (kpt[0, 1] < height * 9 / 11):
            if kpt[0, 1] > min(kpt[5, 1], kpt[6, 1]):
                flag = True
            else:
                flag = False
            stu.append([kpt[0, 0], kpt[0, 1], flag])
            nn += 1
            ax.add_patch(
                Circle(
                    xy=(kpt[0, 0], kpt[0, 1]),
                    radius=5,
                    color=colors_hp[-3]))

    near = {}
    iou_thr = 400
    for i in range(nn):
        near[i] = True

    for i in range(nn):
        if not near[i]:
            continue
        for j in range(i + 1, nn):
            # if distance(stu[i], stu[j]) < 10:
            #     print(distance(stu[i], stu[j]))
            if distance(stu[i], stu[j]) < iou_thr * stu[i][1] / height:
                near[j] = False

    num = 0
    student = []
    for i in range(nn):
        if near[i]:
            num += 1
            student.append(stu[i])
            ax.add_patch(
                Circle(
                    xy=(stu[i][0], stu[i][1]),
                    radius=5,
                    color=colors_hp[0]))
            # 加入纵坐标小于图片高度的0.3 则认为其坐在后面
            if stu[i][1] < height * 0.3:
                back += 1
    if num == 0:
        return None
    if back / num > 0.5:
        pos = '中后'
    else:
        pos = '前中'
    plt.imshow(img)
    stream, _ = canvas.print_to_buffer()
    buffer = np.frombuffer(stream, dtype='uint8')
    img_rgba = buffer.reshape(height, width, 4)
    rgb, alpha = np.split(img_rgba, [3], axis=2)
    img = rgb.astype('uint8')
    img = mmcv.rgb2bgr(img)
    path = '/home/amax/haidongxu/python/static/test/' + str(file_name) + '.png'
    # mmcv.imwrite(img, path)
    plt.imshow(ori_img)
    stream, _ = canvas.print_to_buffer()
    buffer = np.frombuffer(stream, dtype='uint8')
    img_rgba = buffer.reshape(height, width, 4)
    rgb, alpha = np.split(img_rgba, [3], axis=2)
    imgwith = rgb.astype('uint8')
    # imgwith = mmcv.rgb2bgr(imgwith)
    path_with = '/home/amax/python/point/' + str(file_name) + '.png'
    # mmcv.imwrite(imgwith, path_with)
    plt.close()
    return num, [img, path], [imgwith, path_with], student, pos