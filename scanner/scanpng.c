#include "png.h"
#include "stdio.h"
#include "stdlib.h"
#include "Python.h"

#define ERROR_OPENFILE -1
#define ERROR_CREATESTRUCT -2
#define ERROR_CREATEINFO -3
#define ERROR_PNGLONGJUMP -4
#define ERROR_FORMAT -5
#define ERROR_MALLOC -6


char *translate_color_type(int color_type) {
   switch(color_type) {
   case PNG_COLOR_TYPE_GRAY:
     return "grayscale";
   case PNG_COLOR_TYPE_RGB:
     return "rgb";
   case PNG_COLOR_TYPE_PALETTE:
     return "palletted";
   }
   return "other color type";
}

int read_png(char *file_name, png_bytep **p_row_pointers, png_uint_32 *p_height, png_uint_32 *p_width)
{
   png_structp png_ptr;
   png_infop info_ptr;
   int bit_depth, color_type;
   FILE *fp;

   if ((fp = fopen(file_name, "rb")) == NULL)
      return (ERROR_OPENFILE);
   png_ptr = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
   if (png_ptr == NULL)
   {
      fclose(fp);
      return (ERROR_CREATESTRUCT);
   }
   info_ptr = png_create_info_struct(png_ptr);
   if (info_ptr == NULL)
   {
      fclose(fp);
      png_destroy_read_struct(&png_ptr, png_infopp_NULL, png_infopp_NULL);
      return (ERROR_CREATEINFO);
   }
   /* Set up libpng standard error handling */
   if (setjmp(png_jmpbuf(png_ptr)))
   {
      /* If we get here, we had a problem reading the file */
      /* Free all of the memory associated with the png_ptr and info_ptr */
      png_destroy_read_struct(&png_ptr, &info_ptr, png_infopp_NULL);
      fclose(fp);
      return (ERROR_PNGLONGJUMP);
   }
   /* Set up io */
   png_init_io(png_ptr, fp);
   /* Read the file information */
   png_read_info(png_ptr, info_ptr);
   bit_depth = png_get_bit_depth(png_ptr, info_ptr);
   color_type = png_get_color_type(png_ptr, info_ptr);
   //transform all pngs into 8 bit grayscale
   if (color_type == PNG_COLOR_TYPE_PALETTE) {
     png_set_palette_to_rgb(png_ptr);
     png_set_rgb_to_gray_fixed(png_ptr, 1, -1, -1);//silently do conversion with default color weightings
   }
   if (color_type == PNG_COLOR_TYPE_GRAY && bit_depth < 8)
     png_set_expand_gray_1_2_4_to_8(png_ptr);
   if(bit_depth == 16)
     png_set_strip_16(png_ptr);
   if (color_type & PNG_COLOR_MASK_ALPHA)
     png_set_strip_alpha(png_ptr);
   if (color_type == PNG_COLOR_TYPE_RGB ||
       color_type == PNG_COLOR_TYPE_RGB_ALPHA)
     png_set_rgb_to_gray_fixed(png_ptr, 1, -1, -1);//silently do conversion with default color weightings
   //should leave us with either an 8 bit grayscale
   png_read_update_info(png_ptr, info_ptr);
   bit_depth = png_get_bit_depth(png_ptr, info_ptr);
   color_type = png_get_color_type(png_ptr, info_ptr);
   //sanity check
   if(color_type != PNG_COLOR_TYPE_GRAY && bit_depth != 8) {
      png_destroy_read_struct(&png_ptr, &info_ptr, png_infopp_NULL);
      fclose(fp);
      return (ERROR_FORMAT);
   }
   *p_width = png_get_image_width(png_ptr, info_ptr);
   png_uint_32 height = png_get_image_height(png_ptr, info_ptr);
   int rowbytes = png_get_rowbytes(png_ptr, info_ptr);
   char *image_data = malloc(rowbytes * height);
   if(!image_data) {
      png_destroy_read_struct(&png_ptr, &info_ptr, png_infopp_NULL);
      fclose(fp);
      return (ERROR_MALLOC);
   }
   png_bytep *row_pointers = malloc(height * sizeof(png_byte*));
   if(!row_pointers) {
     free(image_data);
     png_destroy_read_struct(&png_ptr, &info_ptr, png_infopp_NULL);
     fclose(fp);
     return (ERROR_MALLOC);
   }
   //set up the row pointers
   for(int c=0; c<height; c++)
     row_pointers[c] = image_data + rowbytes * c;
   //read in the image
   png_read_image(png_ptr, row_pointers);
   /*Should now have image data pointed to by row_pointers so fill in the return values*/
   *p_row_pointers = row_pointers;
   *p_height = height;
   /* Clean up */
   png_destroy_read_struct(&png_ptr, &info_ptr, png_infopp_NULL);
   fclose(fp);
   return 0;
}


png_uint_32 process_row(png_bytep row_data, png_uint_32 width, png_uint_32 sample_length) {
  png_uint_32 sample_total = 0;
  png_uint_32 retval;
  //process initial sample
  int c;
  for(c = 0; c < sample_length; c++) {
    sample_total += *(row_data + c);
  }
  retval = sample_total;
  for(; c < width; c++) {
    sample_total += *(row_data + c);
    sample_total -= *(row_data + c - sample_length);
    if(sample_total < retval)
      retval = sample_total;
  }
  return retval;
}


void weighted_mean_rows(png_uint_32 *p_row_ink, png_uint_32 height) {
  //e,g, weighted mean of row 2 = (row 0 + row 4 + 2 * (row 1 + row 3) + 3 * row 2)/9
  for(int c = 2; c < height - 2; c++) {
    *(p_row_ink + c) = (*(p_row_ink + c - 2) + *(p_row_ink + c + 2) +
                        2 * (*(p_row_ink + c - 1) + *(p_row_ink + c + 1)) +
                        3 * *(p_row_ink + c)) / 9;
  }
}


static PyObject *
process_image(PyObject *self, PyObject *args) {
  png_bytep *row_pointers = 0;
  png_uint_32 height, width, sample_fraction, sample_width;
  char *filename;
  char message[64];
  int res;
  //unpack filename
  if(!PyArg_ParseTuple(args, "sl", &filename, &sample_fraction))
    return NULL;
  //read in the png
  res = read_png(filename, &row_pointers, &height, &width);
  if(res) {
    //note that if read_png fails, it is guaranteed that all allocated memory will have been cleaned up
    snprintf(message, 64, "PNG Error: %d", res);
    PyErr_SetString(PyExc_Exception, message);
    return NULL;
  }
  //process the png
  png_uint_32 row_ink[height];
  sample_width = width / sample_fraction;
  row_ink[0] = 0xff * sample_width;//first line gives reference maximum value
  for(int c = 1; c < height; c++) {
    row_ink[c] = process_row(row_pointers[c], width, sample_width);
  }
  //copy the result into a python list
  PyObject *list = PyList_New(height);
  if(!list) {
    free(row_pointers[0]);
    free(row_pointers);
    return NULL;
  }
  for(long c = 0; c < height; c++) {
      PyObject *num = PyInt_FromLong(row_ink[c]);
      if(!num) {
        Py_DECREF(list);
        free(row_pointers[0]);
        free(row_pointers);
        return NULL;
      }
      PyList_SET_ITEM(list, c, num);//List adopts reference count
  }
  free(row_pointers[0]);
  free(row_pointers);
  return list;
}


static PyMethodDef linedetect_methods[] = {
  {"process_image", process_image, METH_VARARGS, "Process a PNG into a list (one entry per row) of pixel sample totals."},
  {NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC initscanner(void) {
  Py_InitModule("scanner", linedetect_methods);
}


int main(int argc, char **argv)
{
  png_bytep *row_pointers = 0;
  png_uint_32 height, width;
  int res = read_png(argv[1], &row_pointers, &height, &width);
  if(res) {
    printf("Error: %d", res);
  }
  else {
    png_uint_32 row_ink[height];
    for(int c = 0; c < height; c++) {
      row_ink[c] = process_row(row_pointers[c], width, width/16);
    }
    weighted_mean_rows(row_ink, height);
    /* for(int c = 0; c < height; c++) { */
    /*   printf("Row %d: %d\n", c, (int)row_ink[c]); */
    /* } */
  }
  if(row_pointers) {
    free(row_pointers[0]);
    free(row_pointers);
  }
}

