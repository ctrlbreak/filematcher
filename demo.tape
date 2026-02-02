# VHS Demo Tape for File Matcher
# https://github.com/charmbracelet/vhs

Output demo.gif

Set FontSize 14
Set Width 950
Set Height 550
Set Theme "Dracula"
Set Padding 20
Set Shell bash
Set TypingSpeed 40ms

# Start fresh
Hide
Type "cd /Users/patrick/dev/cursor_projects/filematcher && clear"
Enter
Sleep 500ms
Show

# Compare mode
Type "echo '=== Find duplicate files ==='"
Enter
Sleep 500ms

Type "/opt/homebrew/bin/python3 file_matcher.py /tmp/demo_master /tmp/demo_other"
Enter
Sleep 3000ms

Type ""
Enter
Sleep 300ms

# Preview mode
Type "echo '=== Preview hardlink deduplication ==='"
Enter
Sleep 500ms

Type "/opt/homebrew/bin/python3 file_matcher.py /tmp/demo_master /tmp/demo_other --action hardlink"
Enter
Sleep 3000ms

Type ""
Enter
Sleep 300ms

# Execute mode
Type "echo '=== Execute with interactive confirmation ==='"
Enter
Sleep 500ms

Type "/opt/homebrew/bin/python3 file_matcher.py /tmp/demo_master /tmp/demo_other --action hardlink --execute"
Enter
Sleep 2500ms

# Answer prompts
Type "y"
Sleep 2000ms

Type "n"
Sleep 2500ms

Sleep 2000ms
