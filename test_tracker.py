import os
import json
import math

import cv2
import numpy as np
import matplotlib.pyplot as plt


from conv_reg_config import TestCfg
from simgeo import Rect
import tracker
import display
from sequence import Sequence


def load_seq_infos(seq_size=-1):
    seq_root = TestCfg.SEQUENCE_DIR
    seq_list = []
    for item in os.listdir(seq_root):
        item_path = os.path.join(seq_root, item)
        if os.path.isdir(item_path):
            json_path = os.path.join(item_path, 'cfg.json')
            with open(json_path) as json_fp:
                seq = json.load(json_fp)
                seq = Sequence(**seq)
            seq_list.append(seq)
            if seq_size >= 0 and len(seq_list) >= seq_size:
                break
    print('{:d} sequences loaded!'.format(len(seq_list)))
    return seq_list


def choose_seq(seqs, col=10):

    def name_func(i):
        if (i+1)%col == 0:
            return '{:3d}: {:<12s}\n'.format(i, seqs[i].name)
        else:
            return '{:3d}: {:<12s}'.format(i, seqs[i].name)
    s_list = map(name_func, range(len(seqs)))
    info = ''.join(s_list)
    print(info)
    sid = -1
    while True:
        s = input('Choose a sequence by inputting an integer:')
        try:
            sid = int(s)
        except ValueError:
            sid = -1
        if 0 <= sid < len(seqs):
            break
        else:
            print('Input error, try again.')
    return seqs[sid]


def _test_tracker():
    seqs = load_seq_infos()
    seqs.sort(key=lambda o: o.name)
    show_fid = TestCfg.SHOW_TRACK_RESULT_FID
    trk = tracker.ConvRegTracker()
    seq = seqs[0]
    init = seq.gtRect[0]
    init_rect = Rect(*init)
    img_root = os.path.join(TestCfg.SEQUENCE_DIR, '../', seq.path)
    path = os.path.join(img_root,
                        seq.imgFormat.format(seq.startFrame))
    init_image = cv2.imread(path)
    display.show_track_res(seq.startFrame, init_image, init_rect, init_rect, show_fid)
    trk.init(init_image, init_rect)
    for fid in range(1, len(seq.gtRect)):
        frame_id = fid + seq.startFrame
        path = os.path.join(img_root,
                            seq.imgFormat.format(frame_id))
        image = cv2.imread(path)
        gt_rect = Rect(*seq.gtRect[fid])
        pred_rect = trk.track(image)
        display.show_track_res(frame_id, image, gt_rect, pred_rect, show_fid)


def _test_traindata_provider():
    seqs = load_seq_infos(1)
    seq = seqs[0]
    show_fid = TestCfg.SHOW_TRACK_RESULT_FID
    trk = tracker.ConvRegTracker()
    init = seq.gtRect[0]
    init_rect = Rect(*init)
    img_root = os.path.join(TestCfg.SEQUENCE_DIR, '../', seq.path)
    path = os.path.join(img_root,
                        seq.imgFormat.format(seq.startFrame))
    init_image = cv2.imread(path)
    display.show_track_res(seq.startFrame, init_image, init_rect, init_rect, show_fid)
    trk.init(init_image, init_rect)
    while True:
        frame_id = seq.startFrame
        path = os.path.join(img_root,
                            seq.imgFormat.format(frame_id))
        image = cv2.imread(path)
        gt_rect = Rect(*seq.gtRect[0])
        pred_rect = trk.track(image)
        display.show_track_res(frame_id, image, gt_rect, pred_rect, show_fid)


def _test_init_size():
    seqs = load_seq_infos()
    img = np.zeros((400,400,3), np.uint8)
    ws, hs = 0.0, 0.0
    for seq in seqs:
        w = seq.gtRect[0][2]
        h = seq.gtRect[0][3]
        ws += w
        hs += h
        cv2.circle(img, (w,h), 3, (0,255,0))

    cw = round(ws/len(seqs))
    ch = round(hs/len(seqs))
    cv2.circle(img, (cw,ch), 5, (0,0,255), thickness=2)
    plt.figure()
    plt.imshow(img)
    plt.show()
    plt.waitforbuttonpress()


def _test_statistic_motion():
    seqs = load_seq_infos()
    data_list = []
    img = np.zeros((2001,2001,3), dtype=np.uint8)
    for seq in seqs:
        _tmp = []
        _rect = Rect(*seq.gtRect[0])
        for i in range(1, len(seq.gtRect)):
            _next_rect = Rect(*seq.gtRect[i])
            _size = math.sqrt(_rect.w*_rect.h)
            rel_motion_x = (_next_rect.get_center()[0] - _rect.get_center()[0])/_size
            rel_motion_y = (_next_rect.get_center()[1] - _rect.get_center()[1])/_size
            _tmp.append((rel_motion_x, rel_motion_y))
            _rect = _next_rect
            idx = round(rel_motion_x * 1000) + 1000
            idy = round(rel_motion_y * 1000) + 1000

            if 0 <= idx < 2001 and 0 <= idy < 2001:
                img[idy, idx, 1] = 255
        data_list.extend(_tmp)
    print('Total length: {}'.format(len(data_list)))
    data = np.array(data_list, dtype=np.float)

    import scipy.stats
    rv = scipy.stats.norm.fit(data[:], floc=0.0)
    print(rv)
    cv2.circle(img, (1000,1000), radius=int(round(1000*rv[1])), color=(255,0,0), thickness=3)
    plt.figure()
    plt.imshow(img)
    plt.show()

    print('Variance: {:.4f}'.format(rv[1]))
    plt.waitforbuttonpress()


if __name__ == '__main__':
    _test_tracker()
    # _test_init_size()
    # _test_traindata_provider()
    # _test_statistic_motion()
