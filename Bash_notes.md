# Bash Notes

!/bin/bash

## I/O

### Test file write speed 
`dd if=/dev/zero of=testfile bs=1024 count=1024000`

### stderr and stdout stdin 
0: stdin, 1: stdout, 2:stderr

Redirect stderr to a file `2> file `

Redirect stderr to stdout `2>&1 `



## Parallel
`youtube-dl --get-id "url" | xargs -I '{}' -P 10 youtube-dl  -o '%(title)s.%(ext)s'  'https://youtube.com/watch?v={}'`

`find /home/jp/data/100x500x500/*.f32 | xargs -I {} -P 6 bash ../run.sh '{}' '-3 500 500 100'`

## File Archive 

### Extract files from *.tar
```tar xvf file.tar```

### Extract files from *.tar.gz
```tar xvxf file.tar.gz```

## Text 

`grep "keyword" file | cut -d "deliminator" -f n(nth part to extract)`

## resource monitor

`watch -n.1 "grep \"^[c]pu MHz\" /proc/cpuinfo"`
