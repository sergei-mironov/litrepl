## Coverage report

``` python
!coverage report --format=markdown -m
```

<!--result-->
| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| python/litrepl/\_\_init\_\_.py              |       34 |       12 |     65% |24-29, 35-40 |
| python/litrepl/base.py                      |      581 |       47 |     92% |48, 60, 91, 101, 149, 184, 224-230, 240, 246, 418, 429-430, 454-459, 467, 477-478, 508, 588, 645-646, 703, 725-727, 771-780, 798-803 |
| python/litrepl/eval.py                      |      336 |       32 |     90% |36, 39-40, 87-88, 100, 131, 157-158, 182-184, 199, 208, 284-290, 309-310, 328, 337, 362, 374-377, 390-391 |
| python/litrepl/interpreters/\_\_init\_\_.py |        0 |        0 |    100% |           |
| python/litrepl/interpreters/aicli.py        |       49 |       19 |     61% |15-17, 36, 40-50, 59-65 |
| python/litrepl/interpreters/ipython.py      |       29 |        1 |     97% |        68 |
| python/litrepl/interpreters/python.py       |       22 |        1 |     95% |        39 |
| python/litrepl/interpreters/shell.py        |       22 |        1 |     95% |        26 |
| python/litrepl/main.py                      |      210 |       51 |     76% |22-24, 194, 197-200, 243, 252, 269-274, 276-278, 289-300, 313, 316-317, 325-329, 338-346, 348-349, 355-356 |
| python/litrepl/revision.py                  |        1 |        1 |      0% |         2 |
| python/litrepl/semver.py                    |        1 |        1 |      0% |         2 |
| python/litrepl/types.py                     |       95 |        6 |     94% |140, 145, 151, 155, 159, 162 |
| python/litrepl/utils.py                     |       97 |        6 |     94% |37, 55, 129-132 |
|                                   **TOTAL** | **1477** |  **178** | **88%** |           |
<!--noresult-->
