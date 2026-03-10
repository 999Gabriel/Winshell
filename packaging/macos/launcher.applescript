on run
	set appPath to POSIX path of (path to me)
	set runtimePath to appPath & "Contents/Resources/winshell-runtime"
	set launchCmd to quoted form of runtimePath & "; echo; echo '[WinShell exited] Press Enter to close...'; read"

	tell application "Terminal"
		activate
		do script launchCmd
	end tell
end run
