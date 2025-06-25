from flask import Flask, render_template, redirect, url_for, flash
import os
import subprocess
import signal

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-me' # Ganti dengan kunci rahasia Anda

PID_FILE = "bot.pid"
LOG_FILE = "bot.log"
BOT_SCRIPT = "bot.py"

def is_bot_running():
    """Mengecek apakah proses bot sedang berjalan berdasarkan file PID."""
    if not os.path.exists(PID_FILE):
        return False
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        # Kirim sinyal 0 untuk mengecek apakah proses ada
        os.kill(pid, 0)
    except (IOError, ValueError, ProcessLookupError):
        # File PID ada tapi prosesnya tidak ada (stale)
        return False
    except PermissionError:
        # Tidak punya izin, tapi anggap saja proses berjalan
        return True
    return True

@app.route('/')
def index():
    """Menampilkan halaman utama panel."""
    running = is_bot_running()
    logs = ""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                # Baca 50 baris terakhir
                lines = f.readlines()
                logs = "".join(lines[-50:])
        except Exception as e:
            logs = f"Gagal membaca log: {e}"
    return render_template('index.html', is_running=running, logs=logs)

@app.route('/start', methods=['POST'])
def start_bot():
    """Memulai proses bot di background."""
    if is_bot_running():
        flash("Bot sudah berjalan.", "warning")
        return redirect(url_for('index'))
    
    try:
        # Menjalankan skrip bot sebagai proses baru
        subprocess.Popen(["python3", BOT_SCRIPT])
        flash("Bot berhasil dimulai!", "success")
    except Exception as e:
        flash(f"Gagal memulai bot: {e}", "danger")
        
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_bot():
    """Menghentikan proses bot."""
    if not is_bot_running():
        flash("Bot sudah berhenti.", "warning")
        return redirect(url_for('index'))
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        # Kirim sinyal SIGTERM untuk berhenti secara halus
        os.kill(pid, signal.SIGTERM)
        flash("Sinyal berhenti berhasil dikirim ke bot.", "success")
    except Exception as e:
        flash(f"Gagal menghentikan bot: {e}", "danger")
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Jangan gunakan ini untuk produksi. Gunakan Gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=True)