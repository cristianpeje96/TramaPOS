' TramaPos · Arranca TramaPos-Agente.exe sin mostrar ninguna ventana.
' Se usa desde un acceso directo en la carpeta de Inicio de Windows
' (shell:startup) para que el agente arranque solo al prender el PC.
' Debe estar en la misma carpeta que la subcarpeta "dist" generada por
' build_exe.bat.
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run Chr(34) & carpeta & "\dist\TramaPos-Agente.exe" & Chr(34), 0, False
