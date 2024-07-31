// Copyright 2024 Huawei Cloud Computing Technology Co., Ltd.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <cstring>
#include <iostream>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

void print_buffer(char *start, char *end) {
  ++end;
  while (start != end) {
    std::cout << *start++;
  }
}

bool ends_with(char *end, std::string const &token) {
  auto it = token.rbegin();
  while (it != token.rend()) {
    if (*it++ != *end--) {
      return false;
    }
  }
  return true;
}

int main(int argc, char **argv) {
  int pipefd_a[2]; // pipefd_a[0] reads from pipe
                   // pipefd_a[1] writes to pipe
  int pipefd_b[2];
  if (pipe(pipefd_a) == -1) {
    perror("pipe error");
    exit(EXIT_FAILURE);
  }
  if (pipe(pipefd_b) == -1) {
    perror("pipe error");
    exit(EXIT_FAILURE);
  }

  auto pid = fork();
  if (pid == -1) {
    perror("fork error");
    exit(EXIT_FAILURE);
  }

  if (pid == 0) {
    std::string const s{argv[1]};
    std::string const token = s.substr(s.rfind('/') + 1);
    std::cout << "playing: " << s << std::endl;

    // child reads from pipefd_a[0];
    //       writes to pipefd_b[1];
    dup2(pipefd_b[1], STDOUT_FILENO);
    dup2(pipefd_a[0], STDIN_FILENO);

    close(pipefd_a[1]); // close unused write end
    close(pipefd_b[0]); // close unused read end
    close(pipefd_b[1]);
    close(pipefd_a[0]);
    execl(s.c_str(), token.c_str());

    _exit(0);
  } else {
    // master reads from pipefd_b[0]
    //        writes to pipefd_a[1];
    close(pipefd_a[0]);
    close(pipefd_b[1]);

    bool run = true;
    int a = 1;
    int b = 101;
    int trial = 50;

    char buffer[1024];
    char *p = buffer;
    std::string s;
    while (run) {
      while (read(pipefd_b[0], p, 1)) {
        if (*p == '\n') {
          print_buffer(buffer, p);
          p = buffer;
          continue;
        }
        if (*p == '!') {
          if (ends_with(p, "win!")) {
            run = false;
            print_buffer(buffer, p);
            std::cout << std::endl;
            break;
          }
          if (ends_with(p, "small!")) {
            a = trial;
            trial = (a + b) / 2;
          }
          if (ends_with(p, "big!")) {
            b = trial;
            trial = (a + b) / 2;
          }
          char trial_buf[80];
          int len = sprintf(trial_buf, "%d\n", trial);
          write(pipefd_a[1], trial_buf, len);
        }
        if (!run) {
          break;
        }
        ++p;
      }
    }
    close(pipefd_b[0]);
    close(pipefd_a[1]);
    int status;
    waitpid(0, &status, 0);
  }
}
