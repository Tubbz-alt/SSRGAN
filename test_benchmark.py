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
from ssrgan.utils import create_folder
from tester import Test

model_names = sorted(name for name in models.__dict__
                     if name.islower() and not name.startswith("__")
                     and callable(models.__dict__[name]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Research and application of GAN based super resolution "
                                                 "technology for pathological microscopic images.")
    # basic parameters
    parser.add_argument("--dataroot", default="./data", type=str,
                        help="Path to datasets. (default:`./data`)")
    parser.add_argument("-j", "--workers", default=4, type=int, metavar="N",
                        help="Number of data loading workers. (default:4)")
    parser.add_argument("--outf", default="test", type=str, metavar="PATH",
                        help="The location of the image in the evaluation process. (default: ``test``).")
    parser.add_argument("--device", default="",
                        help="device id i.e. `0` or `0,1` or `cpu`. (default: ````).")

    # model parameters
    parser.add_argument("-a", "--arch", metavar="ARCH", default="bionet",
                        choices=model_names,
                        help="model architecture: " +
                             " | ".join(model_names) +
                             " (default: bionet)")
    parser.add_argument("--upscale-factor", type=int, default=4, choices=[4],
                        help="Low to high resolution scaling factor. (default:4).")
    parser.add_argument("--model-path", default="", type=str, metavar="PATH",
                        help="Path to latest checkpoint for model. (default: ````).")
    parser.add_argument("--pretrained", dest="pretrained", action="store_true",
                        help="Use pre-trained model.")

    # test parameters
    parser.add_argument("-b", "--batch-size", default=16, type=int, metavar="N",
                        help="mini-batch size (default: 16), this is the total "
                             "batch size of all GPUs on the current node when "
                             "using Data Parallel or Distributed Data Parallel.")
    args = parser.parse_args()
    print(args)

    print("[*]Start evaluating test dataset performance...")
    create_folder(args.outf)  # create evaluation directory.
    test = Test(args)
    test.run()
    print("[*]Test dataset performance evaluation completed!")
