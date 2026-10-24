#!/bin/sh

set -e

# Check if a PID is provided as an argument
if [ -z "$1" ]; then
  echo "Please provide a process identifier (PID)."
  exit 1
fi

PID="$1"

# Function to find and print the child processes along with their process groups and session IDs
get_child_processes() {
  local parent_pid=$1

  # Using ps to find child processes of the given PID
  child_pids=$(ps --ppid $parent_pid -o pid=)

  for child_pid in $child_pids; do
    # Get the process group ID and session ID for each child process
    group_id=$(ps -p $child_pid -o pgid=)
    session_id=$(ps -p $child_pid -o sid=)

    echo "Child PID: $child_pid, Group ID: $group_id, Session ID: $session_id"

    # Recursively find and print child processes
    get_child_processes $child_pid
  done
}

# Print the main process information
main_group_id=$(ps -p $PID -o pgid=)
main_session_id=$(ps -p $PID -o sid=)
echo "Main PID: $PID, Group ID: $main_group_id, Session ID: $main_session_id"

# Start with the provided PID
get_child_processes $PID
