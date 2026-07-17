import os
import socket
import threading
import time
import subprocess
import paramiko
from dotenv import load_dotenv
import sys
import select
import argparse

parser = argparse.ArgumentParser(description='Миграции БД с поддержкой окружений')
parser.add_argument('--env', choices=['local', 'prod'], default='local', 
                   help='Окружение: local (по умолчанию) или prod')
args, unknown = parser.parse_known_args()

if args.env == 'prod':
    env_file = '.env.production'
else:
    env_file = '.env.local'

if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"Загружено окружение: {args.env} ({env_file})")
else:
    print(f"Файл {env_file} не найден, загружаем .env по умолчанию")
    load_dotenv()

SERVER_HOST = os.getenv("SERVER_HOST")
SERVER_PORT = os.getenv("SERVER_PORT")
SERVER_PORT = int(SERVER_PORT) if SERVER_PORT else None
SERVER_USER = os.getenv("SERVER_USER")
SERVER_PASSWORD = os.getenv("SERVER_PASSWORD")
LOCAL_PORT = int(os.getenv("POSTGRES_PORT", "5434"))
REMOTE_HOST = "127.0.0.1"
# Порт Postgres на самом сервере: compose-стек публикует его на 5434
REMOTE_PORT = int(os.getenv("REMOTE_DB_PORT", "5434"))

DB_NAME = os.getenv("POSTGRES_DB", "smart_tracker")
DB_USER = os.getenv("POSTGRES_USER", "smart_tracker_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "smart_tracker_password")

def wait_for_port(port, host='127.0.0.1', timeout=30):
    """Проверка доступности порта"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2) as sock:
                sock.send(b'\x00\x00\x00\x08\x04\xd2\x16\x2f')
                return True
        except (OSError, socket.error):
            time.sleep(1)
    return False

def forward_source(source, dest):
    """Функция для пересылки данных"""
    try:
        while True:
            try:
                data = source.recv(32768)
                if not data:
                    break
                dest.send(data)
            except (socket.error, paramiko.SSHException):
                break
    except Exception:
        pass
    finally:
        try:
            source.close()
        except:
            pass
        try:
            dest.close()
        except:
            pass

def handle_connection(chan, local_sock):
    """Обработка одного соединения"""
    try:
        t1 = threading.Thread(target=forward_source, args=(local_sock, chan), daemon=True)
        t2 = threading.Thread(target=forward_source, args=(chan, local_sock), daemon=True)
        t1.start()
        t2.start()
        
        while t1.is_alive() and t2.is_alive():
            time.sleep(0.1)
    except Exception:
        pass

def start_tunnel():
    """Запуск SSH туннеля"""
    if not SERVER_HOST:
        print("SERVER_HOST не указан, работаем с локальной БД")
        return None, None
    
    print(f"Подключение к {SERVER_USER}@{SERVER_HOST}:{SERVER_PORT}...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    connect_kwargs = {
        'hostname': SERVER_HOST,
        'port': SERVER_PORT,
        'username': SERVER_USER,
        'password': SERVER_PASSWORD,
        'timeout': 30,
        'banner_timeout': 60,
        'auth_timeout': 60,
        'allow_agent': False,
        'look_for_keys': False
    }
    
    try:
        client.connect(**connect_kwargs)
        transport = client.get_transport()
        transport.set_keepalive(30)
        
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("127.0.0.1", LOCAL_PORT))
        server_sock.listen(100)
        
        def accept_loop():
            while True:
                try:
                    local_sock, addr = server_sock.accept()
                    
                    try:
                        chan = transport.open_channel(
                            'direct-tcpip',
                            (REMOTE_HOST, REMOTE_PORT),
                            addr
                        )
                        
                        if chan:
                            threading.Thread(
                                target=handle_connection,
                                args=(chan, local_sock),
                                daemon=True
                            ).start()
                        else:
                            local_sock.close()
                            
                    except Exception:
                        local_sock.close()
                        
                except Exception:
                    break
        
        threading.Thread(target=accept_loop, daemon=True).start()
        print(f"Туннель запущен: 127.0.0.1:{LOCAL_PORT}")
        
        return client, server_sock
        
    except Exception as e:
        print(f"Ошибка подключения SSH: {e}")
        raise

def run_alembic_command():
    """Запуск команды alembic"""
    alembic_cmd = ["alembic"]
    
    if unknown:
        alembic_cmd.extend(unknown)
    else:
        alembic_cmd.extend(["upgrade", "head"])
    
    print(f"Выполнение: {' '.join(alembic_cmd)}")
    
    env = os.environ.copy()
    
    if SERVER_HOST:
        env['DATABASE_URL_SYNC'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{LOCAL_PORT}/{DB_NAME}"
    else:
        db_host = "localhost"
        db_port = LOCAL_PORT
        
        env['DATABASE_URL_SYNC'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{db_host}:{db_port}/{DB_NAME}"
    
    result = subprocess.run(
        alembic_cmd,
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Ошибка: {result.stderr}")
        return result.returncode
    else:
        if result.stdout:
            print(result.stdout)
        return 0

if __name__ == "__main__":
    try:
        client, server_sock = start_tunnel()
        
        if client:
            if not wait_for_port(LOCAL_PORT):
                print("Не удалось дождаться порта")
                exit(1)
        
        exit_code = run_alembic_command()
        exit(exit_code)
            
    except KeyboardInterrupt:
        print("\nПрерывание")
        exit(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        exit(1)
    finally:
        if 'server_sock' in locals() and server_sock:
            try:
                server_sock.close()
            except:
                pass
        if 'client' in locals() and client:
            try:
                client.close()
            except:
                pass