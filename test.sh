#!/usr/bin/env sh

printf '*2\r\n$4\r\necHo\r\n$5\r\nhello\r\n' | nc -w 2 127.0.0.1 6379
