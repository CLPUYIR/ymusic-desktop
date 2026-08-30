Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oShortcut = WshShell.CreateShortcut(strDesktop & "\YMusic Desktop.lnk")
oShortcut.TargetPath = "C:\Users\abhis\ymusic_desktop\run.bat"
oShortcut.WorkingDirectory = "C:\Users\abhis\ymusic_desktop"
oShortcut.WindowStyle = 1
oShortcut.Description = "YMusic Desktop Client"
oShortcut.Save
