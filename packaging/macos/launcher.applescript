on run
	set mePath to POSIX path of (path to me)
	if mePath ends with "/" then set mePath to text 1 thru -2 of mePath

	set marker to "/Contents/"
	if mePath contains marker then
		set markerOffset to offset of marker in mePath
		set bundleRoot to text 1 thru (markerOffset - 1) of mePath
	else
		set bundleRoot to mePath
	end if

	set runtimePath to bundleRoot & "/Contents/Resources/winshell-runtime"
	set launchCmd to "clear; " & quoted form of runtimePath & "; echo; echo '[WinShell exited] Press Enter to close...'; read"

	tell application "Terminal"
		activate
		do script launchCmd
	end tell
end run
