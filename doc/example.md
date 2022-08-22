Executable sections are marked with the "python" tag. Putting the cursor on one
of the typing the :LitEval1 command executes its code in a background Python
interpreter.

```python
W='Hello, World!'
print(W)
```

Verbatim sections next to the executable section are result sections. The output
of the code from the executable section is pasted here. The original
content of the section is replaced with the output of the last execution.

```
Hello, World!
```

Markdown comments with `litrepl` word also mark a result section. This way we
could produce the markdown document markup.

<!--litrepl-->
Hello, World!
<!--litrepl-->

