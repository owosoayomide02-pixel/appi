' Double-click this to start Appi like a normal Windows app. No CMD window.
Option Explicit
Dim fso, sh, root, agent, cmd, launched
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
agent = root & "\apps\device-agent"
If Not fso.FolderExists(agent) Then
  MsgBox "Appi folder not found:" & vbCrLf & agent, 16, "Appi"
  WScript.Quit 1
End If
sh.CurrentDirectory = agent
launched = False
For Each cmd In Array("pythonw -m app.launcher", "pyw -3 -m app.launcher", "python -m app.launcher")
  On Error Resume Next
  Err.Clear
  sh.Run cmd, 0, False
  If Err.Number = 0 Then
    launched = True
    Exit For
  End If
  On Error GoTo 0
Next
If Not launched Then
  MsgBox "Could not start Appi. Install Python from python.org and try again.", 16, "Appi"
End If
