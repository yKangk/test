import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from database import init_db, execute, fetchall
from data_parser import DataFile


class LabNotebookApp:
    def __init__(self, master):
        self.master = master
        master.title("实验记录本")
        self.create_widgets()
        init_db()
        self.load_projects()

    def create_widgets(self):
        self.project_frame = ttk.LabelFrame(self.master, text="项目")
        self.project_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

        self.project_list = tk.Listbox(self.project_frame)
        self.project_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.project_list.bind('<<ListboxSelect>>', self.on_project_select)

        self.proj_btn_frame = tk.Frame(self.project_frame)
        self.proj_btn_frame.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(self.proj_btn_frame, text="新建", command=self.add_project).pack(fill=tk.X)
        ttk.Button(self.proj_btn_frame, text="删除", command=self.delete_project).pack(fill=tk.X)
        ttk.Button(self.proj_btn_frame, text="汇总", command=self.summary_project).pack(fill=tk.X)

        self.exp_frame = ttk.LabelFrame(self.master, text="实验记录")
        self.exp_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.exp_list = tk.Listbox(self.exp_frame, width=40)
        self.exp_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.exp_list.bind('<<ListboxSelect>>', self.on_experiment_select)

        self.exp_btn_frame = tk.Frame(self.exp_frame)
        self.exp_btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(self.exp_btn_frame, text="新建", command=self.add_experiment).pack(fill=tk.X)
        ttk.Button(self.exp_btn_frame, text="删除", command=self.delete_experiment).pack(fill=tk.X)
        ttk.Button(self.exp_btn_frame, text="上传数据", command=self.upload_data).pack(fill=tk.X)
        ttk.Button(self.exp_btn_frame, text="查看数据", command=self.view_data).pack(fill=tk.X)

        self.master.columnconfigure(1, weight=1)
        self.master.rowconfigure(0, weight=1)

    def load_projects(self):
        self.project_list.delete(0, tk.END)
        projects = fetchall("SELECT id, name FROM projects")
        self.projects = {name: pid for pid, name in projects}
        for pid, name in projects:
            self.project_list.insert(tk.END, name)

    def on_project_select(self, event=None):
        selection = self.project_list.curselection()
        if not selection:
            return
        name = self.project_list.get(selection[0])
        pid = self.projects.get(name)
        self.load_experiments(pid)

    def load_experiments(self, project_id):
        self.exp_list.delete(0, tk.END)
        if project_id is None:
            return
        exps = fetchall("SELECT id, name FROM experiments WHERE project_id=?", (project_id,))
        self.experiments = {name: eid for eid, name in exps}
        for eid, name in exps:
            self.exp_list.insert(tk.END, name)

    def add_project(self):
        name = simple_input("项目名称")
        if name:
            execute("INSERT INTO projects (name) VALUES (?)", (name,))
            self.load_projects()

    def delete_project(self):
        selection = self.project_list.curselection()
        if not selection:
            return
        name = self.project_list.get(selection[0])
        pid = self.projects.get(name)
        if messagebox.askyesno("确认", f"删除项目 {name}?"):
            execute("DELETE FROM projects WHERE id=?", (pid,))
            execute("DELETE FROM experiments WHERE project_id=?", (pid,))
            self.load_projects()
            self.exp_list.delete(0, tk.END)

    def summary_project(self):
        selection = self.project_list.curselection()
        if not selection:
            return
        name = self.project_list.get(selection[0])
        pid = self.projects.get(name)
        exp_count = fetchall("SELECT COUNT(*) FROM experiments WHERE project_id=?", (pid,))[0][0]
        files = fetchall(
            "SELECT file_path, file_type FROM data_files WHERE experiment_id IN (SELECT id FROM experiments WHERE project_id=?)",
            (pid,)
        )
        file_count = len(files)
        messagebox.showinfo(
            "汇总",
            f"项目: {name}\n实验数量: {exp_count}\n数据文件数量: {file_count}",
        )

    def add_experiment(self):
        selection = self.project_list.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择项目")
            return
        project_name = self.project_list.get(selection[0])
        project_id = self.projects.get(project_name)
        name = simple_input("实验名称")
        if not name:
            return
        fields = simple_input("实验自定义字段(JSON)") or "{}"
        execute(
            "INSERT INTO experiments (project_id, name, custom_fields) VALUES (?, ?, ?)",
            (project_id, name, fields)
        )
        self.load_experiments(project_id)

    def delete_experiment(self):
        project_sel = self.project_list.curselection()
        exp_sel = self.exp_list.curselection()
        if not project_sel or not exp_sel:
            return
        project_id = self.projects.get(self.project_list.get(project_sel[0]))
        exp_name = self.exp_list.get(exp_sel[0])
        exp_id = self.experiments.get(exp_name)
        if messagebox.askyesno("确认", f"删除实验 {exp_name}?"):
            execute("DELETE FROM experiments WHERE id=?", (exp_id,))
            execute("DELETE FROM data_files WHERE experiment_id=?", (exp_id,))
            self.load_experiments(project_id)

    def upload_data(self):
        project_sel = self.project_list.curselection()
        exp_sel = self.exp_list.curselection()
        if not project_sel or not exp_sel:
            return
        exp_name = self.exp_list.get(exp_sel[0])
        exp_id = self.experiments.get(exp_name)
        path = filedialog.askopenfilename(title="选择数据文件")
        if not path:
            return
        ext = os.path.splitext(path)[1].lower().strip('.')
        execute(
            "INSERT INTO data_files (experiment_id, file_path, file_type) VALUES (?, ?, ?)",
            (exp_id, path, ext)
        )
        messagebox.showinfo("上传", "数据已上传")

    def view_data(self):
        exp_sel = self.exp_list.curselection()
        if not exp_sel:
            return
        exp_name = self.exp_list.get(exp_sel[0])
        exp_id = self.experiments.get(exp_name)
        files = fetchall("SELECT id, file_path, file_type FROM data_files WHERE experiment_id=?", (exp_id,))
        if not files:
            messagebox.showinfo("提示", "没有数据文件")
            return
        info = []
        for fid, path, ftype in files:
            try:
                data = DataFile(path, ftype)
                data.parse()
                info.append(f"{os.path.basename(path)}: {len(data.data)} 行")
            except Exception as e:
                info.append(f"{os.path.basename(path)}: 解析失败 {e}")
        messagebox.showinfo("数据文件", "\n".join(info))


def simple_input(title: str) -> str:
    popup = tk.Toplevel()
    popup.title(title)
    tk.Label(popup, text=title).pack()
    entry = tk.Entry(popup)
    entry.pack()
    result = []

    def on_ok():
        result.append(entry.get())
        popup.destroy()

    ttk.Button(popup, text="确定", command=on_ok).pack()
    popup.wait_window()
    return result[0] if result else None


def main():
    root = tk.Tk()
    app = LabNotebookApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
