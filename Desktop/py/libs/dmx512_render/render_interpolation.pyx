# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False
# cython: language_level=3
# cython: infer_types=True

cimport cython
from libc.stdlib cimport malloc, calloc, free


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void linspace_c(int start, int stop, int n, int* result) noexcept nogil:
    if n == 1:
        result[0] = stop
        return
    cdef double h = (<double>stop - <double>start) / (<double>n - 1)
    cdef int i
    for i in range(n):
        result[i] = <int>(start + h * i)
    result[n - 1] = stop


def linspace(int start, int stop, int n):
    if n <= 0:
        raise ValueError("n must be positive")
    cdef int* lst = <int*>malloc(n * sizeof(int))
    linspace_c(start, stop, n, lst)
    cdef list retn = [lst[i] for i in range(n)]
    free(lst)
    return retn


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void compute_xdiff(double* x, int n, double* xdiff) noexcept nogil:
    cdef int i
    for i in range(n-1):
        xdiff[i] = x[i+1] - x[i]


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void compute_dydx(double* xdiff, double* y, int n, double* dydx) noexcept nogil:
    cdef int i
    for i in range(n-1):
        if xdiff[i] == 0:
            dydx[i] = 0.0
        else:
            dydx[i] = (y[i+1] - y[i]) / xdiff[i]


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void compute_coefficients(double* xdiff, double* dydx, int n, 
                               double* w, double* z) noexcept nogil:
    cdef:
        int i
        double m
    
    w[0] = 0.0
    z[0] = 0.0
    
    for i in range(1, n-1):
        m = xdiff[i-1] * (2 - w[i-1]) + 2 * xdiff[i]
        if m == 0:
            w[i] = 0.0
            z[i] = 0.0
        else:
            w[i] = xdiff[i] / m
            z[i] = (6*(dydx[i]-dydx[i-1]) - xdiff[i-1]*z[i-1]) / m
    
    z[n-1] = 0.0
    
    for i in range(n-2, -1, -1):
        z[i] = z[i] - w[i] * z[i+1]


@cython.boundscheck(False)
@cython.wraparound(False)
cdef void find_indices(double* x, int n, int len_x0, int* result) noexcept nogil:
    cdef int j, i, found
    for j in range(len_x0):
        found = 0
        for i in range(n - 1):  # Ограничиваем до n-2
            if x[i] <= j < x[i+1]:
                result[j] = i + 1
                found = 1
                break
        if not found:
            if j >= x[n-1]:
                result[j] = n - 1
            else:
                result[j] = 0


@cython.boundscheck(False)
@cython.wraparound(False)
def cubic_interpolate(tuple x_tup, tuple y_tup):
    cdef:
        int n = len(x_tup)
        int len_x0 = x_tup[n - 1] - x_tup[0] + 1
        int min_x_tup = min(x_tup)
        int i, j
        double* x = <double*> malloc(n * sizeof(double))
        double* y = <double*> malloc(n * sizeof(double))
        double* xdiff = <double*> malloc((n-1) * sizeof(double))
        double* dydx = <double*> malloc((n-1) * sizeof(double))
        double* w = <double*> calloc(n-1, sizeof(double))
        double* z = <double*> calloc(n, sizeof(double))
        int* indices = <int*> malloc(len_x0 * sizeof(int))
        int* result = <int*> malloc(len_x0 * sizeof(int))
        int idx
        double xi_prev, xi, yi_prev, yi
        double zi_prev, zi, hi, inv_hi, inv_6hi
        double dx1, dx2, t1, t2, t3, t4, value
        int clipped

    try:
        # Инициализация массивов
        for i in range(n):
            x[i] = x_tup[i] - min_x_tup
            y[i] = y_tup[i]

        # Вычисление производных и коэффициентов
        compute_xdiff(x, n, xdiff)
        compute_dydx(xdiff, y, n, dydx)
        compute_coefficients(xdiff, dydx, n, w, z)
        find_indices(x, n, len_x0, indices)

        # Основной цикл интерполяции
        with nogil:
            for j in range(len_x0):
                idx = indices[j]
                xi_prev = x[idx-1]
                xi = x[idx]
                yi_prev = y[idx-1]
                yi = y[idx]
                zi_prev = z[idx-1]
                zi = z[idx]

                hi = xi - xi_prev
                if hi <= 0:
                    hi = 1.0

                inv_hi = 1.0 / hi
                inv_6hi = inv_hi / 6.0
                dx1 = xi - j
                dx2 = j - xi_prev

                t1 = dx1*dx1*dx1 * zi_prev * inv_6hi
                t2 = dx2*dx2*dx2 * zi * inv_6hi
                t3 = (yi_prev * inv_hi - zi_prev * hi / 6.0) * dx1
                t4 = (yi * inv_hi - zi * hi / 6.0) * dx2

                value = t1 + t2 + t3 + t4
                clipped = <int>value
                clipped = max(0, clipped)
                clipped = min(clipped, 255)
                result[j] = clipped
        
        # Конвертация результата
        res_list = [result[i] for i in range(len_x0)]

    finally:
        free(x)
        free(y)
        free(xdiff)
        free(dydx)
        free(w)
        free(z)
        free(indices)
        free(result)

    return res_list
