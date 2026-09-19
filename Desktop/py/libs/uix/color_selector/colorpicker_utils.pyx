# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False
# cython: language_level=3
# cython: infer_types=True

cimport cython
from libc.stdlib cimport malloc, free
from cpython.bytes cimport PyBytes_FromStringAndSize

# @cython.boundscheck(False)
# @cython.wraparound(False)
# cdef void hsv_to_rgb(double h, double s, double v, double* r, double* g, double* b):
#     if s <= 0.0:
#         r[0] = v
#         g[0] = v
#         b[0] = v
#         return
#     cdef int i = <int>(h * 6.0)
#     cdef double f = h * 6.0 - i
#     cdef double p = v * (1.0 - s)
#     cdef double q = v * (1.0 - s * f)
#     cdef double t = v * (1.0 - s * (1.0 - f))
#     i %= 6

#     if i == 0:
#         r[0] = v; g[0] = t; b[0] = p
#     elif i == 1:
#         r[0] = q; g[0] = v; b[0] = p
#     elif i == 2:
#         r[0] = p; g[0] = v; b[0] = t
#     elif i == 3:
#         r[0] = p; g[0] = q; b[0] = v
#     elif i == 4:
#         r[0] = t; g[0] = p; b[0] = v
#     elif i == 5:
#         r[0] = v; g[0] = p; b[0] = q


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void hsl_to_rgb(double h, double s, double l, double* r, double* g, double* b):
    if s <= 0.0:
        r[0] = l
        g[0] = l
        b[0] = l
        return

    # Вычисление хромы
    cdef double c = (1.0 - abs(2.0 * l - 1.0)) * s
    # Умножение hue на 6 для перехода к диапазону [0, 6)
    cdef double h_prime = h * 6.0
    # Промежуточное значение X
    cdef double x = c * (1.0 - abs(h_prime % 2.0 - 1.0))
    # Сдвиг для коррекции цвета
    cdef double m = l - c / 2.0

    cdef double r1, g1, b1

    if h_prime < 1.0:
        r1 = c; g1 = x; b1 = 0.0
    elif h_prime < 2.0:
        r1 = x; g1 = c; b1 = 0.0
    elif h_prime < 3.0:
        r1 = 0.0; g1 = c; b1 = x
    elif h_prime < 4.0:
        r1 = 0.0; g1 = x; b1 = c
    elif h_prime < 5.0:
        r1 = x; g1 = 0.0; b1 = c
    else:
        r1 = c; g1 = 0.0; b1 = x

    r[0] = r1 + m
    g[0] = g1 + m
    b[0] = b1 + m


@cython.boundscheck(False)
@cython.wraparound(False)
def get_color_data(int width, int height, double lightness):
    cdef:
        int x, y
        double hue, saturation
        double r, g, b
        unsigned char* data = <unsigned char*>malloc(width * height * 3)
        unsigned char* ptr = data
        double fw = <double>width
        double fh = <double>height

    for y in range(height):
        saturation = <double>(y) / <double>(height)
        for x in range(width):
            hue = <double>(x) / <double>(width)
            hsl_to_rgb(hue, saturation, lightness, &r, &g, &b)

            ptr[0] = <unsigned char>(r * 255.0)
            ptr[1] = <unsigned char>(g * 255.0)
            ptr[2] = <unsigned char>(b * 255.0)
            ptr += 3

    result = PyBytes_FromStringAndSize(<char*>data, width * height * 3)
    free(data)
    return result
