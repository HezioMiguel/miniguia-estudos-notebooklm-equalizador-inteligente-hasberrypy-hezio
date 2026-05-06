import numpy as np
import pyaudio
import sys
from scipy.signal import butter, lfilter, lfilter_zi
from numba import jit

# =========================================================
# 1. CONFIGURAÇÕES TÉCNICAS (MODIFICÁVEIS)
# =========================================================
CHUNK = 512          # Latência de buffer (~11.6ms @ 44.1kHz)
FS = 44100           # Taxa de amostragem
F_TARGET = 3200.0    # Frequência central do EQ Dinâmico
Q = 1.2              # Fator de qualidade (largura da banda)
THRESHOLD_DB = -18.0 # Limite de atuação
RATIO = 4.0          # Compressão (4:1)
ATK_MS = 5.0         # Ataque rápido para transientes
REL_MS = 60.0        # Release musical

# =========================================================
# 2. ENGINE DE PROCESSAMENTO ULTRA-RÁPIDA (NUMBA)
# =========================================================
@jit(nopython=True, cache=True)
def engine_dsp_pro(abs_sq, chunk_size, c_rms, c_atk, c_rel, threshold_db, ratio, env_in, g_in):
    """
    Processamento de ganho dinâmico em nível de código de máquina.
    Usa propriedades logarítmicas para evitar raízes quadradas pesadas.
    """
    gr_linear = np.ones(chunk_size, dtype=np.float32)
    curr_e = env_in
    curr_g = g_in
    
    for i in range(chunk_size):
        # Suavização RMS (Energia média)
        curr_e = c_rms * curr_e + (1.0 - c_rms) * abs_sq[i]
        
        # Conversão direta p/ dB (10 * log10(x^2) é o mesmo que 20 * log10(x))
        env_db = 10.0 * np.log10(curr_e + 1e-12)
        
        # Cálculo do ganho alvo
        g_target = 1.0
        if env_db > threshold_db:
            # Curva de transferência padrão de compressão
            g_target = 10.0**((threshold_db - env_db) * (1.0 - 1.0/ratio) / 20.0)
            
        # Balística Assimétrica (Ataque e Release suaves)
        coeff = c_atk if g_target < curr_g else c_rel
        curr_g = coeff * curr_g + (1.0 - coeff) * g_target
        gr_linear[i] = curr_g
        
    return gr_linear, curr_e, curr_g

# =========================================================
# 3. SETUP DE FILTROS E ESTADOS
# =========================================================
nyq = 0.5 * FS
bw = F_TARGET / Q
low = max(0.001, (F_TARGET - bw/2) / nyq)
high = min(0.999, (F_TARGET + bw/2) / nyq)
b_bp, a_bp = butter(2, [low, high], btype='bandpass')

# Estados persistentes para evitar estalos (Pulo do Gato)
zi_banda = lfilter_zi(b_bp, a_bp)
curr_env = np.float64(0.0)
last_g = np.float64(1.0)

# Coeficientes de tempo
def get_c(ms): return np.float64(np.exp(-1.0 / (FS * (ms / 1000.0))))
c_atk, c_rel, c_rms = get_c(ATK_MS), get_c(REL_MS), get_c(20.0)

# =========================================================
# 4. CALLBACK DE ÁUDIO REAL-TIME
# =========================================================
def callback(in_data, frame_count, time_info, status):
    global zi_banda, curr_env, last_g
    
    # Converte buffer para array
    x = np.frombuffer(in_data, dtype=np.float32).copy()
    
    # Isola a banda (Filtro de fase estável)
    banda, zi_banda = lfilter(b_bp, a_bp, x, zi=zi_banda)
    
    # Roda a Engine Numba
    gr, curr_env, last_g = engine_dsp_pro(
        banda**2, CHUNK, c_rms, c_atk, c_rel, 
        THRESHOLD_DB, RATIO, curr_env, last_g
    )
    
    # Recombinação e Limiter de segurança simples
    final = x + (banda * (gr - 1.0))
    
    # Peak monitor (Opcional)
    if np.max(np.abs(final)) > 1.0:
        final /= np.max(np.abs(final))
        
    return (final.astype(np.float32).tobytes(), pyaudio.paContinue)

# =========================================================
# 5. INICIALIZAÇÃO E SELEÇÃO DE HARDWARE
# =========================================================
p = pyaudio.PyAudio()

print("\n--- DISPOSITIVOS DISPONÍVEIS ---")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"ID {i}: {info['name']} (Inputs: {info['maxInputChannels']})")

# Selecione os IDs aqui baseado no print acima
IN_ID = 1  # Exemplo: Placa USB
OUT_ID = 2 

print("\nCompilando Engine Numba (Warm-up)...")
_ = engine_dsp_pro(np.zeros(CHUNK, dtype=np.float32), CHUNK, c_rms, c_atk, c_rel, THRESHOLD_DB, RATIO, 0.0, 1.0)

try:
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=FS,
                    input=True,
                    output=True,
                    input_device_index=IN_ID,
                    output_device_index=OUT_ID,
                    frames_per_buffer=CHUNK,
                    stream_callback=callback)

    print(f"\n>> ENGINE ATIVA EM {F_TARGET}Hz")
    print(">> Pressione Ctrl+C para encerrar...")
    
    stream.start_stream()
    while stream.is_active():
        pass

except KeyboardInterrupt:
    print("\nEncerrando...")
except Exception as e:
    print(f"\nErro: {e}")
finally:
    if 'stream' in locals():
        stream.stop_stream()
        stream.close()
    p.terminate()
