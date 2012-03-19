
scanner.so: scanpng.o
	gcc -shared -lpng scanpng.o -o scanner.so

scanpng.o: scanpng.c
	gcc -c -g -I/usr/include/python2.6 -std=c99 scanpng.c
