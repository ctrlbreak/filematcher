# VHS Demo Tape for File Matcher

Output demo.gif

Set FontSize 15
Set Width 1000
Set Height 600
Set Theme "Dracula"
Set Padding 20
Set Shell bash
Set TypingSpeed 30ms

# Start fresh
Hide
Type "cd /Users/patrick/dev/cursor_projects/filematcher && clear"
Enter
Sleep 500ms
Show

# Execute hardlink with interactive confirmation
Type "/opt/homebrew/bin/python3 file_matcher.py /tmp/demo_master /tmp/demo_other --action hardlink --execute"
Enter
Sleep 3000ms

# Answer prompts with Enter after each
Type "y"
Enter
Sleep 1500ms

Type "y"
Enter
Sleep 1500ms

Type "n"
Enter
Sleep 1500ms

Type "a"
Enter
Sleep 3000ms

Sleep 2000ms
