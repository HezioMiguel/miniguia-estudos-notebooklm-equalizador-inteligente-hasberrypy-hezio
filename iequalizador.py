from pydub import AudioSegment
from pydub.scipy_effects import eq

def equalizador_inteligente(canais):
    """
    Recebe um dicionário de canais de áudio e aplica HPF, LPF e EQ Dinâmico Paramétrico
    baseado no tipo de instrumento detectado.
    """
    canais_processados = {}
    
    for nome_canal, audio in canais.items():
        
        if nome_canal == "voz":
            # 1. Filtros de Limpeza (HPF e LPF)
            # Remove o ruído grave inútil para a voz e preserva os agudos [4]
            audio = audio.high_pass_filter(100) 
            audio = audio.low_pass_filter(16000)
            
            # 2. EQ Inteligente para a Voz
            # Tira o som nasal (entre 1kHz e 1.5kHz) [10]
            audio = eq(audio, focus_freq=1250, filter_mode="peak", gain=-3, order=2)
            # Adiciona Presença (5kHz) para a voz não ficar sem vida [11, 12]
            audio = eq(audio, focus_freq=5000, filter_mode="peak", gain=2, order=2)
            # Adiciona "Ar" (10kHz) para dar respiração e brilho [13]
            audio = eq(audio, focus_freq=10000, filter_mode="peak", gain=2, order=2)
            
        elif nome_canal == "baixo":
            # 1. Filtros de Limpeza (HPF e LPF)
            # Corta frequências altas que entram em conflito com guitarras e vozes [4]
            audio = audio.high_pass_filter(30)
            audio = audio.low_pass_filter(1000)
            
            # 2. EQ Inteligente para o Baixo
            # Tira a famosa "Lama" (200 Hz), que embola o som na mixagem [10, 14]
            audio = eq(audio, focus_freq=200, filter_mode="peak", gain=-4, order=2)
            
        elif nome_canal == "bateria":
            # 1. Filtros de Limpeza
            audio = audio.high_pass_filter(25)
            
            # 2. EQ Inteligente para a Bateria
            # Remove o "som de lata/caixa" (300Hz a 500Hz) típico de ressonâncias ruins [10]
            audio = eq(audio, focus_freq=400, filter_mode="peak", gain=-4, order=2)
            
        # Adiciona o canal modificado de volta
        canais_processados[nome_canal] = audio
        
    return canais_processados

# ==========================================
# SIMULAÇÃO DE USO DA FERRAMENTA
# ==========================================

# 1. Carregue as faixas (stems) isoladas do seu projeto
canais_originais = {
    "voz": AudioSegment.from_file("voz_isolada.wav"),
    "baixo": AudioSegment.from_file("baixo_isolado.wav"),
    "bateria": AudioSegment.from_file("bateria_isolada.wav")
}

# 2. Processa o EQ Inteligente
canais_mixados = equalizador_inteligente(canais_originais)

# 3. Faz a Mixagem final sobrepondo (overlay) todas as camadas em um arquivo só [15, 16]
mix_final = canais_mixados["bateria"].overlay(canais_mixados["baixo"]).overlay(canais_mixados["voz"])

# 4. Exporta o som final [17]
mix_final.export("mixagem_inteligente_final.mp3", format="mp3")
