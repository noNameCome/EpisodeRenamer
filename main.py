# RenaMatcher - 영상/자막 파일명 일괄 변경 프로그램
import sys
import os
import re
import tkinter as tk
from tkinter import messagebox, ttk
import registry
import renamer

# 드래그앤드롭
try:
  from tkinterdnd2 import TkinterDnD, DND_FILES
  _BASE = TkinterDnD.Tk
  USE_DND = True
except ImportError:
  _BASE = tk.Tk
  USE_DND = False

# ── 다크 테마 색상 ──
BG       = "#0f1117"
SURFACE  = "#1a1d27"
SURFACE2 = "#22263a"
BORDER   = "#2e334d"
ACCENT   = "#6c63ff"
ACCENT_HV= "#7d76ff"
TEXT     = "#ffffff"
SUBTEXT  = "#8b8fa8"
VIDEO    = "#4f8ef7"
VIDEO_H  = "#293656"
VIDEO_B  = "#2d4069"
SUB_C    = "#f7954f"
SUB_H    = "#42373d"
SUB_B    = "#57423f"
DANGER   = "#e05c5c"
DANGER_H = "#422a32"
SUCCESS  = "#4caf87"
MODE_ACT = "#2d2f58"
SEL_BG   = "#3d3a6e"
SEL_FG   = "#a89fff"
FONT     = ("Segoe UI", 10)
FONT_B   = ("Segoe UI", 10, "bold")
FONT_H   = ("Segoe UI", 13, "bold")
FONT_SM  = ("Segoe UI", 9)
FONT_XS  = ("Segoe UI", 8)


def get_icon_ico():
  if getattr(sys, 'frozen', False):
    base = sys._MEIPASS
  else:
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
  ico_path = os.path.join(base, 'icon.ico')
  if not os.path.exists(ico_path) and not getattr(sys, 'frozen', False):
    png_path = os.path.join(base, 'icon.png')
    if os.path.exists(png_path):
      try:
        from PIL import Image
        img = Image.open(png_path)
        img.save(ico_path, format='ICO', sizes=[(256,256),(64,64),(32,32),(16,16)])
      except Exception:
        return None
  return ico_path if os.path.exists(ico_path) else None


def hover(widget, enter_bg, leave_bg, enter_fg=None, leave_fg=None):
  # 마우스 오버 효과
  def _enter(e):
    widget.config(bg=enter_bg)
    if enter_fg: widget.config(fg=enter_fg)
  def _leave(e):
    widget.config(bg=leave_bg)
    if leave_fg: widget.config(fg=leave_fg)
  widget.bind("<Enter>", _enter)
  widget.bind("<Leave>", _leave)


class PreviewDialog(tk.Toplevel):
  # 미리보기 다이얼로그
  def __init__(self, parent, items):
    super().__init__(parent)
    self.title("변경 미리보기")
    self.configure(bg=SURFACE)
    self.resizable(True, True)
    self.minsize(700, 420)
    self.confirmed = False
    self.transient(parent)
    self.grab_set()

    # 헤더
    h = tk.Frame(self, bg=BG, pady=12)
    h.pack(fill="x")
    tk.Label(h, text="변경 미리보기", font=FONT_H, bg=BG, fg=TEXT).pack(side="left", padx=18)
    tk.Label(h, text=f"총 {len(items)}개", font=FONT_SM, bg=BG, fg=ACCENT).pack(side="right", padx=18)
    tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    # 테이블
    tree_wrap = tk.Frame(self, bg=SURFACE)
    tree_wrap.pack(fill="both", expand=True, padx=14, pady=12)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Preview.Treeview",
                    background=SURFACE2, foreground=TEXT,
                    fieldbackground=SURFACE2, font=FONT_SM, rowheight=26)
    style.configure("Preview.Treeview.Heading",
                    background=BG, foreground=SUBTEXT,
                    font=FONT_B, relief="flat")
    style.map("Preview.Treeview",
              background=[("selected", SEL_BG)],
              foreground=[("selected", SEL_FG)])

    cols = ("before", "arrow", "after")
    tv = ttk.Treeview(tree_wrap, columns=cols, show="headings",
                      style="Preview.Treeview")
    tv.heading("before", text="변경 전")
    tv.heading("arrow",  text="")
    tv.heading("after",  text="변경 후")
    tv.column("before", width=300, anchor="w")
    tv.column("arrow",  width=30,  anchor="center")
    tv.column("after",  width=300, anchor="w")

    sb_y = ttk.Scrollbar(tree_wrap, orient="vertical",   command=tv.yview,
                         style="Dark.Vertical.TScrollbar")
    sb_x = ttk.Scrollbar(tree_wrap, orient="horizontal", command=tv.xview,
                         style="Dark.Horizontal.TScrollbar")
    tv.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
    sb_y.pack(side="right",  fill="y")
    sb_x.pack(side="bottom", fill="x")
    tv.pack(fill="both", expand=True)

    for old, new in items:
      tag = "same" if old == new else "change"
      tv.insert("", "end", values=(old, "→", new), tags=(tag,))
    tv.tag_configure("same",   foreground=SUBTEXT)
    tv.tag_configure("change", foreground=TEXT)

    # 버튼
    tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
    btn_row = tk.Frame(self, bg=SURFACE, pady=12)
    btn_row.pack(fill="x")

    cancel = tk.Button(btn_row, text="취소", command=self._cancel,
                       bg=SURFACE2, fg=SUBTEXT, font=FONT_B,
                       relief="flat", bd=0, cursor="hand2", padx=20, pady=8,
                       activebackground=BORDER, activeforeground=TEXT)
    cancel.pack(side="right", padx=(8,18))
    hover(cancel, BORDER, SURFACE2, TEXT, SUBTEXT)

    confirm = tk.Button(btn_row, text="확인 – 일괄수정", command=self._confirm,
                        bg=ACCENT, fg="#ffffff", font=FONT_B,
                        relief="flat", bd=0, cursor="hand2", padx=20, pady=8,
                        activebackground=ACCENT_HV, activeforeground="#ffffff")
    confirm.pack(side="right")
    hover(confirm, ACCENT_HV, ACCENT)

    # 창 중앙 배치
    self.update_idletasks()
    px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
    py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
    self.geometry(f"+{px}+{py}")
    self.wait_window()

  def _confirm(self):
    self.confirmed = True
    self.destroy()

  def _cancel(self):
    self.confirmed = False
    self.destroy()


class App(_BASE):
  def __init__(self):
    super().__init__()
    self.title("RenaMatcher")
    self.configure(bg=BG)
    self.resizable(True, True)
    self.minsize(800, 600)
    self.backup = {}
    self.folder_path = sys.argv[1] if len(sys.argv) > 1 else ""
    self._mode_btns = []

    ico = get_icon_ico()
    if ico:
      try:
        self.iconbitmap(ico)
      except Exception:
        pass

    # ttk 다크 스크롤바 스타일 전역 설정
    s = ttk.Style()
    s.theme_use("clam")
    for orient in ("Vertical", "Horizontal"):
      s.configure(f"Dark.{orient}.TScrollbar",
                  background=BORDER, troughcolor=SURFACE2,
                  arrowcolor=SUBTEXT, bordercolor=SURFACE2,
                  darkcolor=BORDER, lightcolor=BORDER)
      s.map(f"Dark.{orient}.TScrollbar",
            background=[("active", SUBTEXT), ("disabled", BORDER)])

    self._build_ui()

    if USE_DND:
      self._setup_dnd()

    if self.folder_path:
      self._load_files()

  def _setup_dnd(self):
    # 드래그앤드롭 설정
    self.drop_target_register(DND_FILES)
    self.dnd_bind('<<Drop>>', self._on_drop)

  def _on_drop(self, event):
    # 드롭된 경로 처리
    path = event.data.strip().strip('{}')
    if os.path.isdir(path):
      self.folder_path = path
    elif os.path.isfile(path):
      self.folder_path = os.path.dirname(path)
    else:
      return
    self._load_files()
    self._status("드롭으로 폴더 로드됨", SUCCESS)

  def _build_ui(self):
    # ── 타이틀 바 ──
    tb = tk.Frame(self, bg=BG)
    tb.pack(fill="x")

    logo = tk.Frame(tb, bg=BG)
    logo.pack(side="left", padx=18, pady=11)
    tk.Label(logo, text="Rena",    font=("Segoe UI",14,"bold"), bg=BG, fg=ACCENT).pack(side="left")
    tk.Label(logo, text="Matcher", font=("Segoe UI",14,"bold"), bg=BG, fg=TEXT).pack(side="left")

    # 장식용 macOS 스타일 점
    dots = tk.Frame(tb, bg=BG)
    dots.pack(side="right", padx=18)
    for color in ["#ff5f57","#febc2e","#28c840"]:
      c = tk.Canvas(dots, width=13, height=13, bg=BG, highlightthickness=0)
      c.create_oval(1,1,12,12, fill=color, outline="")
      c.pack(side="left", padx=3, pady=11)

    tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    # ── 헤더 ──
    hdr = tk.Frame(self, bg=SURFACE)
    hdr.pack(fill="x")

    path_f = tk.Frame(hdr, bg=SURFACE2,
                      highlightthickness=1, highlightbackground=BORDER)
    path_f.pack(side="left", padx=18, pady=10, fill="x", expand=True)
    tk.Label(path_f, text="📁", font=FONT_SM, bg=SURFACE2, fg=SUBTEXT).pack(side="left", padx=(8,4), pady=6)
    self.lbl_path = tk.Label(path_f,
                             text=self.folder_path or "폴더를 우클릭 또는 창에 드래그하여 선택하세요",
                             font=FONT_SM, bg=SURFACE2, fg=SUBTEXT, anchor="w")
    self.lbl_path.pack(side="left", fill="x", expand=True, pady=6, padx=(0,10))

    reg_f = tk.Frame(hdr, bg=SURFACE)
    reg_f.pack(side="right", padx=18, pady=10)

    add = tk.Button(reg_f, text="⊕ 레지스트리 등록", command=self._reg_add,
                    bg=ACCENT, fg="#fff", font=FONT_SM,
                    relief="flat", bd=0, cursor="hand2", padx=14, pady=7,
                    activebackground=ACCENT_HV, activeforeground="#fff")
    add.pack(side="left")
    hover(add, ACCENT_HV, ACCENT)

    rem = tk.Button(reg_f, text="⊖ 레지스트리 제거", command=self._reg_remove,
                    bg=SURFACE, fg=DANGER, font=FONT_SM,
                    relief="flat", bd=0, cursor="hand2", padx=14, pady=6,
                    highlightthickness=1, highlightbackground=DANGER,
                    activebackground=DANGER_H, activeforeground=DANGER)
    rem.pack(side="left", padx=(8,0))
    hover(rem, DANGER_H, SURFACE)

    tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    # ── 본문 ──
    body = tk.Frame(self, bg=BG)
    body.pack(fill="both", expand=True, padx=20, pady=16)

    # 파일 패널 (좌/우)
    panels = tk.Frame(body, bg=BG)
    panels.pack(fill="both", expand=True)
    panels.columnconfigure(0, weight=1)
    panels.columnconfigure(1, weight=1)
    panels.rowconfigure(0, weight=1)

    self.lst_video, self.vid_badge = self._make_panel(
      panels, "비디오 파일", VIDEO, VIDEO_H, VIDEO_B, 0)
    self.lst_sub, self.sub_badge = self._make_panel(
      panels, "자막 파일", SUB_C, SUB_H, SUB_B, 1)

    # ── 옵션 섹션 ──
    opt = tk.Frame(body, bg=SURFACE2,
                   highlightthickness=1, highlightbackground=BORDER)
    opt.pack(fill="x", pady=(0,14))
    opt_in = tk.Frame(opt, bg=SURFACE2)
    opt_in.pack(fill="x", padx=18, pady=14)

    # 모드 라벨
    tk.Label(opt_in, text="변경  모드", font=("Segoe UI",8,"bold"),
             bg=SURFACE2, fg=SUBTEXT).pack(anchor="w", pady=(0,8))

    # 모드 토글 버튼
    mode_row = tk.Frame(opt_in, bg=SURFACE2)
    mode_row.pack(fill="x", pady=(0,12))
    self.mode_var = tk.StringVar(value="video")
    for val, lbl in [("video","▶  비디오 기준"),("sub","≡  자막 기준"),("rule","✎  이름규칙")]:
      active = val == "video"
      b = tk.Button(mode_row, text=lbl,
                    bg=MODE_ACT if active else SURFACE2,
                    fg=ACCENT if active else SUBTEXT,
                    font=FONT_SM, relief="flat", bd=0, cursor="hand2",
                    padx=16, pady=7,
                    highlightthickness=1,
                    highlightbackground=ACCENT if active else BORDER,
                    activebackground=MODE_ACT, activeforeground=ACCENT)
      b.config(command=lambda v=val: self._set_mode(v))
      b.pack(side="left", padx=(0,8))
      self._mode_btns.append((val, b))

    tk.Frame(opt_in, bg=BORDER, height=1).pack(fill="x", pady=(0,10))

    # 이름규칙 입력
    rule_row = tk.Frame(opt_in, bg=SURFACE2)
    rule_row.pack(fill="x", pady=(0,6))
    tk.Label(rule_row, text="이름규칙", font=FONT_SM, bg=SURFACE2,
             fg=SUBTEXT, width=7, anchor="w").pack(side="left")
    self.ent_rule = tk.Entry(rule_row, font=FONT, bg=SURFACE, fg=TEXT,
                             insertbackground=TEXT, relief="flat",
                             highlightthickness=1, highlightcolor=ACCENT,
                             highlightbackground=BORDER,
                             disabledbackground=SURFACE2, disabledforeground=BORDER)
    self.ent_rule.pack(side="left", fill="x", expand=True, ipady=6)

    # 힌트 태그 (클릭 시 입력창에 삽입)
    hint_row = tk.Frame(opt_in, bg=SURFACE2)
    hint_row.pack(fill="x", pady=(6,0))
    self._hint_tags = []
    for tag, desc in [("%d","번호"), ("%02d","제로패딩"), ("%03d","세자리"), ("%d화","화수"), ("%02d화","제로패딩+화수")]:
      t = tk.Label(hint_row, text=f" {tag}  {desc} ", font=FONT_XS,
                   bg=SURFACE, fg=SUBTEXT, cursor="hand2",
                   highlightthickness=1, highlightbackground=BORDER)
      t.pack(side="left", padx=(0,6))
      self._hint_tags.append((tag, t))

    tk.Frame(opt_in, bg=BORDER, height=1).pack(fill="x", pady=10)

    # 시작 번호
    num_row = tk.Frame(opt_in, bg=SURFACE2)
    num_row.pack(fill="x")
    tk.Label(num_row, text="시작 번호", font=FONT_SM, bg=SURFACE2,
             fg=SUBTEXT).pack(side="left", padx=(0,10))
    self._spn_wrap = tk.Frame(num_row, bg=SURFACE,
                              highlightthickness=1, highlightbackground=BORDER)
    self._spn_wrap.pack(side="left")
    self.spn_start = tk.Spinbox(self._spn_wrap, from_=1, to=999, width=5,
                                font=FONT, bg=SURFACE, fg=TEXT,
                                relief="flat", bd=0, highlightthickness=0,
                                buttonbackground=SURFACE2, insertbackground=TEXT,
                                disabledbackground=SURFACE2, disabledforeground=BORDER)
    self.spn_start.pack(padx=4, pady=3)
    self._update_rule_widgets()

    # ── 액션 바 ──
    act = tk.Frame(body, bg=BG)
    act.pack(fill="x")
    self.lbl_status = tk.Label(act, text="", font=FONT_SM,
                               bg=BG, fg=SUBTEXT, anchor="w")
    self.lbl_status.pack(side="left", fill="x", expand=True)

    restore = tk.Button(act, text="↩ 복원", command=self._restore,
                        bg=SURFACE2, fg=SUBTEXT, font=FONT_B,
                        relief="flat", bd=0, cursor="hand2", padx=22, pady=9,
                        highlightthickness=1, highlightbackground=BORDER,
                        activebackground=BORDER, activeforeground=TEXT)
    restore.pack(side="right", padx=(8,0))
    hover(restore, BORDER, SURFACE2, TEXT, SUBTEXT)

    apply_b = tk.Button(act, text="✦ 일괄수정", command=self._apply,
                        bg=ACCENT, fg="#fff", font=FONT_B,
                        relief="flat", bd=0, cursor="hand2", padx=28, pady=9,
                        activebackground=ACCENT_HV, activeforeground="#fff")
    apply_b.pack(side="right")
    hover(apply_b, ACCENT_HV, ACCENT)

  def _make_panel(self, parent, title, accent, header_bg, header_border, col):
    # 패널 외곽 프레임
    outer = tk.Frame(parent, bg=SURFACE2,
                     highlightthickness=1, highlightbackground=BORDER)
    outer.grid(row=0, column=col, sticky="nsew",
               padx=(0,8) if col == 0 else (8,0), pady=(0,14))
    outer.rowconfigure(2, weight=1)
    outer.columnconfigure(0, weight=1)

    # 리스트박스 (먼저 생성 - 버튼 커맨드 참조용)
    list_f = tk.Frame(outer, bg=SURFACE2)
    list_f.grid(row=2, column=0, sticky="nsew", padx=6, pady=6)
    list_f.rowconfigure(0, weight=1)
    list_f.columnconfigure(0, weight=1)

    lb = tk.Listbox(list_f, bg=SURFACE2, fg=TEXT,
                    selectbackground=SEL_BG, selectforeground=SEL_FG,
                    font=FONT_SM, relief="flat", bd=0,
                    highlightthickness=0, activestyle="none",
                    selectmode="extended")
    sy = ttk.Scrollbar(list_f, orient="vertical",   command=lb.yview,
                       style="Dark.Vertical.TScrollbar")
    sx = ttk.Scrollbar(list_f, orient="horizontal", command=lb.xview,
                       style="Dark.Horizontal.TScrollbar")
    lb.config(yscrollcommand=sy.set, xscrollcommand=sx.set)
    sy.grid(row=0, column=1, sticky="ns")
    sx.grid(row=1, column=0, sticky="ew")
    lb.grid(row=0, column=0, sticky="nsew")

    # 패널 헤더
    ph = tk.Frame(outer, bg=header_bg)
    ph.grid(row=0, column=0, sticky="ew")

    left_h = tk.Frame(ph, bg=header_bg)
    left_h.pack(side="left", padx=12, pady=9)
    tk.Label(left_h, text=title, font=FONT_B, bg=header_bg, fg=accent).pack(side="left")
    count_lbl = tk.Label(left_h, text=" 0 ", font=FONT_XS, bg=header_bg, fg=accent)
    count_lbl.pack(side="left", padx=(8,0))

    # 헤더 우측 버튼 (↑ ↓ ✕)
    right_h = tk.Frame(ph, bg=header_bg)
    right_h.pack(side="right", padx=8, pady=6)

    for sym, direction in [("↑",-1),("↓",1),("✕",None)]:
      is_del = direction is None
      if is_del:
        cmd  = lambda lb=lb: self._delete(lb)
        fg_c = DANGER
        hv_c = DANGER_H
      else:
        cmd  = lambda lb=lb, d=direction: self._move(lb, d)
        fg_c = SUBTEXT
        hv_c = BORDER

      b = tk.Button(right_h, text=sym, command=cmd,
                    bg=SURFACE, fg=fg_c, font=("Segoe UI",9),
                    relief="flat", bd=0, cursor="hand2",
                    padx=7, pady=4,
                    highlightthickness=1, highlightbackground=BORDER,
                    activebackground=hv_c, activeforeground=fg_c)
      b.pack(side="left", padx=2)
      hover(b, hv_c, SURFACE)

    # 헤더 하단 구분선
    tk.Frame(outer, bg=header_border, height=1).grid(row=1, column=0, sticky="ew")

    return lb, count_lbl

  def _set_mode(self, val):
    # 모드 버튼 토글 스타일 변경
    self.mode_var.set(val)
    for v, btn in self._mode_btns:
      active = v == val
      btn.config(
        bg=MODE_ACT if active else SURFACE2,
        fg=ACCENT if active else SUBTEXT,
        highlightbackground=ACCENT if active else BORDER,
      )
    self._update_rule_widgets()

  def _update_rule_widgets(self):
    # 이름규칙 모드일 때만 입력 위젯 활성화
    is_rule = self.mode_var.get() == "rule"
    self.ent_rule.config(state="normal" if is_rule else "disabled")
    self.spn_start.config(state="normal" if is_rule else "disabled")
    self._spn_wrap.config(highlightbackground=BORDER if is_rule else SURFACE2)
    for tag, lbl in self._hint_tags:
      if is_rule:
        lbl.config(fg=SUBTEXT, cursor="hand2")
        lbl.bind("<Button-1>", lambda e, s=tag: self._insert_tag(s))
        hover(lbl, SURFACE2, SURFACE, ACCENT, SUBTEXT)
      else:
        lbl.config(fg=BORDER, cursor="")
        lbl.unbind("<Button-1>")

  def _insert_tag(self, tag):
    # 힌트 태그 클릭 시 입력창에 삽입
    self.ent_rule.insert(tk.END, tag)
    self.ent_rule.focus()

  def _load_files(self):
    videos, subs = renamer.load_files(self.folder_path)
    self.lst_video.delete(0, tk.END)
    self.lst_sub.delete(0, tk.END)
    for v in videos: self.lst_video.insert(tk.END, v)
    for s in subs:   self.lst_sub.insert(tk.END, s)
    self.lbl_path.config(text=self.folder_path, fg=TEXT)
    self.vid_badge.config(text=f" {len(videos)} ")
    self.sub_badge.config(text=f" {len(subs)} ")
    self._status(f"비디오 {len(videos)}개  ·  자막 {len(subs)}개 로드됨", SUBTEXT)

  def _move(self, listbox, direction):
    # 다중 선택 이동 (위/아래)
    sel = list(listbox.curselection())
    if not sel: return
    if direction == -1 and sel[0] == 0: return
    if direction ==  1 and sel[-1] == listbox.size() - 1: return
    items = [listbox.get(i) for i in sel]
    for i in reversed(sel):
      listbox.delete(i)
    for i, item in zip(sel, items):
      listbox.insert(i + direction, item)
    for i in sel:
      listbox.selection_set(i + direction)

  def _delete(self, listbox):
    # 다중 선택 삭제
    for i in reversed(listbox.curselection()):
      listbox.delete(i)

  def _get_list(self, lb):
    return list(lb.get(0, tk.END))

  def _apply(self):
    if not self.folder_path:
      messagebox.showwarning("경고", "폴더 경로가 없습니다.")
      return
    mode   = self.mode_var.get()
    videos = self._get_list(self.lst_video)
    subs   = self._get_list(self.lst_sub)
    try:
      start = int(self.spn_start.get())
    except ValueError:
      start = 1

    # 미리보기 계산
    try:
      if mode == "video":
        preview_items = renamer.preview_by_video(videos, subs)
      elif mode == "sub":
        preview_items = renamer.preview_by_sub(videos, subs)
      else:
        rule = self.ent_rule.get().strip()
        if not rule:
          messagebox.showwarning("경고", "이름규칙을 입력해주세요.")
          return
        if not re.search(r'%\d*d', rule):
          rule = rule.rstrip() + ' %d'
        preview_items = renamer.preview_by_rule(videos, subs, rule, start)
    except Exception as e:
      messagebox.showerror("오류", str(e))
      return

    if not preview_items:
      messagebox.showinfo("알림", "변경할 파일이 없습니다.")
      return

    # 미리보기 팝업
    dlg = PreviewDialog(self, preview_items)
    if not dlg.confirmed:
      return

    # 실제 변경 실행
    try:
      if mode == "video":
        backup, results, skipped = renamer.rename_by_video(self.folder_path, videos, subs)
      elif mode == "sub":
        backup, results, skipped = renamer.rename_by_sub(self.folder_path, videos, subs)
      else:
        backup, results, skipped = renamer.rename_by_rule(self.folder_path, videos, subs, rule, start)
      self.backup.update(backup)
      msg = f"✓  {len(results)}개 변경 완료"
      if skipped:
        msg += f"   {len(skipped)}개 건너뜀"
        messagebox.showwarning("일부 건너뜀", "\n".join(skipped[:10]))
      self._status(msg, SUCCESS)
      self._load_files()
    except Exception as e:
      messagebox.showerror("오류", str(e))

  def _restore(self):
    if not self.backup:
      messagebox.showinfo("알림", "복원할 내역이 없습니다.")
      return
    results = renamer.restore(self.folder_path, self.backup)
    self.backup = {}
    self._load_files()
    self._status(f"↩  {len(results)}개 복원 완료", SUB_C)

  def _reg_add(self):
    ok, msg = registry.register()
    messagebox.showinfo("레지스트리 등록", msg) if ok else messagebox.showerror("오류", msg)

  def _reg_remove(self):
    ok, msg = registry.unregister()
    messagebox.showinfo("레지스트리 제거", msg) if ok else messagebox.showerror("오류", msg)

  def _status(self, msg, color=SUBTEXT):
    self.lbl_status.config(text=msg, fg=color)


if __name__ == "__main__":
  app = App()
  app.mainloop()
