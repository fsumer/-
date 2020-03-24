"""
我现在即想执行命令又想上传下载文件并且多次执行
yum install ansible
yum install redis
yum install redis
upload

单链接下完成多部操作
"""
# 下面写的类 你只要只要是想通过paramiko链接服务器都可以使用
import paramiko


class SSHProxy(object):
    def __init__(self, hostname, port, username, password):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.transport = None

    def open(self):  # 给对象赋值一个上传下载文件对象连接
        self.transport = paramiko.Transport((self.hostname, self.port))
        self.transport.connect(username=self.username, password=self.password)

    def command(self, cmd):  # 正常执行命令的连接  至此对象内容就既有执行命令的连接又有上传下载链接
        ssh = paramiko.SSHClient()
        ssh._transport = self.transport

        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read()
        return result

    def upload(self, local_path, remote_path):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.put(local_path, remote_path)
        sftp.close()

    def close(self):
        self.transport.close()

    def __enter__(self):  # 对象执行with上下文会自动触发
        #
        # print('触发了enter')
        self.open()
        return self  # 这里发挥上面with语法内的as后面拿到的就是什么
        # return 123


    def __exit__(self, exc_type, exc_val, exc_tb):  # with执行结束自动触发
        # print('触发了exit')
        self.close()
"""
上面这个类在使用的时候 需要先执行open方法
obj = SSHProxy()
obj.open()  文件对象 链接服务器

obj.command()
obj.command()
obj.upload()
obj.upload()

obj.close()  关闭链接


文件操作
f = open()

f.write()
f.read()

f.close()

with上下文管理
with open() as f:
    ...
"""

# 对象默认是不支持with语法的
# obj = SSHProxy('172.16.219.173',22,'root','jason123')
# with obj as f:
#     # print('进入with代码块')
#     print(f)
if __name__ == '__main__':

    with SSHProxy('172.16.219.173',22,'root','jason123') as ssh:
        ssh.command()
        ssh.command()
        ssh.command()
        ssh.upload()


"""
面试题
请在Context类中添加代码完成该类的实现
class Context:
    pass

with Context() as ctx:
    ctx.do_something()
"""
# class Context:
#     def __enter__(self):
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         pass
#
#     def do_something(self):
#         pass
#
# with Context() as ctx:
#     ctx.do_something()