import numpy as np
from scipy.signal import butter, filtfilt
import soundfile as sf

# =========================================================
# 1. MÓDULO DE FILTRAGEM BÁSICA (HPF E LPF)
# =========================================================
def aplicar_hpf_lpf(sinal, fs, hpf_freq, lpf_freq):
    """
    Aplica filtros Passa-Alta (Corta graves) e Passa-Baixa (Corta agudos).
    Utiliza o design de filtro Butterworth para curvas suaves [5, 7].
    """
    # High-Pass Filter (Filtro Passa-Alta)
    b_h, a_h = butter(4, hpf_freq / (0.5 * fs), btype='high')
    sinal = filtfilt(b_h, a_h, sinal)
    
    # Low-Pass Filter (Filtro Passa-Baixa)
    b_l, a_l = butter(4, lpf_freq / (0.5 * fs), btype='low')
    sinal = filtfilt(b_l, a_l, sinal)
    
    return sinal

# =========================================================
# 2. MÓDULO DO EQUALIZADOR DINÂMICO
# =========================================================
def equalizador_dinamico(sinal, fs, freq_alvo, largura_banda, threshold_linear, attack_ms, release_ms, max_reducao=0.1):
    """
    Aplica a redução de ganho APENAS quando a frequência alvo passar do threshold.
    """
    # 1. Separa o áudio em duas faixas usando processamento paralelo [8]
    low_cut = freq_alvo - (largura_banda / 2)
    high_cut = freq_alvo + (largura_banda / 2)
    
    # Isola a frequência problemática (Bandpass) [3, 9]
    b_bp, a_bp = butter(4, [low_cut / (0.5 * fs), high_cut / (0.5 * fs)], btype='bandpass')
    banda_alvo = filtfilt(b_bp, a_bp, sinal)
    
    # Isola o restante do áudio que não será alterado (Bandstop) [10]
    b_bs, a_bs = butter(4, [low_cut / (0.5 * fs), high_cut / (0.5 * fs)], btype='bandstop')
    resto_audio = filtfilt(b_bs, a_bs, sinal)
    
    # 2. Configurações de Dinâmica (Envelope Follower e Fatores de Tempo) [4]
    # Converte os tempos de milissegundos para fatores do tamanho do buffer [11]
    attack_factor = np.exp(-1.0 / (fs * (attack_ms / 1000.0)))
    release_factor = np.exp(-1.0 / (fs * (release_ms / 1000.0)))
    
    ganho_aplicado = np.ones_like(banda_alvo)
    ganho_atual = 1.0
    env_atual = 0.0
    
    # 3. Analisa amostra por amostra (Sample by Sample)
    for n in range(len(banda_alvo)):
        # Calcula o Envelope: lê as ondas e ignora quedas abruptas [4]
        env_atual = max(abs(banda_alvo[n]), env_atual * release_factor)
        
        # Calcula o Ganho Alvo (Comprime/Tira ganho se ultrapassar o Threshold) [11]
        if env_atual > threshold_linear:
            target_gain = threshold_linear / env_atual
            target_gain = max(target_gain, max_reducao) # Limita para não silenciar 100%
        else:
            target_gain = 1.0 # Deixa intacto se estiver abaixo do limite
            
        # Suaviza a mudança de ganho aplicando os fatores de Attack e Release [11]
        ganho_atual = ganho_atual * attack_factor + target_gain * (1.0 - attack_factor)
        ganho_aplicado[n] = ganho_atual

    # 4. Multiplica o novo ganho na banda isolada e mistura com o restante do áudio original [8, 12]
    banda_controlada = banda_alvo * ganho_aplicado
    sinal_final = resto_audio + banda_controlada
    
    return sinal_final

# =========================================================
# 3. EXECUTANDO A FERRAMENTA NA MÚSICA
# =========================================================

# Carrega o áudio e a taxa de amostragem usando a biblioteca soundfile [6, 13]
# O áudio precisa estar normalizado entre -1.0 e 1.0
sinal, fs = sf.read("seu_audio.wav")

# Se for estéreo, processamos apenas o canal esquerdo por simplicidade neste exemplo.
if len(sinal.shape) > 1:
    sinal = sinal[:, 0]

# --- PASSO A: Aplicar Limpeza (HPF e LPF do canal) ---
# Corta sub-graves abaixo de 80Hz e ruídos agudos acima de 15000Hz
sinal_limpo = aplicar_hpf_lpf(sinal, fs, hpf_freq=80, lpf_freq=15000)

# --- PASSO B: Aplicar Equalizador Dinâmico Inteligente ---
# Vamos tirar o ganho APENAS da frequência irritante de 4000 Hz, quando ela gritar acima de 0.2 de amplitude.
sinal_processado = equalizador_dinamico(
    sinal=sinal_limpo,
    fs=fs,
    freq_alvo=4000,          # Centro em 4kHz (agudo incômodo)
    largura_banda=1000,      # Atinge a região de 3500Hz a 4500Hz
    threshold_linear=0.2,    # Limite matemático (substitui o limite em dBFS)
    attack_ms=10,            # Age em 10 milissegundos
    release_ms=50,           # Solta o filtro em 50 milissegundos
    max_reducao=0.3          # Reduz até no máximo 30% do volume original da faixa
)

# Exporta o áudio processado e inteligenteizado final
sf.write("audio_inteligente_final.wav", sinal_processado, fs)
print("Processamento concluído com sucesso!")
