Executable sections are marked with the "python" tag. Putting the cursor on one
of the typing the :LitEval1 command executes its code in a background Python
interpreter.

``` python
W='Hello, World!'
print(W)
```

Verbatim sections next to the executable section are result sections. Litrepl
pastes the result here during the evaluation. The original content of this
section is replaced.

``` result
Hello, World!
```

Markdown comment-looking tags `lresult`/`lnoresult` also mark executable and
result sections. This way we can produce the Markdown document markup directly.

<!--
``` python
print("Hello, LitREPL")
```
-->

<!--result-->
Hello, LitREPL
<!--noresult-->

