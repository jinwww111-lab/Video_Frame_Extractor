import cv2
import os
import tkinter as tk
from tkinter import filedialog, messagebox, Scrollbar, Canvas, Frame, Button, Label, Entry, Toplevel
from PIL import Image, ImageTk

# ------------------- 提取帧函数 -------------------
def extract_frames(video_path, interval):
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_id = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_id % interval == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        frame_id += 1
    cap.release()
    return frames

# ------------------- 按钮功能 -------------------
def select_video():
    global video_path
    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi"), ("All files", "*.*")])
    if file_path:
        video_path = file_path
        file_label.config(text=f"已选择视频: {file_path}")

def extract_and_display():
    global frames, frame_thumbnails, frame_labels
    if not video_path:
        messagebox.showerror("错误", "请先选择视频文件！")
        return
    try:
        interval = int(interval_entry.get())
    except ValueError:
        messagebox.showerror("错误", "请输入有效的帧间隔数值！")
        return

    # 提取帧
    frames.clear()
    frames.extend(extract_frames(video_path, interval))
    if not frames:
        messagebox.showwarning("提示", "未提取到任何帧！")
        return

    # 清空旧缩略图
    for widget in frame_container.winfo_children():
        widget.destroy()

    frame_thumbnails.clear()
    frame_labels.clear()
    selected_indices.clear()

    thumb_size = 160
    for i, frame in enumerate(frames):
        img = Image.fromarray(frame)
        img.thumbnail((thumb_size, thumb_size))
        imgtk = ImageTk.PhotoImage(img)
        frame_thumbnails.append(imgtk)

        lbl = Label(frame_container, image=imgtk, borderwidth=2, relief="solid")
        lbl.grid(row=i // 5, column=i % 5, padx=5, pady=5)
        frame_labels.append(lbl)

        def toggle_select(event, idx=i, label=lbl):
            if idx in selected_indices:
                selected_indices.remove(idx)
                label.config(highlightthickness=0, relief="solid")
            else:
                selected_indices.add(idx)
                label.config(highlightbackground="red", highlightthickness=2, relief="ridge")

        lbl.bind("<Button-1>", toggle_select)
        lbl.bind("<Double-Button-1>", lambda e, idx=i: open_preview(idx))

def save_selected():
    if not selected_indices:
        messagebox.showinfo("提示", "你还没有选择任何图片！")
        return

    output_dir = filedialog.askdirectory(title="选择保存文件夹")
    if not output_dir:
        return

    for i in selected_indices:
        img_bgr = cv2.cvtColor(frames[i], cv2.COLOR_RGB2BGR)
        filename = os.path.join(output_dir, f"frame_{i:05d}.jpg")
        cv2.imwrite(filename, img_bgr)

    messagebox.showinfo("完成", f"已保存 {len(selected_indices)} 张图片到\n{output_dir}")

# ------------------- 放大预览窗口 -------------------
def open_preview(start_idx):
    top = Toplevel(root)
    top.title(f"预览 - 帧 {start_idx}/{len(frames)-1}")

    MAX_WIDTH, MAX_HEIGHT = 800, 600
    current_index = [start_idx]

    img_label = Label(top)
    img_label.pack(pady=5)

    def show_image(idx):
        img = Image.fromarray(frames[idx])
        w_ratio = min(MAX_WIDTH / img.width, 1.0)
        h_ratio = min(MAX_HEIGHT / img.height, 1.0)
        scale_ratio = min(w_ratio, h_ratio)
        disp_width = int(img.width * scale_ratio)
        disp_height = int(img.height * scale_ratio)
        img_resized = img.resize((disp_width, disp_height), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(img_resized)
        img_label.imgtk = imgtk
        img_label.config(image=imgtk)
        top.title(f"预览 - 帧 {idx}/{len(frames)-1}" + ("（已选中）" if idx in selected_indices else ""))

    def prev_frame():
        if current_index[0] > 0:
            current_index[0] -= 1
            show_image(current_index[0])

    def next_frame():
        if current_index[0] < len(frames) - 1:
            current_index[0] += 1
            show_image(current_index[0])

    def select_this_frame():
        i = current_index[0]
        lbl = frame_labels[i]
        if i in selected_indices:
            selected_indices.remove(i)
            lbl.config(highlightthickness=0, relief="solid")
        else:
            selected_indices.add(i)
            lbl.config(highlightbackground="red", highlightthickness=2, relief="ridge")
        show_image(i)  # 更新标题

    btn_frame = Frame(top)
    btn_frame.pack(pady=5)

    prev_btn = Button(btn_frame, text="上一张", command=prev_frame)
    prev_btn.pack(side="left", padx=5)
    select_btn = Button(btn_frame, text="选中此帧", command=select_this_frame)
    select_btn.pack(side="left", padx=5)
    next_btn = Button(btn_frame, text="下一张", command=next_frame)
    next_btn.pack(side="left", padx=5)

    show_image(start_idx)

# ------------------- UI -------------------
root = tk.Tk()
root.title("视频帧提取与选择保存")

video_path = ""
frames = []
frame_thumbnails = []
frame_labels = []
selected_indices = set()

# 选择视频
file_label = Label(root, text="未选择视频")
file_label.pack()
select_button = Button(root, text="选择视频文件", command=select_video)
select_button.pack(pady=5)

# 帧间隔输入
Label(root, text="每隔多少帧提取一张:").pack()
interval_entry = Entry(root)
interval_entry.insert(0, "10")
interval_entry.pack(pady=5)

# 提取按钮
extract_button = Button(root, text="提取并显示帧", command=extract_and_display)
extract_button.pack(pady=5)

# 滚动区域
canvas = Canvas(root, width=850, height=500)
scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

frame_container = Frame(canvas)
canvas.create_window((0, 0), window=frame_container, anchor="nw")

def on_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
frame_container.bind("<Configure>", on_configure)

# 保存按钮居中
save_button = Button(root, text="保存选中图片", command=save_selected)
save_button.pack(pady=10)

root.mainloop()





