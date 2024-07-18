#!/bin/sh

(
echo 'WARNING: THIS SCRIPT EXECUTES AI-GENERATED PROGRAMS!'
echo 'ARE YOU USING SYSTEM-LEVEL CONTAINER?'
echo '(Press Enter to continue; Press CTRL+C to cancel)'
) >&2
read

litrepl restart ai
(
echo "/model \"~/.local/share/nomic.ai/GPT4All/Meta-Llama-3-8B-Instruct.Q4_0.gguf\""
echo "Please be very brief! How can I convert 'input.gif' to 'output.webm' using ffmpeg oneliner?"
) | tee >(cat 1>&2) \
  | litrepl eval-code ai \
  | tee >(cat 1>&2) \
  | sed -n 's/^`\?\(ffmpeg[^`]*\)`\?$/\1/p' \
  >_cmd.sh

while ! (
        rm output.webm 2>/dev/null ; \
        test -s _cmd.sh || { echo "Please suggest an ffmpeg oneliner!" >&2 ; exit 1; } && \
        sh _cmd.sh && \
        test -s output.webm || { echo "OUTPUT FILE IS EMPTY!" >&2 ; exit 1; } ; \
        ) 2>_err.txt ; do
  (
  echo $'Nope! The output was:\n\n'
  cat _err.txt | tail
  echo $'\n\nPlease make another attempt!'
  ) | tee >(cat 1>&2) \
    | litrepl eval-code ai \
    | tee >(cat 1>&2) \
    | sed -n 's/^`\?\(ffmpeg[^`]*\)`\?$/\1/p' \
    > _cmd.sh
done
