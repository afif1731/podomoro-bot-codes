from gtts import gTTS
import os

texts = {
    # Kondisi Bluetooth
    "waiting_bluetooth": "Menunggu koneksi Bluetooth. Silakan nyalakan perangkat Bluetooth Anda.",
    "bluetooth_connected": "Bluetooth terhubung. Robot Pomodoro siap digunakan.",
    "bluetooth_disconnected": "Bluetooth terputus. Mencoba menghubungkan kembali.",
    
    # Kondisi utama
    "idle": "Robot Pomodoro dalam mode siaga. Sentuh saya untuk memulai sesi kerja.",
    "working": "Sesi kerja dimulai. Fokus dan kerjakan tugas Anda.",
    "working_reminder": "Ingat, tetap fokus. Hindari gangguan selama sesi kerja.",
    
    # Kondisi gangguan
    "distraction_detected": "Terdeteksi gangguan. Mohon kembali fokus pada pekerjaan.",
    "distraction_warning": "Peringatan: Terlalu banyak gangguan. Kualitas kerja akan menurun.",
    
    # Kondisi istirahat
    "break_start": "Waktu istirahat! Silakan rileks, minum air, atau regangkan tubuh.",
    "break_end": "Istirahat selesai. Siap untuk sesi kerja berikutnya?",
    
    # Pengingat istirahat
    "break_reminder": "Pengingat: Sudah waktunya istirahat. Jaga kesehatan mata dan postur tubuh.",
    "break_overdue": "Anda melewati waktu istirahat. Segera ambil istirahat pendek untuk produktivitas optimal.",
    
    # Selesai
    "session_complete": "Sesi Pomodoro selesai. Kerja bagus! Waktunya istirahat panjang.",
    "all_sessions_complete": "Semua sesi hari ini selesai. Istirahat yang cukup untuk besok.",
    
    # Sistem
    "system_ready": "Sistem Pomodoro siap. Atur timer dan mulai produktif!",
    "timer_set": "Timer diatur. Sesi kerja akan dimulai sebentar lagi.",
    "pause": "Sesi dijeda. Lanjutkan ketika sudah siap.",
    "resume": "Sesi dilanjutkan. Kembali fokus.",
    
    # Motivasi
    "motivation_work": "Tetap semangat! Setiap menit fokus membawa Anda lebih dekat ke tujuan.",
    "motivation_break": "Istirahat adalah bagian dari produktivitas. Nikmati waktu istirahat Anda."
}

def generate_audio_files(output_folder="audio"):
    """Generate semua file audio untuk Pomodoro Robot"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    print("=== GENERATING POMODORO ROBOT AUDIO FILES ===")
    success_count = 0
    error_count = 0
    
    for name, text in texts.items():
        try:
            print(f"\nMembuat: {name}")
            print(f"Teks: '{text}'")
            
            tts = gTTS(text=text, lang='id', slow=False)
            
            filename = f"{output_folder}/{name}.mp3"
            tts.save(filename)
            
            if os.path.exists(filename):
                file_size = os.path.getsize(filename) / 1024  # KB
                print(f"✓ Berhasil: {filename} ({file_size:.1f} KB)")
                success_count += 1
            else:
                print(f"✗ Gagal: File tidak terbentuk")
                error_count += 1
                
        except Exception as e:
            print(f"✗ Error saat membuat {name}: {str(e)}")
            error_count += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Total files: {len(texts)}")
    print(f"Berhasil: {success_count}")
    print(f"Gagal: {error_count}")
    
    return success_count == len(texts)

def get_state_mapping():
    """Mapping state aplikasi ke nama file audio"""
    return {
        # Bluetooth states
        "WAITING_FOR_DEVICE": "waiting_bluetooth",
        "DEVICE_CONNECTED": "bluetooth_connected",
        "DEVICE_DISCONNECTED": "bluetooth_disconnected",
        
        # Timer states
        "IDLE": "idle",
        "WORK_SESSION_START": "working",
        "WORK_SESSION_ACTIVE": "working_reminder",
        "BREAK_SESSION_START": "break_start",
        "BREAK_SESSION_END": "break_end",
        
        # Focus states
        "DISTRACTION_DETECTED": "distraction_detected",
        "DISTRACTION_WARNING": "distraction_warning",
        
        # Reminder states
        "BREAK_REMINDER": "break_reminder",
        "BREAK_OVERDUE": "break_overdue",
        
        # Completion states
        "SESSION_COMPLETE": "session_complete",
        "ALL_SESSIONS_COMPLETE": "all_sessions_complete",
        
        # System states
        "SYSTEM_READY": "system_ready",
        "TIMER_SET": "timer_set",
        "PAUSED": "pause",
        "RESUMED": "resume",
        
        # Motivation states (bisa dipanggil acak)
        "MOTIVATION_WORK": "motivation_work",
        "MOTIVATION_BREAK": "motivation_break"
    }

def get_audio_path_for_state(state, audio_folder="audio"):
    """Mendapatkan path file audio berdasarkan state"""
    mapping = get_state_mapping()
    audio_file = mapping.get(state)
    
    if audio_file:
        return f"{audio_folder}/{audio_file}.mp3"
    else:
        # Fallback ke idle state
        return f"{audio_folder}/idle.mp3"

# Contoh penggunaan
if __name__ == "__main__":
    # Generate semua file audio
    success = generate_audio_files()
    
    if success:
        print("\n✅ Semua file audio berhasil digenerate!")
        
        # Contoh penggunaan state mapping
        print("\n=== STATE MAPPING EXAMPLE ===")
        test_states = ["WORK_SESSION_START", "BREAK_REMINDER", "SESSION_COMPLETE"]
        
        for state in test_states:
            audio_path = get_audio_path_for_state(state)
            print(f"State '{state}' → Audio: {audio_path}")
            
        # List semua file yang dibuat
        print("\n=== GENERATED FILES ===")
        for filename in sorted(os.listdir("audio")):
            if filename.endswith(".mp3"):
                print(f"• {filename}")
    else:
        print("\n⚠️ Beberapa file gagal digenerate. Periksa koneksi internet.")