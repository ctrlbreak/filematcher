# VHS Demo Tape for File Matcher
# https://github.com/charmbracelet/vhs

Output demo.gif

Set FontSize 14
Set Width 900
Set Height 500
Set Theme "Dracula"
Set Padding 20
Set Shell zsh

# Show the command we're about to run
Type "# Find duplicate files across directories"
Enter
Sleep 500ms

Type "python file_matcher.py /tmp/demo_master /tmp/demo_other"
Enter
Sleep 2s

Type ""
Enter
Sleep 500ms

Type "# Preview hardlink deduplication"
Enter
Sleep 500ms

Type "python file_matcher.py /tmp/demo_master /tmp/demo_other --action hardlink"
Enter
Sleep 2s

Type ""
Enter
Sleep 500ms

Type "# Execute with interactive confirmation"
Enter
Sleep 500ms

Type "python file_matcher.py /tmp/demo_master /tmp/demo_other --action hardlink --execute"
Enter
Sleep 1500ms

# Answer first prompt with 'y'
Type "y"
Sleep 1s

# Answer second prompt with 'n'
Type "n"
Sleep 1s

Sleep 2s
