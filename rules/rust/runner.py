#!/usr/bin/env python3
# Copyright 2024 Huawei Cloud Computing Technology Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import subprocess
import time

time_start: float = 0
time_stop: float = 0
result: str = "UNKNOWN"
stderr: str = None
stdout: str = None


def end(x):
    return "\n" if x else ""


def dump_results() -> None:
    global time_start, time_stop, result, stdout, stderr
    with open("result", "w") as f:
        print(f"{result}", file=f)
    with open("time-start", "w") as f:
        print(f"{time_start:.3f}", file=f)
    with open("time-stop", "w") as f:
        print(f"{time_stop:.3f}", file=f)
    with open("stdout", "w") as f:
        print(f"{stdout}", file=f, end=end(stdout))
    with open("stderr", "w") as f:
        print(f"{stderr}", file=f, end=end(stderr))


class dumper:
    def __enter__(self):
        global time_start
        time_start = time.time()

    def __exit__(self, type, value, traceback):
        dump_results()


with dumper():
    TEMP_DIR = os.path.realpath("scratch")
    os.makedirs(TEMP_DIR, exist_ok=True)

    WORK_DIR = os.path.realpath("work")
    os.makedirs(WORK_DIR, exist_ok=True)

    ENV = dict(os.environ, TEST_TMPDIR=TEMP_DIR, TMPDIR=TEMP_DIR, TERM="xterm-256color")

    with open("test-launcher.json") as f:
        test_launcher = json.load(f)

    with open("test-args.json") as f:
        test_args = json.load(f)

    ret = subprocess.run(
        test_launcher + ["../test", "--color", "always"] + test_args,
        cwd=WORK_DIR,
        env=ENV,
        capture_output=True,
    )
    time_stop = time.time()
    result = "PASS" if ret.returncode == 0 else "FAIL"
    stdout = ret.stdout.decode("utf-8")
    stderr = ret.stderr.decode("utf-8")

    if result != "PASS":
        exit(1)
