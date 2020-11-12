# Copyright 2020 Dakewe Biotech Corporation. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import os

import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
import torchvision.utils as vutils
from PIL import Image
from sewar.full_ref import psnr
from sewar.full_ref import ssim
from tqdm import tqdm

from ssrgan.utils import Logger
from ssrgan.utils import configure
from ssrgan.utils import inference
from ssrgan.utils import process_image


class Estimate(object):
    def __init__(self, args):
        self.args = args

        # Print log.
        self.logger = Logger(args)

    def image_quality_evaluation(self, sr_filename, hr_filename):
        """Image quality evaluation function.

        Args:
            sr_filename (str): Image file name after super resolution.
            hr_filename (str): Original high resolution image file name.
        """
        logger = self.logger

        # Evaluate performance
        sr = cv2.imread(sr_filename)
        hr = cv2.imread(hr_filename)

        psnr_value = psnr(sr, hr)
        ssim_value = ssim(sr, hr)

        logger.print_info("\n")
        logger.print_info("====================== Performance summary ======================")
        logger.print_info(f"PSNR: {psnr_value:.2f}\n"
                          f"SSIM: {ssim_value[0]:.4f}\n")
        logger.print_info("============================== End ==============================")
        logger.print_info("\n")

    def run(self):
        args = self.args

        model, device = configure(args)

        # Read img to tensor.
        lr = process_image(args.lr)
        # Transfer to the specified device for processing.
        lr = lr.to(device)

        sr, use_time = inference(model, lr)
        print(f"Use time: {use_time * 1000:.2f}ms/{use_time:.4f}s.")  # Super resolution image time.

        vutils.save_image(sr, "sr.bmp")  # Save super resolution image.

        self.image_quality_evaluation("sr.bmp", args.hr)


class Video(object):
    def __init__(self, args):

        model, device = configure(args)

        # Image preprocessing operation
        pil2tensor = transforms.ToTensor()
        tensor2pil = transforms.ToPILImage()

        video_capture = cv2.VideoCapture(args.file)
        # Prepare to write the processed image into the video.
        fps = video_capture.get(cv2.CAP_PROP_FPS)
        total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        # Set video size
        size = (int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        sr_size = (size[0] * args.upscale_factor, size[1] * args.upscale_factor)
        pare_size = (sr_size[0] * 2 + 10, sr_size[1] + 10 + sr_size[0] // 5 - 9)
        # Video write loader.
        sr_writer = cv2.VideoWriter(f"sr_{args.scale_factor}x_{os.path.basename(args.file)}",
                                    cv2.VideoWriter_fourcc(*"MPEG"), fps, sr_size)
        compare_writer = cv2.VideoWriter(f"compare_{args.scale_factor}x_{os.path.basename(args.file)}",
                                         cv2.VideoWriter_fourcc(*"MPEG"), fps, pare_size)

        logger = Logger(args)

        self.args = args
        self.device = device
        self.model = model

        # Image processing operations
        self.pil2tensor = pil2tensor
        self.tensor2pil = tensor2pil

        # Video parameters
        self.video_capture = video_capture
        self.fps = fps
        self.total_frames = total_frames
        self.size = size
        self.sr_size = sr_size
        self.pare_size = pare_size
        self.sr_writer = sr_writer
        self.compare_writer = compare_writer

        # Print log.
        self.logger = logger

    def run(self):
        args = self.args
        model = self.model
        device = self.device

        pil2tensor = self.pil2tensor
        tensor2pil = self.tensor2pil
        video_capture = self.video_capture
        total_frames = self.total_frames
        sr_size = self.sr_size
        sr_writer = self.sr_writer
        compare_writer = self.compare_writer

        # Set eval model.
        model.eval()

        # read frame
        success, raw_frame = video_capture.read()
        progress_bar = tqdm(range(total_frames), desc="[processing video and saving/view result videos]")
        for _ in progress_bar:
            if success:
                img = pil2tensor(raw_frame).unsqueeze(0)
                lr = img.to(device)

                with torch.no_grad():
                    sr = model(lr)

                sr = sr.cpu()
                sr = sr.data[0].numpy()
                sr *= 255.0
                sr = (np.uint8(sr)).transpose((1, 2, 0))
                # save sr video
                sr_writer.write(sr)

                # make compared video and crop shot of left top\right top\center\left bottom\right bottom
                sr = tensor2pil(sr)
                # Five areas are selected as the bottom contrast map.
                crop_sr_imgs = transforms.FiveCrop(size=sr.width // 5 - 9)(sr)
                crop_sr_imgs = [np.asarray(transforms.Pad(padding=(10, 5, 0, 0))(img)) for img in crop_sr_imgs]
                sr = transforms.Pad(padding=(5, 0, 0, 5))(sr)
                # Five areas in the contrast map are selected as the bottom contrast map
                compare_img = transforms.Resize((sr_size[1], sr_size[0]), interpolation=Image.BICUBIC)(
                    tensor2pil(raw_frame))
                crop_compare_imgs = transforms.FiveCrop(size=compare_img.width // 5 - 9)(compare_img)
                crop_compare_imgs = [np.asarray(transforms.Pad(padding=(0, 5, 10, 0))(img)) for img in
                                     crop_compare_imgs]
                compare_img = transforms.Pad(padding=(0, 0, 5, 5))(compare_img)
                # concatenate all the pictures to one single picture
                # 1. Mosaic the left and right images of the video.
                top_img = np.concatenate((np.asarray(compare_img), np.asarray(sr)), axis=1)
                # 2. Mosaic the bottom left and bottom right images of the video.
                bottom_img = np.concatenate(crop_compare_imgs + crop_sr_imgs, axis=1)
                bottom_img_height = int(top_img.shape[1] / bottom_img.shape[1] * bottom_img.shape[0])
                bottom_img_width = top_img.shape[1]
                # 3. Adjust to the right size.
                bottom_img = np.asarray(
                    transforms.Resize((bottom_img_height, bottom_img_width))(tensor2pil(bottom_img)))
                # 4. Combine the bottom zone with the upper zone.
                final_image = np.concatenate((top_img, bottom_img))

                # save compare video
                compare_writer.write(final_image)

                if args.view:
                    # display video
                    cv2.imshow("LR video convert HR video ", final_image)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                # next frame
                success, raw_frame = video_capture.read()
