all: scanner scanner.so

scanner: scanpng.c
	gcc -g -DNOPYTHON scanpng.c -I/usr/include/python3.2 -std=c99 -o scanner -lpng

scanner.so: scanpng.o
	gcc -shared scanpng.o -o scanner.so -lpng
	chmod 755 scanner.so

scanpng.o: scanpng.c
	gcc -c -I/usr/include/python3.2 -std=c99 scanpng.c
