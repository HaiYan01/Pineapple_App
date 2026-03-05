# Pineapple_App

1. 环境准备
无论您使用 Windows 还是 Mac，首先需要安装 Python 和必要的依赖库。

1.1 安装 Python
Windows: 访问 Python官网 下载 Python 3.9 或更高版本。安装时务必勾选 Add Python to PATH。
Mac: 推荐使用 Homebrew 安装，终端运行：brew install python。或者直接在官网下载安装包。

1.2 安装依赖库
打开终端 或 命令提示符/PowerShell，运行以下命令安装所有需要的第三方库：
pip install customtkinter pandas matplotlib fpdf requests pyinstaller
说明：
customtkinter: 用于现代化的界面。
pandas: 用于数据处理和导出。
matplotlib: 用于生成统计图表。
fpdf: 用于导出 PDF 文件。
requests: 用于 AI 功能（仅 Windows 版需要）。
pyinstaller: 用于打包成可执行文件。

2. 运行源代码
Windows 用户
将代码文件保存为 pineapple_app For Windows.py。
双击文件运行，或在命令行中执行：
python "pineapple_app For Windows.py"

Mac 用户
将代码文件保存为 pineapple_app For Mac.py。
打开终端，导航到文件所在目录，执行：
python3 "pineapple_app For Mac.py"

3. 打包为 Windows 应用
我们将使用 pyinstaller 将 Python 脚本打包成独立的 .exe 文件，这样用户无需安装 Python 环境即可运行。

步骤 1: 准备图标文件 (可选)
如果需要给软件一个图标，请准备一个 .ico 格式的图标文件（例如 icon.ico），放在与 .py 文件相同的目录下。

步骤 2: 执行打包命令
打开 PowerShell 或 CMD，进入代码所在目录，执行以下命令：
pyinstaller --noconsole --onefile --name "菠萝皮登记系统" "pineapple_app For Windows.py"
参数解释：
--noconsole: 运行时不显示黑色的命令行窗口（推荐用于 GUI 程序）。
--onefile: 将所有依赖打包成一个单独的 .exe 文件，方便分发。
--name "菠萝皮登记系统": 生成的 exe 文件名称。
(可选) --icon=icon.ico: 如果你有图标，加上这个参数。

步骤 3: 获取文件
打包完成后，会在当前目录下生成一个 dist 文件夹，里面就是 菠萝皮登记系统.exe。您可以将其发送给其他人直接使用。


4. 打包为 macOS 应用
Mac 的打包过程与 Windows 类似，但需要注意权限和架构问题。

步骤 1: 执行打包命令
打开终端，进入代码所在目录，执行：
pyinstaller --noconsole --onefile --windowed --name "菠萝皮登记系统" "pineapple_app For Mac.py"
参数解释：
--windowed (等同于 -w): Mac 特有参数，防止程序启动时出现终端窗口。
其他参数同 Windows。

步骤 2: 找到并运行 App
打包完成后，在 dist 文件夹中会生成 菠萝皮登记系统.app。
首次运行：双击 App 可能会提示“无法打开，因为它来自身份不明的开发者”。
解决方法：右键点击 App -> 选择“打开” -> 在弹出的对话框中点击“打开”。
或者在“系统设置” -> “隐私与安全性”中手动允许运行。
进阶：添加图标
如果你有 .icns 格式的图标文件，可以使用 --icon=icon.icns 参数。

5. 重要注意事项
1. 关于字体
Windows: 代码默认调用 Microsoft YaHei (微软雅黑)。Windows 系统自带，无需额外处理。
Mac: 代码默认调用 PingFang SC (苹方)。Mac 系统自带，无需额外处理。
如果打包后在其他电脑上字体显示乱码或方块，通常是对方系统缺失该字体，代码已包含容错处理（会回退到默认字体），但界面美观度可能会受影响。
2. 数据库位置
程序运行后，会自动在用户的“文档”文件夹下创建数据库文件：
Windows: C:\Users\用户名\Documents\pineapple_data.db
Mac: /Users/用户名/Documents/pineapple_data.db
注意：如果需要迁移数据，只需备份该 .db 文件并放入新电脑的对应位置即可。
