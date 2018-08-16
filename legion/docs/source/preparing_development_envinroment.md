# Preparing development enviroment 
1. Using Vargant or VirtualBox install Ubuntu/Lubuntu image v16.04.
To fix bidirectional copy paste from windows to Ubuntu look for solution
https://askubuntu.com/questions/22743/how-do-i-install-guest-additions-in-a-virtualbox-vm/22745#22745
2. Install packages to new system:
    * Java (JRE,JDK)
    ```bash
    sudo apt-get update
    sudo apt-get install default-jre
    sudo apt-get install default-jdk
    sudo add-apt-repository ppa:webupd8team/java
    sudo apt-get update
    sudo apt-get install oracle-java8-installer
    ```
    
    * Python 3.5+
    ```bash
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install python3.6
    ```
    
    * Docker (allow non-root user use docker)
    ```text
    https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-using-the-repository
    https://docs.docker.com/install/linux/linux-postinstall/
    ```
    
    * kops binaries  
    ```bash
    wget https://github.com/kubernetes/kops/releases/download/1.8.0/kops-linux-amd64
    chmod +x kops-linux-amd64
    sudo mv kops-linux-amd64 /usr/local/bin/kops
    ```
    
    * kubectl binaries
    ```bash
    sudo apt-get update && sudo apt-get install -y apt-transport-https
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
    sudo touch /etc/apt/sources.list.d/kubernetes.list 
    echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list
    sudo apt-get update
    sudo apt-get install -y kubectl
    kubectl version
    ```
3. Install PyCharm