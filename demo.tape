# VHS Demo Tape for File Matcher
# https://github.com/charmbracelet/vhs

Output demo.gif

Set FontSize 14
Set Width 900
Set Height 500
Set Theme "Dracula"
Set Padding 20
Set Shell zsh
Set TypingSpeed 50ms

# Start fresh
Hide
Type "cd /Users/patrick/dev/cursor_projects/filematcher && clear"
Enter
Sleep 500ms
Show

# Compare mode
Type "# Find duplicate files"
Enter
Sleep 300ms

Type "python file_matcher.py /tmp/demo_master /tmp/demo_other"
Enter
Sleep 2500ms

# Preview mode
Type "# Preview hardlink deduplication"
Enter
Sleep 300ms

Type "python file_matcher.py /tmp/demo_master /tmp/demo_other --action hardlink"
Enter
Sleep 2500ms

# Execute mode
Type "# Execute with interactive confirmation (y/n/a/q)"
Enter
Sleep 300ms

Type "python file_matcher.py /tmp/demo_master /tmp/demo_other --action hardlink --execute"
Enter
Sleep 2000ms

# Answer prompts
Type "y"
Sleep 1500ms

Type "n"
Sleep 2000ms

Sleep 1500ms
