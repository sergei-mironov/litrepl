## Coverage report

``` python
!coverage report --format=markdown -m
```

<!--result-->
| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| python/litrepl/\_\_init\_\_.py              |       34 |       12 |     65% |24-29, 35-40 |
| python/litrepl/base.py                      |      558 |       46 |     92% |48, 60, 78, 88, 137, 167, 207-213, 223, 229, 401, 412-413, 437-442, 450, 473, 499-500, 558, 615-616, 681-683, 727-736, 754-759 |
| python/litrepl/eval.py                      |      336 |      100 |     70% |36, 39-40, 49, 63, 67, 73, 77-78, 90-91, 93, 96-97, 101, 116, 118, 121-123, 126, 148-149, 151-152, 154, 156-159, 173-176, 179-183, 199, 205, 207, 212-223, 236, 249, 265-266, 277-280, 299-301, 317-319, 321, 326, 330, 335-339, 352, 364-370, 374-375, 381-382, 414, 420-423, 438, 442, 450, 454, 458, 465-471, 490-505 |
| python/litrepl/interpreters/\_\_init\_\_.py |        0 |        0 |    100% |           |
| python/litrepl/interpreters/aicli.py        |       50 |       19 |     62% |15-17, 37, 41-51, 60-66 |
| python/litrepl/interpreters/ipython.py      |       32 |        1 |     97% |        70 |
| python/litrepl/interpreters/python.py       |       22 |        1 |     95% |        38 |
| python/litrepl/interpreters/shell.py        |       22 |        1 |     95% |        26 |
| python/litrepl/main.py                      |      206 |       47 |     77% |22-24, 194, 197-200, 243, 252, 269-274, 276-278, 289-298, 311, 321-325, 334-342, 344-345, 351-352 |
| python/litrepl/revision.py                  |        1 |        1 |      0% |         2 |
| python/litrepl/semver.py                    |        1 |        1 |      0% |         2 |
| python/litrepl/types.py                     |       94 |        6 |     94% |137, 142, 148, 152, 156, 159 |
| python/litrepl/utils.py                     |       97 |        6 |     94% |37, 55, 129-132 |
|                                   **TOTAL** | **1453** |  **241** | **83%** |           |
<!--noresult-->
