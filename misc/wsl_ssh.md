## why use wsl-ssh on windows? 

Windows stock openssh does not support [ssh multiplexing](https://www.golinuxcloud.com/ssh-multiplexing). If we can use wsl-ssh on windows, we can resuse the ssh sessions without repeated MFA for a certain amount of time. 

## how to use wsl-ssh? 

1. Create a .bat file with the following line. Name it as wslssh.bat. 

`C:\Windows\system32\wsl.exe bash -ic 'ssh %*'`

2. Use wslssh.bat.

`.\wslssh.bat user@remote-machine`

## how to use wsl-ssh in vs code on windows? 

In vscode settings, search "remote.SSH.path", and put the abslute path of `wslssh.bat` there. 

When connecting to a remote session, the remote machine will talk with wsl instance for authentication instead of windows host. 


