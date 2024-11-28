LitREPL
=======

* 3+4
* How to evaluate Python code in Vim?

   ``` python
   import tqdm, time
   for i in (bar := tqdm.tqdm(range(6))):
     time.sleep(0.5)
   ```

   ``` result
   100%|██████████| 6/6 [00:03<00:00,  2.00it/s]
   ```

