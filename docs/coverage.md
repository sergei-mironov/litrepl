## Coverage report

``` python
!coverage report --format=markdown -m
```

<!--result-->
| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| python/litrepl/\_\_init\_\_.py              |       34 |       12 |     65% |24-29, 35-40 |
| python/litrepl/base.py                      |      636 |       82 |     87% |61, 92, 102, 142, 150, 194, 243-249, 251-253, 259, 265, 439, 477-482, 492, 502-503, 533, 615-617, 674-675, 732, 754-756, 800-809, 832, 838-879 |
| python/litrepl/eval.py                      |      381 |       31 |     92% |39-40, 89-90, 116-117, 129, 131-132, 148-149, 185-186, 192, 218-219, 243-245, 269, 374-375, 393, 416, 430-433, 448-449, 472 |
| python/litrepl/interpreters/\_\_init\_\_.py |        0 |        0 |    100% |           |
| python/litrepl/interpreters/aicli.py        |       49 |       31 |     37% |14-17, 22-27, 29-30, 32, 34-37, 39-57, 59-65 |
| python/litrepl/interpreters/ipython.py      |       29 |        1 |     97% |        68 |
| python/litrepl/interpreters/python.py       |       22 |        1 |     95% |        39 |
| python/litrepl/interpreters/shell.py        |       22 |        1 |     95% |        26 |
| python/litrepl/main.py                      |      228 |       52 |     77% |23-25, 219-220, 271, 280, 297-302, 304-306, 318-329, 344, 347-348, 356-360, 369-377, 379-380, 385-392 |
| python/litrepl/revision.py                  |        1 |        1 |      0% |         2 |
| python/litrepl/semver.py                    |        1 |        1 |      0% |         2 |
| python/litrepl/types.py                     |       97 |        6 |     94% |145, 150, 156, 160, 164, 167 |
| python/litrepl/utils.py                     |      100 |        6 |     94% |37, 55, 129-132 |
|                                   **TOTAL** | **1600** |  **225** | **86%** |           |
<!--noresult-->
