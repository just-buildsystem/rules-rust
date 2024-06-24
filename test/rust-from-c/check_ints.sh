set -e

for i in `seq 1 42`; do
    ./main -$i | grep " -$i is $i"
done
