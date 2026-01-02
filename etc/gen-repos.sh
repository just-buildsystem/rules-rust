#!/bin/sh
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

set -euo pipefail

readonly ROOT=$(readlink -f $(dirname $0)/..)

: ${RULES_CC_REPO:=https://github.com/just-buildsystem/rules-cc}
: ${RULES_CC_BRANCH:=v1.6.4-alpha+20260102}

just-import-git -C ${ROOT}/etc/repos.template.json \
                --as rules-cc -b ${RULES_CC_BRANCH} ${RULES_CC_REPO} rules \
    | \
    just-import-git -C - \
                    --map test-rules test-rules \
                    --as rules-test -b ${RULES_CC_BRANCH} ${RULES_CC_REPO} tests \
    | ${ROOT}/bin/hdump.py > ${ROOT}/etc/repos.json
