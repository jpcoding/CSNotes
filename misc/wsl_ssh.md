## why use wsl-ssh on windows? 

Windows stock openssh does not support [ssh multiplexing](https://www.golinuxcloud.com/ssh-multiplexing). If we can use wsl-ssh on windows, we can resuse the ssh sessions without repeated MFA for a certain amount of time. 

## how to use wsl-ssh? 

1. Create a .bat file with the following line
`C:\Windows\system32\wsl.exe bash -ic 'ssh %*'`



## how to use wsl-ssh in vs code on windows? 
