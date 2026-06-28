Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath
WshShell.Run "cmd /c " & chr(34) & strPath & "\Enviar Ofertas.bat" & chr(34) & " --headless > " & chr(34) & strPath & "\registro_execucao.txt" & chr(34) & " 2>&1", 0
Set WshShell = Nothing


