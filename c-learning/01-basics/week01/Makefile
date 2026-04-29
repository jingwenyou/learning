CC     = gcc
CFLAGS = -Wall -Wextra -std=c11 -g

TARGETS = hello types

all: $(TARGETS)

hello: hello.c
	$(CC) $(CFLAGS) -o $@ $<

types: types.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(TARGETS)

.PHONY: all clean
