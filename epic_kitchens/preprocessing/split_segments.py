#!/usr/bin/env python3
import argparse
import logging
import os
import pathlib
import sys

import pandas as pd

from epic_kitchens.labels import VIDEO_ID_COL
from epic_kitchens.video import FlowModality, RGBModality, split_video_frames

LOG = logging.getLogger(__name__)

DESCRIPTION = '''\
Process frame dumps, and a set of annotations in a pickled dataframe
to produce a set of segmented action videos using symbolic links.

``
Taking a set of videos in the directory format:

    P01_01
    |--- frame_0000000001.jpg
    |--- frame_0000000002.jpg
    |--- ...

Produce a set of action segments in the directory format:

    P01_01_0_chop-wood
    |--- frame_0000000001.jpg
    |--- ...
    |--- frame_0000000735.jpg
    
    
The final number `Z` in `PXX_YY_Z-narration` denotes the index of the segment, this can then 
be used to look up the corresponding information on the segment such as the raw narration, 
verb class, noun classes etc
``
'''


def commonpath(paths):
    return os.path.commonpath(paths)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('annotations_pkl', type=pathlib.Path)
    parser.add_argument('video', type=str)
    parser.add_argument('frame_dir', type=lambda p: pathlib.Path(p).absolute())
    parser.add_argument('links_dir', type=lambda p: pathlib.Path(p).absolute())
    parser.add_argument('--modality', type=str.lower, default='rgb', choices=['rgb', 'flow'])
    parser.add_argument('--frame-format', type=str, default='frame%06d.jpg',
                        help='Only process video folders matching pattern')
    parser.add_argument('--fps', type=float, default=59.94)
    parser.add_argument('--of-stride', type=int, default=2)
    parser.add_argument('--of-dilation', type=int, default=3)
    args = parser.parse_args()
    print(args.frame_dir)
    print(args.links_dir)

    logging.basicConfig(level=logging.INFO)
    if not args.annotations_pkl.exists():
        LOG.error("Annotations pickle: '{}' does not exist".format(args.annotations_pkl))
        sys.exit(1)

    annotations = pd.read_pickle(args.annotations_pkl)
    fps = int(args.fps)
    if args.modality.lower() == 'rgb':
        frame_dirs = [args.frame_dir]
        links_dirs = [args.links_dir]
        modality = RGBModality(fps=fps)
    elif args.modality.lower() == 'flow':
        axes = ['u', 'v']
        frame_dirs = [args.frame_dir.joinpath(axis) for axis in axes]
        links_dirs = [args.links_dir.joinpath(axis) for axis in axes]
        modality = FlowModality(rgb_fps=fps, stride=int(args.of_stride), dilation=int(args.of_dilation))
    else:
        print("Modality '{}' is not recognised".format(args.modality))
        sys.exit(1)

    video_annotations = annotations[annotations[VIDEO_ID_COL] == args.video]
    for frame_dir, links_dir in zip(frame_dirs, links_dirs):
        common_root = commonpath([frame_dir, links_dir])
        print(common_root)
        split_video_frames(modality, args.frame_format, video_annotations, links_dir, frame_dir)