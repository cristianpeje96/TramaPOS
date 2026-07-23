' TramaPos · Arranca iniciar_backend.bat sin mostrar ninguna ventana.
' Se usa desde un acceso directo en la carpeta de Inicio de Windows
' (shell:startup) para que el POS arranque solo al prender el PC.
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run Chr(34) & carpeta & "\iniciar_backend.bat" & Chr(34), 0, False
