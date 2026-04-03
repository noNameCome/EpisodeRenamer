# 레지스트리 등록/해제 모듈
import winreg
import sys
import os

APP_NAME = "RenaMatcher"
MENU_TEXT = "RenaMatcher로 열기"

def get_command():
  # 실행 명령어 반환 (exe / 스크립트 구분)
  if getattr(sys, 'frozen', False):
    # PyInstaller exe
    return f'"{sys.executable}" "%V"'
  else:
    # Python 스크립트로 실행 시
    script_path = os.path.abspath(sys.argv[0])
    return f'"{sys.executable}" "{script_path}" "%V"'

def get_icon_path():
  # exe면 exe 자체, 스크립트면 icon.ico 경로
  if getattr(sys, 'frozen', False):
    return sys.executable
  base = os.path.dirname(os.path.abspath(sys.argv[0]))
  ico = os.path.join(base, 'icon.ico')
  return ico if os.path.exists(ico) else ""

def _write_key(base_path, command, icon):
  # 레지스트리 키 작성 공통 함수
  key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_path)
  winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_TEXT)
  if icon:
    winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon)
  winreg.CloseKey(key)
  cmd_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{base_path}\\command")
  winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
  winreg.CloseKey(cmd_key)

def register():
  # 폴더 우클릭 + 폴더 내부 우클릭 모두 등록
  command = get_command()
  icon = get_icon_path()
  try:
    # 폴더 아이콘 우클릭
    _write_key(f"Software\\Classes\\Directory\\shell\\{APP_NAME}", command, icon)
    # 폴더 내부 빈 공간 우클릭
    _write_key(f"Software\\Classes\\Directory\\Background\\shell\\{APP_NAME}", command, icon)
    return True, f"레지스트리 등록 완료"
  except Exception as e:
    return False, f"오류: {e}"

def unregister():
  # 폴더 우클릭 + 내부 우클릭 둘 다 제거
  try:
    for base in ["Directory\\shell", "Directory\\Background\\shell"]:
      key_path = f"Software\\Classes\\{base}\\{APP_NAME}"
      try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\command")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
      except FileNotFoundError:
        pass
    return True, "레지스트리 제거 완료"
  except Exception as e:
    return False, f"오류: {e}"
