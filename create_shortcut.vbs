Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oShortcut = WshShell.CreateShortcut(strDesktop & "\YMusic Desktop.lnk")
strScriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
oShortcut.TargetPath = strScriptDir & "\run.bat"
oShortcut.WorkingDirectory = strScriptDir
oShortcut.WindowStyle = 1
oShortcut.Description = "YMusic Desktop Client"
oShortcut.Save
