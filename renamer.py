# 파일명 변경 로직 모듈
import os
import re

VIDEO_EXTS    = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.m4v', '.ts', '.flv'}
SUBTITLE_EXTS = {'.srt', '.ass', '.ssa', '.smi', '.vtt', '.sub'}

def natural_sort_key(s):
  return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

def long_path(p):
  if os.name == 'nt' and not p.startswith('\\\\?\\'):
    return '\\\\?\\' + os.path.abspath(p)
  return p

def safe_rename(old_path, new_path):
  if os.path.abspath(old_path) == os.path.abspath(new_path):
    return False, "동일한 이름 (건너뜀)"
  if os.path.exists(new_path):
    return False, f"이미 존재함: {os.path.basename(new_path)}"
  os.rename(long_path(old_path), long_path(new_path))
  return True, ""

def load_files(folder_path):
  if not os.path.isdir(folder_path):
    return [], []
  files = os.listdir(folder_path)
  videos = sorted([f for f in files if os.path.splitext(f)[1].lower() in VIDEO_EXTS], key=natural_sort_key)
  subs   = sorted([f for f in files if os.path.splitext(f)[1].lower() in SUBTITLE_EXTS], key=natural_sort_key)
  return videos, subs

def apply_rule(rule, index):
  return re.sub(r'%(\d*)d', lambda m: str(index).zfill(int(m.group(1)) if m.group(1) else 1), rule)

# ── 미리보기 함수 ──────────────────────────────────────────
def preview_by_video(videos, subs):
  count = min(len(videos), len(subs))
  return [(subs[i], os.path.splitext(videos[i])[0] + os.path.splitext(subs[i])[1])
          for i in range(count)]

def preview_by_sub(videos, subs):
  count = min(len(videos), len(subs))
  return [(videos[i], os.path.splitext(subs[i])[0] + os.path.splitext(videos[i])[1])
          for i in range(count)]

def preview_by_rule(videos, subs, rule, start=1):
  result = []
  for i, name in enumerate(videos):
    ext = os.path.splitext(name)[1]
    result.append((name, apply_rule(rule, i + start) + ext))
  for i, name in enumerate(subs):
    ext = os.path.splitext(name)[1]
    result.append((name, apply_rule(rule, i + start) + ext))
  return result

# ── 실제 변경 함수 ─────────────────────────────────────────
def rename_by_video(folder, videos, subs):
  backup, results, skipped = {}, [], []
  for i in range(min(len(videos), len(subs))):
    new_name = os.path.splitext(videos[i])[0] + os.path.splitext(subs[i])[1]
    ok, msg  = safe_rename(os.path.join(folder, subs[i]), os.path.join(folder, new_name))
    if ok:
      backup[new_name] = subs[i]; results.append((subs[i], new_name))
    else:
      skipped.append(f"{subs[i]} → {msg}")
  return backup, results, skipped

def rename_by_sub(folder, videos, subs):
  backup, results, skipped = {}, [], []
  for i in range(min(len(videos), len(subs))):
    new_name = os.path.splitext(subs[i])[0] + os.path.splitext(videos[i])[1]
    ok, msg  = safe_rename(os.path.join(folder, videos[i]), os.path.join(folder, new_name))
    if ok:
      backup[new_name] = videos[i]; results.append((videos[i], new_name))
    else:
      skipped.append(f"{videos[i]} → {msg}")
  return backup, results, skipped

def rename_by_rule(folder, videos, subs, rule, start=1):
  backup, results, skipped = {}, [], []
  for i, name in enumerate(videos):
    ext      = os.path.splitext(name)[1]
    new_name = apply_rule(rule, i + start) + ext
    ok, msg  = safe_rename(os.path.join(folder, name), os.path.join(folder, new_name))
    if ok:
      backup[new_name] = name; results.append((name, new_name))
    else:
      skipped.append(f"{name} → {msg}")
  for i, name in enumerate(subs):
    ext      = os.path.splitext(name)[1]
    new_name = apply_rule(rule, i + start) + ext
    ok, msg  = safe_rename(os.path.join(folder, name), os.path.join(folder, new_name))
    if ok:
      backup[new_name] = name; results.append((name, new_name))
    else:
      skipped.append(f"{name} → {msg}")
  return backup, results, skipped

def restore(folder, backup):
  results = []
  for new_name, old_name in backup.items():
    new_path = os.path.join(folder, new_name)
    if os.path.exists(new_path):
      ok, _ = safe_rename(new_path, os.path.join(folder, old_name))
      if ok:
        results.append((new_name, old_name))
  return results
