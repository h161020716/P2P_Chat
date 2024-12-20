import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
import json
import os
import time
import wx
import queue
import threading
import subprocess

class ChatApp:
    def __init__(self, root, conn_to_client, conn_from_client):
        self.root = root
        self.root.title("登录界面")
        self.root.geometry("500x300")

        self.main_frame = None

        self.bg_photo = None  # 保存背景图片的引用
        self.image_refs = []
        
        self.username_entry = None
        self.username = None
        self.password_entry = None

        self.SendArea = None 
        self.ChatArea = None

        self.curUser = None
        self.userData = {}
        self.friendTree = None
        self.groups = None

        self.conn_to_client = conn_to_client
        self.conn_from_client = conn_from_client
        self.running = True
        

    def setup_login_ui(self):
        """设置登录界面"""
        # 设置背景图片
        bg_image = Image.open("front\\images\\loginbackground.jpg")  # 替换为你的图片路径
        bg_image = bg_image.resize((500, 300), Image.Resampling.LANCZOS)  # 调整图片大小
        self.bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = tk.Label(self.root, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # 表单区域
        form_width = 280
        form_height = 150
        form_x = (500 - form_width) // 2
        form_y = (300 - form_height) // 2

        # 用户名标签和输入框
        username_label = tk.Label(self.root, text="用户名:", font=("KaiTi", 13), bg="lightblue")
        username_label.place(x=form_x, y=form_y, width=80, height=30)

        self.username_entry = tk.Entry(self.root, font=("KaiTi", 13))
        self.username_entry.place(x=form_x + 90, y=form_y, width=200, height=30)

        # 密码标签和输入框
        password_label = tk.Label(self.root, text="密码:", font=("KaiTi", 13), bg="lightblue")
        password_label.place(x=form_x, y=form_y + 50, width=80, height=30)

        self.password_entry = tk.Entry(self.root, font=("KaiTi", 12), show="*")
        self.password_entry.place(x=form_x + 90, y=form_y + 50, width=200, height=30)

        # 登录按钮
        login_button = tk.Button(self.root, text="登录", font=("KaiTi", 13), command=self.login)
        login_button.place(x=form_x + 40, y=form_y + 100, width=80, height=30)

        # 注册按钮
        register_button = tk.Button(self.root, text="注册", font=("KaiTi", 13), command=self.register)
        register_button.place(x=form_x + 160, y=form_y + 100, width=80, height=30)

    def login(self):
        """处理登录逻辑"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            self.conn_to_client.send(f"LOGIN:{username};{password}")
            self.check_login_response()
        else:
            messagebox.showerror("登录失败", "用户名或密码不能为空！")
    
    def check_login_response(self):
        # 定期检查Client有没有返回消息
        if self.conn_from_client.poll():
            response = self.conn_from_client.recv()
            print(f"LOGIN APP: {response}")
            if response == "LOGIN_SUCCESS":

                username = self.username_entry.get()
                self.username = username
                new_user = {
                    "username": "'"+username+"'",
                    "password": "'"+self.password_entry.get()+"'",
                }

                if not os.path.exists(f"front/user/{username}.json"):
                    with open("front/user/admin.json", "w") as f:
                        json.dump(new_user, f)

                with open(f"front/user/{username}.json", "r", encoding="utf-8") as f:
                    user = json.load(f)

                self.groups = user['groups']
                for group in self.groups:
                    for user in group["group_members"]:
                        self.userData[user['id']] = {"host": "", "port": ""}
                print(f"用户数据: {self.userData}")
                self.root.withdraw()
                self.open_friend_window()
            else:
                messagebox.showerror("登录失败", "用户名或密码错误！")
        else:
            # 若暂无消息，100ms后再检查
            self.root.after(100, self.check_login_response)

    def register(self):
        """处理注册逻辑"""
        messagebox.showinfo("提示", "注册功能尚未实现")

    def on_closing(self):
        self.running = False
        self.root.destroy()
        self.main_frame.destroy()
    
    def send_msg(self, event=None):
        msg = self.SendArea.get("0.0", "end")  # 1.0 表示第一行第0列, end-1c 表示倒数第一个字符
        
        if not msg.strip():  # 去掉空白字符后检查消息是否为空
            messagebox.showerror("发送失败", "消息不能为空！")
            return  # 直接返回，不发送空消息
        
        self.ChatArea.configure(state=tk.NORMAL)
        print(f"slef.curUser: {self.curUser}")
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"
        self.ChatArea.insert("end", "我：" + timestamp, "green")
        self.ChatArea.insert("end", msg + "\n")
        self.conn_to_client.send(f"MSG:{self.curUser};{msg}")

        # 清空 SendArea 并将光标移动到开始位置
        self.SendArea.delete("1.0", "end")
        self.SendArea.insert("1.0", "")  # 确保光标在开始位置
        self.SendArea.mark_set("insert", "1.0")  # 显式设置光标到开始位置
        self.ChatArea.configure(state=tk.DISABLED)

    def insert_File(self, file_path, username):
        self.ChatArea.configure(state=tk.NORMAL)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"
        self.ChatArea.insert("end", f"{username}：" + timestamp, "green")
        self.ChatArea.insert("end", f"发送文件: {file_path}\n")
        self.ChatArea.configure(state=tk.DISABLED)
    
    def show_maessagboxe(self, nickname):
        messagebox.showinfo("聊天邀请", f"{nickname}向您发起聊天")

    def check_msg(self):
        if self.conn_from_client.poll():
            response = self.conn_from_client.recv()
            print(f"APP接受消息: {response}")
            if response.startswith("MSG:"):
                from_user, message = response.split(":")[1].split(";", 1)
                self.ChatArea.configure(state=tk.NORMAL)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"
                self.ChatArea.insert("end", from_user + "：" + timestamp)
                self.ChatArea.insert("end", message + "\n")
                self.ChatArea.configure(state=tk.DISABLED)
            elif response.startswith("CONN_SUCCESS:"):
                nickname, host, port = response.split(":")[1].split(";", 2)
                item_id = self.get_item_id_by_nickname(nickname)
                self.userData[item_id] = {"host": host, "port": int(port)}
                print(f"用户数据check_msg: {self.userData}")
                threading.Thread(target=self.show_maessagboxe, args=(nickname,)).start()
                self.conn_to_client.send(f"CONN:{host};{port}")
                self.curUser = nickname
            elif response.startswith("FILE|"):
                nickname, file_Path = response.split("|")[1].split(";", 1)
                self.ChatArea.configure(state=tk.NORMAL)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"
                self.ChatArea.insert("end", f"{nickname}：" + timestamp)
                self.ChatArea.insert("end", f"发送文件: {file_Path}\n")
                self.ChatArea.configure(state=tk.DISABLED)
            elif response.startswith("IMAGE|"):
                nickname, image_path = response.split("|")[1].split(";", 1)
                img = Image.open(image_path)
                img_resized = img.resize((128, 128), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img_resized)
                
                self.ChatArea.configure(state=tk.NORMAL)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"
                self.ChatArea.insert("end", f"{nickname}：" + timestamp, "green")
                self.ChatArea.image_create("end", image=img_tk)
                self.image_refs.append(img_tk)
                self.ChatArea.insert("end", "\n")
                self.ChatArea.configure(state=tk.DISABLED)
            else:
                print(f"接收到的位置格式: {response}")
            self.root.after(100, self.check_msg) 
        else:
            self.root.after(100, self.check_msg) # 100ms后再次检查

    def get_item_id_by_nickname(self, nickname):
        for group in self.groups:
            for member in group["group_members"]:
                if member["name"] == nickname:
                    return member["id"]
        return 0  # 如果找不到，返回 None

    def double_selected(self, event):
        item_id = self.friendTree.identify_row(event.y)

        if not item_id:
            return
        
        user_name = self.friendTree.item(item_id, "text")
        print(f"Selected user: {user_name}")
        print(f"当前的用户信息:{self.userData}")

        if item_id in self.userData:
            user_info = self.userData[item_id]
            print(f"{user_name} 在线\n")
            if user_info['host'] and user_info['port']:
                self.curUser = user_name
                self.conn_to_client.send(f"CONN:{user_info['host']};{user_info['port']}")
            else:
                messagebox.showerror("连接失败", "对方不在线！")
        else:
            messagebox.showerror("连接失败", "对方不在线！")
        
    def right_click(self, event):
        item_id = self.friendTree.identify_row(event.y)
        
        if not item_id:
            return
        
        user_name = self.friendTree.item(item_id, "text")
        print(f"右键选择: {user_name}")
        def save_changes():
            new_host = host_entry.get()
            new_port = port_entry.get()
            if item_id in self.userData:
                self.userData[item_id]['host'] = new_host
                self.userData[item_id]['port'] = int(new_port)
                edit_win.destroy()
                messagebox.showinfo("编辑成功", "用户信息已更新！")
            else:
                messagebox.showerror("编辑失败", "未找到用户信息！")

        user_name = self.friendTree.item(item_id, "text")
        user_info = self.userData.get(item_id, {"host": "", "port": ""})

        edit_win = tk.Toplevel(self.main_frame)
        edit_win.configure(bg="white")
        edit_win.title(f"编辑{user_name}信息")
        edit_win.geometry("300x150")
        edit_win.resizable(False, False)

        tk.Label(edit_win, text="主机地址:").place(x=30, y=30)
        host_entry = tk.Entry(edit_win)
        host_entry.insert(0, user_info["host"] or "")
        host_entry.place(x=100, y=30)

        tk.Label(edit_win, text="端口号:").place(x=30, y=60)
        port_entry = tk.Entry(edit_win)
        port_entry.insert(0, user_info["port"] or "")
        port_entry.place(x=100, y=60)

        save_button = tk.Button(edit_win, text="保存", command=save_changes)
        save_button.place(x=140, y=100)
    
    def upload_File(self):
    # 打开文件选择对话框
        select_file = filedialog.askopenfilename(
            title="选择要发送的文件",
            filetypes=[("所有文件", "*.*")]  # 可以根据需要调整文件类型过滤
        )
        print(select_file)
        if select_file:
            self.conn_to_client.send(f"FILE|{self.curUser};{select_file}")
            messagebox.showinfo("文件发送成功", "文件已发送！")

            self.ChatArea.configure(state=tk.NORMAL)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"
            self.ChatArea.insert("end", "我：" + timestamp, "green")
            self.ChatArea.insert("end", f"发送文件: {select_file}\n")
            self.ChatArea.insert("end", "\n")
            self.ChatArea.configure(state=tk.DISABLED)

        # self.conn_to_client.send(f"MSG:{self.curUser};发送文件: {select_file}")

    def upload_image(self):
        file_path = filedialog.askopenfilename(
            title="选择图片", 
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )

        if file_path:
            try:
                img = Image.open(file_path)
                img_resized = img.resize((128, 128), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img_resized)
                
                self.ChatArea.configure(state=tk.NORMAL)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"
                self.ChatArea.insert("end", "我：" + timestamp, "green")
                self.ChatArea.image_create("end", image=img_tk)
                self.image_refs.append(img_tk)
                self.ChatArea.insert("end", "\n")
                self.ChatArea.configure(state=tk.DISABLED)

                self.conn_to_client.send(f"IMAGE|{self.curUser};{file_path}")

            except Exception as e:
                print(f"图片上传失败: {e}")

    def open_friend_window(self):
        """打开用户聊天界面"""
        print(f"数据{self.userData}")

        ChatWin = tk.Toplevel(self.root)
        self.main_frame = ChatWin
        self.main_frame.title(f"{self.username} 聊天界面")
        self.main_frame.configure(bg="white")
        self.main_frame.protocol("WM_DELETE_WINDOW", self.on_closing)  #
        width = 1300
        height = 700
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        x = (screenwidth - width) / 2
        y = (screenheight - height) / 2

        ChatWin.geometry("%dx%d+%d+%d" % (width, height, x, y))
        ChatWin.resizable(False, False)

        FriendArea = tk.Frame(ChatWin, bg="white") # 好友区域
        FriendArea.place(x=10, y=35, width=310, height=650)
        friend_Tree = ttk.Treeview(FriendArea, height = 30,show="tree headings", columns=("ID", "Details")) 
        friend_Tree.heading("#0", text="好友分组")
        friend_Tree.heading("ID", text="编号")
        friend_Tree.heading("Details", text="备注")
        friend_Tree.column("ID", width=40)
        friend_Tree.column("Details", width=50)
        scrollbar = ttk.Scrollbar(FriendArea, orient="vertical", command=friend_Tree.yview)
        friend_Tree.configure(yscroll=scrollbar.set)
        friend_Tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        group_cnt = 0
        for group in self.groups:
            group_id = friend_Tree.insert("", group_cnt,  group["group_id"], text=group["group_name"], values=(""))
            cnt = 0
            for member in group['group_members']:
                friend_Tree.insert(group_id, cnt, member['id'], text=member['name'], values=(member['values'][0], member['values'][1]))
                cnt += 1
            group_cnt += 1

        friend_Tree.bind('<Double-1>', self.double_selected)
        friend_Tree.bind('<Button-3>', self.right_click)
        self.friendTree = friend_Tree

        btn_frame = tk.Frame(ChatWin) # 按钮区域
        btn_frame.place(x=0, y=0, width=1300, height=35)
        tk.Button(btn_frame, text="好友").place(x=10, y=2, width=60)
        tk.Button(btn_frame, text="添加好友").place(x=80, y=2, width=60)
        tk.Button(btn_frame, text="新建标签").place(x=150, y=2, width=60)

        ChatArea = tk.Frame(ChatWin) # 聊天区域
        ChatArea.place(x=320, y=35, width=970, height=650)

        button_height = 24

        MsgArea = tk.Text(ChatArea, bg="white", font=("KaiTi", 12), state=tk.DISABLED) 
        MsgArea.tag_configure("green", foreground='#008C00') # 设置tag, 用于标记消息的颜色
        MsgArea.place(x=0, y=0, width=970, height=650*2/3 - button_height) 
        self.ChatArea = MsgArea 

        ButtonArea = tk.Frame(ChatArea) # 按钮区域
        ButtonArea.place(x=0, y=650*2/3 - button_height, width=970, height=button_height)
        tk.Button(ButtonArea, text="发送文件", command=self.upload_File).place(x=0, y=2, width=60, height=20)
        tk.Button(ButtonArea, text="发送图片", command=self.upload_image).place(x=70, y=2, width=60, height=20)
        tk.Button(ButtonArea, text="语音").place(x=140, y=2, width=60, height=20)
        tk.Button(ButtonArea, text="视频").place(x=210, y=2, width=60, height=20)

        SendArea = tk.Text(ChatArea, bg="white", font=("KaiTi", 12))
        self.SendArea = SendArea
        SendArea.bind("<Return>", self.send_msg) # 绑定回车键发送消息
        Textscrollbar = tk.Scrollbar(SendArea)
        Textscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        Textscrollbar.config(command=SendArea.yview)
        SendArea.config(yscrollcommand=Textscrollbar.set)
        SendArea.place(x=0, y=650*2/3, width=970, height=650/3 - button_height)

        EnterArea = tk.Frame(ChatArea)
        EnterArea.place(x=0, y=650 - button_height, width=970, height=button_height)
        tk.Button(EnterArea, text="发送", command=self.send_msg).place(x=910, y=0, width=60, height=button_height)

        self.check_msg()

# 启动主程序
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    app.start()
    root.mainloop() 
