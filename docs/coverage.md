## Coverage report

``` python
!coverage report --format=markdown -m
```

<!--result-->
| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| python/litrepl/\_\_init\_\_.py              |       34 |       12 |     65% |24-29, 35-40 |
| python/litrepl/base.py                      |      646 |       56 |     91% |61, 92, 102, 150, 194, 243-249, 259, 265, 439, 477-482, 492, 844, 850-891 |
| python/litrepl/eval.py                      |      381 |       31 |     92% |39-40, 89-90, 116-117, 129, 131-132, 148-149, 185-186, 192, 218-219, 243-245, 269, 374-375, 393, 416, 430-433, 448-449, 472 |
| python/litrepl/interpreters/\_\_init\_\_.py |        0 |        0 |    100% |           |
| python/litrepl/interpreters/aicli.py        |       49 |       19 |     61% |15-17, 36, 40-50, 59-65 |
| python/litrepl/interpreters/ipython.py      |       29 |        1 |     97% |        68 |
| python/litrepl/interpreters/python.py       |       22 |        1 |     95% |        39 |
| python/litrepl/interpreters/shell.py        |       22 |        1 |     95% |        26 |
| python/litrepl/main.py                      |      232 |       20 |     91% |23-25, 227-228, 329, 369, 380, 385-388, 390-391, 396-403 |
| python/litrepl/revision.py                  |        1 |        1 |      0% |         2 |
| python/litrepl/semver.py                    |        1 |        1 |      0% |         2 |
| python/litrepl/types.py                     |       97 |        6 |     94% |145, 150, 156, 160, 164, 167 |
| python/litrepl/utils.py                     |      100 |        6 |     94% |37, 55, 129-132 |
|                                   **TOTAL** | **1614** |  **155** | **90%** |           |
<!--noresult-->
