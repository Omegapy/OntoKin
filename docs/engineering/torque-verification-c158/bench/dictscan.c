/* Research probe for GIL-enabled CPython. Exercise only in the isolated benchmark. */
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#ifdef Py_GIL_DISABLED
#error "This experiment requires GIL-enabled CPython"
#endif

static PyObject *
scan(PyObject *self, PyObject *args)
{
    PyObject *dicts, *lengths, *keys, *values;
    if (!PyArg_UnpackTuple(args, "scan", 4, 4, &dicts, &lengths, &keys, &values)) {
        return NULL;
    }
    if (!PyTuple_CheckExact(dicts) || !PyTuple_CheckExact(lengths)
            || !PyTuple_CheckExact(keys) || !PyTuple_CheckExact(values)) {
        PyErr_SetString(PyExc_TypeError, "scan requires four exact tuples");
        return NULL;
    }

    Py_ssize_t n = PyTuple_GET_SIZE(dicts);
    Py_ssize_t total = PyTuple_GET_SIZE(keys);
    if (PyTuple_GET_SIZE(lengths) != n || PyTuple_GET_SIZE(values) != total) {
        Py_RETURN_FALSE;
    }

    Py_ssize_t accounted = 0;
    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject *dict = PyTuple_GET_ITEM(dicts, i);
        PyObject *expected = PyTuple_GET_ITEM(lengths, i);
        if (!PyDict_CheckExact(dict) || !PyLong_CheckExact(expected)) {
            PyErr_SetString(PyExc_TypeError, "expected an exact dict and exact int");
            return NULL;
        }
        Py_ssize_t length = PyLong_AsSsize_t(expected);
        if (length == -1 && PyErr_Occurred()) {
            return NULL;
        }
        if (length != PyDict_Size(dict) || length > total - accounted) {
            Py_RETURN_FALSE;
        }
        accounted += length;
    }
    if (accounted != total) {
        Py_RETURN_FALSE;
    }

    /* Borrow from live exact dicts and the strong-reference tuples. Keep the
       GIL throughout, without calls to user equality, hashing or numeric hooks. */
    for (int keys_pass = 1; keys_pass >= 0; keys_pass--) {
        PyObject *original = keys_pass ? keys : values;
        Py_ssize_t index = 0;
        for (Py_ssize_t i = 0; i < n; i++) {
            PyObject *dict = PyTuple_GET_ITEM(dicts, i);
            Py_ssize_t position = 0;
            PyObject *key, *value;
            while (PyDict_Next(dict, &position, &key, &value)) {
                if (index >= total || (keys_pass ? key : value) != PyTuple_GET_ITEM(original, index)) {
                    Py_RETURN_FALSE;
                }
                index++;
            }
        }
        if (index != total) {
            Py_RETURN_FALSE;
        }
    }
    Py_RETURN_TRUE;
}

static PyMethodDef methods[] = {
    {"scan", scan, METH_VARARGS, "Check lengths, original keys, then original values."},
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "_dictscan_probe", NULL, -1, methods
};
PyMODINIT_FUNC PyInit__dictscan_probe(void)
{
    return PyModule_Create(&module);
}
