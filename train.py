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
import argparse

import ssrgan.models as models
from trainer import Trainer

model_names = sorted(name for name in models.__dict__
                     if name.islower() and not name.startswith("__")
                     and callable(models.__dict__[name]))

parser = argparse.ArgumentParser(description="Research and application of GAN based super resolution "
                                             "technology for pathological microscopic images.")
# basic parameters
parser.add_argument("--dataroot", type=str, default="./data",
                    help="Path to datasets. (default:`./data`)")
parser.add_argument("-j", "--workers", default=4, type=int, metavar="N",
                    help="Number of data loading workers. (default:4)")
parser.add_argument("--manualSeed", type=int, default=1111,
                    help="Seed for initializing training. (default:1111)")
parser.add_argument("--device", default="",
                    help="device id i.e. `0` or `0,1` or `cpu`. (default: ``).")

# log parameters
parser.add_argument("--log_dir", type=str, default="logs",
                    help="Training logs are saved here.")
parser.add_argument("--tensorboard_dir", type=str, default=None,
                    help="Tensorboard is saved here.")
parser.add_argument("--save_freq", type=int, default=5000,
                    help="frequency of evaluating and save the model.")

# model parameters
parser.add_argument("-a", "--arch", metavar="ARCH", default="bionet",
                    choices=model_names,
                    help="model architecture: " +
                         " | ".join(model_names) +
                         " (default: bionet)")
parser.add_argument("--upscale-factor", type=int, default=4, choices=[4],
                    help="Low to high resolution scaling factor. (default:4).")
parser.add_argument("--resume_PSNR", action="store_true",
                    help="Path to latest checkpoint for PSNR model.")
parser.add_argument("--resume", action="store_true",
                    help="Path to latest checkpoint for Generator.")

# training parameters
parser.add_argument("--start-epoch", default=0, type=int, metavar="N",
                    help="manual epoch number (useful on restarts)")
parser.add_argument("--psnr-iters", default=1e6, type=int, metavar="N",
                    help="The number of iterations is needed in the training of PSNR model. (default:1e6)")
parser.add_argument("--iters", default=2e5, type=int, metavar="N",
                    help="The training of srgan model requires the number of iterations. (default:2e5)")
parser.add_argument("-b", "--batch-size", default=8, type=int, metavar="N",
                    help="mini-batch size (default: 8), this is the total "
                         "batch size of all GPUs on the current node when "
                         "using Data Parallel or Distributed Data Parallel.")
parser.add_argument("--psnr-lr", type=float, default=2e-4,
                    help="Learning rate for PSNR model. (default:2e-4)")
parser.add_argument("--lr", type=float, default=1e-4,
                    help="Learning rate. (default:1e-4)")
args = parser.parse_args()
print(args)

if __name__ == "__main__":
    trainer = Trainer(args)
    trainer.run()
    print("All training has been completed!")
