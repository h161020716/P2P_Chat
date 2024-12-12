import tkinter as tk
from tkinter import ttk
import pickle
import json

with open("font/user/usr.json", "r") as f:
    user = json.load(f)
    username = user["username"]
    password = user["password"]

chatWin = tk.Tk()
chatWin.title("聊天界面")



friend_Tree = ttk.Treeview(chatWin, height=40, show="tree")
friend_Tree.place(x=10, y=30)


fri_tree1 = friend_Tree.insert('', 0, 'frist', text='家人', values=("1"))
fri_tree1_1 = friend_Tree.insert(fri_tree1, 0, '001', text='主机2', values=("2"))
fri_tree2 = friend_Tree.insert('', 1, 'second', text='同事', values=("4"))
fri_tree2_1 = friend_Tree.insert(fri_tree2, 0, 'admin', text='女朋友002', values=("5"))


        # def double_selected(event):
        #     for item in friend_Tree.selection():
        #         item_text = friend_Tree.item(item, "text")
        #         chat_usr = {
        #             'usrname': username,
        #             'age': '19',  # 示例数据
        #             'chatname': item_text
        #         }
        #         try:
        #             with open('usr.json', 'w') as wf:
        #                 json.dump(chat_usr, wf)
        #             print(f"Saved chat user info: {chat_usr}")
        #         except Exception as e:
        #             print(f"Failed to save chat user info: {e}")

        # friend_Tree.bind('<Double-1>', double_selected)
 
 
friend_Tree.bind('<Double-1>', double_selected)
friend_Tree.pack(expand=True, fill=tk.X)
 
# 好友按钮
fri_btn = tk.Button(text="好友")
fri_btn.place(x=10, y=2)
 
# 群按钮
cla_btn = tk.Button(text="群聊")
cla_btn.place(x=70, y=2)
 
# 添加好友
into_fri_btn = tk.Button(text="添加好友")
into_fri_btn.place(x=130, y=2)
 
# 搜索好友
l1 = tk.Label(text="查找好友:")
l1.place(x=10, y=771)
 
# 搜索框
e1 = tk.Entry(width=12)
e1.place(x=80, y=770)
 
# 搜索按钮
search_btn = tk.Button(text="搜索")
search_btn.place(x=190, y=770)
# 菜单
menu_btn = tk.Button(text="设置")
menu_btn.place(x=256, y=770)
 
chatWin.mainloop()
