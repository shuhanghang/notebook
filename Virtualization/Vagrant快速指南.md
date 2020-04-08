# Vagrant  快速指南



## 一.安装Vagrant

### 1.1 关于Vagrant

Vagrant是一个用来构建和管理虚拟机环境的工具。

Vagrant实现了自动化虚拟机安装部署，大大减少了虚拟环境的配置时间。

Vagrant提供了一种简单的方式来配置可再生和便捷的工作环境，使用先进得工业标准技术和一致性工作流方式最大化提高个人和团队的效率和伸缩性。

Vagrant支持*VirtualBox, VMware, AWS,  [等等](https://www.vagrantup.com/docs/providers/)* ，并且支持工业标准[工具](https://www.vagrantup.com/docs/provisioning/)如 *shell scripts, Chef, 和Puppet*  能够在虚拟中自动安装和配置。

### 1.2 安装

Vagrant必须在运行虚拟机之前安装，Vagrant支持多平台多架构的设备通过[二进制包](https://www.vagrantup.com/downloads.html)来安装。

安装Vagrant后通过在命令行下执行`vagrant` 命令来验证vagrant是否可用：

```bash
$ vagrant
Usage: vagrant [options] <command> [<args>]

    -v, --version                    Print the version and exit.
    -h, --help                       Print this help.

# ...
```

> 请谨慎使用本地的包管理工具来安装Vagrant，因为在这些源中通常出现缺失必要的依赖或者vagrant版本过低的情况。建议使用[官网](<https://www.vagrantup.com/>)最新Vagrant来配合略低版本的虚拟机软件。





## 二.启动项目 

配置任何Vagrant项目的第一步是创建Vagrantfile，Vagrantfile主要用两个部分：

1：标记你项目的根目录，Vagrant的很多配置选项都与这个目录相关。

2：描述虚拟机的类型和运行项目需要的资源，和需要安装的软件以及连接虚拟机的方式。

Vagrant通过内建命令：`vagrant init` 来初始化目录，根据这篇快速开始指南的目的，请按照下列在终端运行：

```bash
$ mkdir vagrant_getting_started
$ cd vagrant_getting_started
$ vagrant init hashicorp/bionic64
```

运行后将在当前目录生成Vagrantfile。Vagrantfile是一个充满了注释和例子的文件，接下来我将来修改这个文件。

你还可以在预先存在的目录下使用：`vagrant init` 为已存在项目创建Vagrantfile。

如果你使用版本控制并且把项目的Vagrantfile提交到版本控制系统中，方便团队中其他人使用。





## 三.Boxes

除了使用积木的方式建立虚拟机，这个可能是一个缓慢和繁琐的过程，Vagrant 使用一个基础镜像来快速克隆虚拟机，这些基础镜像在Vagrant叫做 “boxes”，在创建一个新的Vagrantfile之后第一步便是指明在Vagrant环境使用的box。

### 3.1 安装box

使用`vagrant box add` 将Boxes add到Vagrant ，这将以指定的名称来存储box，所以在多个Vagrant环境中都可使用。如果你还没有添加box，你可以使用：

```bash
$ vagrant box add hashicorp/bionic64
```

这将从[HashiCorp's Vagrant Cloud box catalog](https://vagrantcloud.com/boxes/search) 下载叫*"hashicorp/bionic64"* 的box，这是一个简单的方式从官方云仓库下载boxes，但是你也可以通过自定义URL添加本地boxes。

一旦你add后Boxes就对于当前用户是全局的，你的每个项目都可以从这个box来克隆创建虚拟机，而且这并会修改box本身。例如当你的两个项目同时使用相同的*hashicorp/bionic64* box，我可以随意的 add 并不会影响当前这个box的虚拟机。

在上面的命令行中，你可能已经注意到了boxes采用了名称空间。Boxes 通过斜杠来分割用户用和box名，在上面的例子中“hashicorp”是用户名，“bioic64”是box名。你也可以通过指定 URLs或者本地路径来指明添加的boxes，但这在快速指南中暂时不作讨论。

###  3.2 使用box

现在我们已经添加了一个box到Vagrant，现在需要来配置我们项目。使用下列内容来配置Vagrantfile：

```bash
Vagrant.configure("2") do |config|
	config.vm.box = "hashicorp/bionic64"
end
```

这里的*"hashicorp/bionic64"* 必须和上面 add 的box名一样。以便让Vagrant知道哪个box被使用。如果之前没有add，Vagrant会自动下载 add 并运行。

你可以通过`config.vm.box_version` 变量来指明box的版本：

```bash
Vagrant.configure("2") do |config|
	config.vm.box = "hashicorp/bionic64"
	config.vm.box_version = "1.1.0"
end
```

你也可以通过来指定`config.vm.box_url`来使使用网络box：

```bash
Vagrant.configure("2") do |config|
	config.vm.box = "hashicorp/bionic64"
	config.vm.box_url = "https://vagrantcloud.com/hashicorp/bionic64"
end
```

### 3.3 查找更多的box

官方boxes：[HashiCorp's Vagrant Cloud box catalog](https://vagrantcloud.com/boxes/search) ，支持公有boxes和私用boxes。





## 四.启动和SSH

使用下面的命令启动你的虚拟机：

```bash
$ vagrant up
```

大约在一分钟以内，你将得到一个运行的Ubuntu虚拟机，因为使用Vagrant 运行虚拟机没有UI界面，所有不会看到整个过程。为了证明虚拟机正在运行，你可以使用SSH连接到虚拟机：

```bash
$ vagrant ssh
```

接下来将进入到一个SSH会话然后就可以进行交互式操作了。尽管可能缓存虚拟机的数据，但请谨慎使用`rm  -rf /`命令，因为Vagrant会把虚拟机的`/vagrant` 目录共享到主机下同Vagrantfile文件的目录下。

使用`CTRL+D、logout、eixt` 命令结束当前会话：

```bash
vagrant@bionic64:~$ logout
Connection to 127.0.0.1 closed.
```

运行`vagrant destroy`  来销毁虚拟机。

> `vagrant destroy` 命令并不会移除下载的box文件，要真正的移除box文件，你可以使用`vagrant box remove` 命令。





## 五.同步文件夹

通过配置*synced folders* ，Vagrant将自动同步虚拟机中的文件。

Vagrant默认会将项目目录共享到虚拟机中的*/vagrant* 下（这时目录下此时只有Vagrantfile文件）。

<!--注：个人在windows上测试时发现*/vagrant* 与项目目录不是实时同步，在重启虚拟机后同步成功！而在Linux上发现重启虚拟机后依然不同步。-->

需要特别注意的是在虚拟机中共享的目录是*/vagrant* 而不是*/home/vagrant* 。

如果你的终端显示客户端增强型工具错误（或者没有客户端增强型工具），你可能需要更新box或者选择不同的box。有些用户可能成功的安装`vagrant-vbguest` 插件，但这并不Vagrant官方支持的。

当使用*synced folders* ，你可以在主机同步目录下使用自己的编辑器来编辑文件。





## 六.配置

Vagrant支持自动配置功能，使用这个功能，在开启虚拟机之前Vagrant可以自动安装软件。

### 6.1 安装Apache

通过使用shell脚本，我们可以为我们的项目安装Apache。在同Vagrantfile的目录下创建下面的一个名叫*bootstrap.sh*的shell脚本：

```bash
#!/usr/bin/env bash

apt-get update
apt-get install -y apache2
if ! [ -L /var/www ]; then
  rm -rf /var/www
  ln -fs /vagrant /var/www
fi
```

接下来，我们配置在虚拟机启动时会读取的Vagrantfile文件：

```bash
Vagrant.configure("2") do |config|
  config.vm.box = "hashicorp/bionic64"
  config.vm.provision :shell, path: "bootstrap.sh"
end
```

`provision`告诉Vagrant使用*boostrrap.sh*脚本安装虚拟机。

### 6.2 关于配置

在Vagrant中一切即可配置，运行`vagrant up`在创建虚拟机时Vagrant将自动配置。你可以在你的终端上看到shell脚本的打印的结果。如果虚拟机已经创建，通过修改vagrantfile后运行`vagrant reload --provision`  来快速重启虚拟机并跳过初始化导入过程。在reload命令后使用provision参数来通过Vagrant运行配置，因为通常Vagrant只会在首次的`vagrant up`才会执行。

> 使用复杂的配置脚本，这可能是在打包自定义Vagrant box是更高效的方式（有点类似于Dockerfile创建容器镜像），具体请参照：[packaging custom boxes](https://www.vagrantup.com/docs/boxes/base.html) 

<!--注：个人在重载配置时，使用`vagrant reload` 或者`vagrant up`后新配置依然生效。--> 





## 七.网络配置

到现在我们的web server已经开启并且可以在本地机上修改文件然后同步到虚拟机中。然而在虚拟机中通过终端来访问web 页面并不让人满意，接下来，我们将通过 Vagrant 的网络模式来让我们可以在主机上来访问虚拟机web 主页。

### 7.1 端口转发

端口转发允许你将虚拟机中指定端口转发到主机上的某个端口上。当你访问主机的这个端口时，实际上所有的流量都转发到了虚拟机映射的端口上了。

通过修改Vagrantfile实现Apache服务端口的转发：

```bash
Vagrant.configure("2") do |config|
  config.vm.box = "hashicorp/bionic64"
  config.vm.provision :shell, path: "bootstrap.sh"
  config.vm.network :forwarded_port, guest: 80, host: 4567
end
```

通过运行 `vagrant reload` 或者 `vagrant up` （取决于虚拟机是否在运行）来使配置生效。

一旦虚拟机重新运行，主机浏览器上访问 http://127.0.0.1:4567 。将看到我们实际访问到了虚拟机中的Apache服务。

### 7.2 其他网络设置

Vagrant同样支持多种网络配置，分配虚拟机静态地址，或者使用桥接模式，其他网络配置请访问[networking](https://www.vagrantup.com/docs/networking/) 了解详情。





## 八.共享

Vagrant 共享使得你可以把你的Vagrant环境分享给互联网的任何人。通过分享你的URL，互联网上的任何设备都可以路由到你的Vagrant环境。

要实现共享的前提条件是必须安装`vagrant -share` 插件：

```bash
$ vagrant share
...
==> default: Creating Vagrant Share session...
==> default: HTTP URL: http://b1fb1f3f.ngrok.io
...
```

接下来在将链接地址复制到浏览器将会看到Apache页面，你可以将此链接分享给其他人。如果你修改了共享文件夹中的内容，必须`Ctrl+C`然后重新share来让链接地址刷新。

*Vagrant Share* 比简单的HTTP共享更强大，了解详情请访问：[complete Vagrant Share documentation](https://www.vagrantup.com/docs/share/)

> 1.Vagrant共享默认使用*ngork 内网穿透驱动器* ，不建议使用其他类型的驱动器。
> 2.基于设计初衷，Vagrant共享功能不建议使用在生产环境中。





## 九.虚拟机管理

Vagrant 提供*suspend（挂起） ，halt（停止）,destroy（销毁）* 三种方式来管理虚拟机：

**Supending**：在项目目录下使用`vagrant suspend `命令将会以文件的形式保存虚拟机当前状态然后关闭虚拟机，`vagrant up` 命令将重新开启虚拟机并恢复挂起之前的状态。这种方式的优点是快速，通常花费5到10秒的时间关闭和重启，缺点是会有更多的磁盘开销来存储虚拟机RAM状态。

**Halting**：在项目目录下使用`vagrant halt`命令将会优雅的关闭虚拟机，`vagrang up` 命令来重新启动虚拟机。这种方式的优点是完成的关闭你的虚拟机，保存磁盘的内容，并且允许你再次启动使用，缺点是将会花费更过的时间来冷启动，主机依然会消耗磁盘空间。

**Destroying**：在项目目录下使用`vagrant destroy` 命令将会使虚拟机彻底的从本机上清除，`vagrant up`将启动一个全新的虚拟机。这种方式的优点是不会在主机上留下任何额外的文件，缺点是再次启动将会花费更多的时间来配置虚拟机。

当虚拟机*Supending 或 Halting* 后，任何时候你都可以通过`vagrant up` 来重新启动你的虚拟机，因为这个Vagrant环境已经被Vagrantfile配置过且所有数据都被保存到了本地。





##  十.虚拟机种类 

Vagrant支持*VirtualBox，VMware，Hper-v* [等等](https://www.vagrantup.com/docs/providers/)类型的虚拟机。一旦你安装了其中任意的一种虚拟机不必修改项目的Vagrantfile文件，只需在`vagrant up`后提供 `--provider`参数即可，比如使用*vmware* 虚拟机：

```bash
$ vagrant up --provider=vmware_fusion
```

指明启动虚拟机的类型后，Vagrant会自动重新配置，你可以使用ssh，destroy等命令来管理虚拟机。





## 十一.参考

【1】https://www.vagrantup.com/intro/getting-started/index.html


