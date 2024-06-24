#include <stdio.h>
#include <stdlib.h>

int foo(int);

int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "Please provide one number as argument\n");
    exit(1);
  }
  int x = atoi(argv[1]);
  printf("absolute value of %d is %d\n", x, foo(x));
  return 0;
}
