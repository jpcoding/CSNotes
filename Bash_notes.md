# Bash Notes

!/bin/bash

## I/O

### Test file write speed 
`dd if=/dev/zero of=testfile bs=1024 count=1024000`


## Parallel
youtube-dl --get-id "url" | xargs -I '{}' -P 10 youtube-dl  -o '%(title)s.%(ext)s'  'https://youtube.com/watch?v={}'
