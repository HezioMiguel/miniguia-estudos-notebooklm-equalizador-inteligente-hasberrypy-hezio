Python Dynamic EQ: Processador de Áudio em Tempo Real
Um Equalizador Dinâmico Inteligente desenvolvido em Python, projetado para processamento de sinais de áudio (DSP) com latência ultrabaixa em sistemas embarcados, como o Raspberry Pi.

📖 Sobre o Projeto
O projeto consiste no desenvolvimento de uma ferramenta de Processamento Digital de Sinais (DSP) em Python, focada na construção de um Equalizador Dinâmico Inteligente.

A aplicação une filtros tradicionais de limpeza (como o Passa-Alta/HPF e Passa-Baixa/LPF para delimitar o espectro das frequências) aos princípios de processadores de dinâmica, utilizando parâmetros como Attack, Release e Threshold. Diferente de um equalizador paramétrico comum, que altera as frequências de forma estática do início ao fim da música, a ferramenta desenvolvida "ouve" a amplitude do sinal e só dispara a equalização quando uma frequência específica – como a "lama" sonora que embola os graves ao redor de 200 Hz ou a estridência em 3200 Hz – ultrapassa o limite de volume configurado. Isso permite correções automáticas e cirúrgicas que trazem nitidez, brilho e presença, preservando a integridade da faixa nos momentos em que o problema não ocorre.

Do ponto de vista técnico e de engenharia de software, o projeto documenta a superação de um grande desafio: a lentidão do Python puro para processar laços iterativos de áudio amostra por amostra. Para resolver esse gargalo de performance em cenários de processamento ao vivo (tempo real), a arquitetura do projeto adota a compilação Just-In-Time (JIT) com a biblioteca Numba. Essa abordagem permite que as lógicas de envelope e ganho sejam pré-compiladas nativamente em linguagem C, operando com latência ultrabaixa sem perder a flexibilidade da sintaxe do Python, aliados à otimização matemática em domínio logarítmico para extrema economia de processamento.

✨ Principais Recursos (Engenharia de Áudio)
Processamento JIT (Numba): A engine matemática é compilada para código de máquina na inicialização, permitindo que laços de cálculo rodem na velocidade do C++.

Detecção RMS em Tempo Real: O envelope follower reage à energia média da música, evitando artefatos causados por picos (transientes) ultrarrápidos.

Matemática no Domínio Logarítmico: Substituição de operações pesadas de raiz quadrada por propriedades logarítmicas (10 * log10(x^2)), economizando milhares de ciclos de CPU por segundo.

Filtros IIR Stateful (lfilter_zi): Manutenção do estado da fase da onda entre os buffers de áudio, eliminando completamente cliques e estalos (pops) durante o streaming ao vivo.

Recombinação Subtrativa: Preserva a fase do sinal original. Se o áudio não ultrapassa o Threshold, o sinal de saída é bit-a-bit idêntico à entrada (transparência total).

🚀 Como Instalar e Rodar
Pré-requisitos
Certifique-se de ter o Python 3.8+ instalado. Se estiver rodando no Raspberry Pi (Linux), você precisará instalar as dependências do sistema para o PyAudio antes:

Bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio
Instalação das Bibliotecas
Clone este repositório e instale as dependências via pip:

Bash
git clone https://github.com/SEU_USUARIO/python-dynamic-eq.git
cd python-dynamic-eq
pip install numpy scipy soundfile pyaudio numba
Configurando o Hardware (Interface de Áudio)
Para evitar problemas de latência, o uso de uma Interface de Áudio USB é altamente recomendado.

Rode o script uma vez. Ele listará os dispositivos de áudio disponíveis no terminal.

Identifique os IDs da Entrada (Microfone/Instrumento) e da Saída (Fones/Monitores) da sua interface USB.

Abra o arquivo main.py e edite as variáveis IN_ID e OUT_ID com os números correspondentes.

Execução
Após configurar a placa de som, inicie a engine:

Bash
python main.py
A engine fará o Warm-up (compilação do Numba) e iniciará o streaming com latência zero perceptível. Pressione Ctrl+C para encerrar.

🛠️ Ajustando os Parâmetros
Você pode "tunar" o equalizador dinâmico editando as constantes no topo do main.py:

F_TARGET: Frequência alvo em Hz (Ex: 3200.0 para sibilância ou 250.0 para graves embolados).

THRESHOLD_DB: Limite em Decibéis para o EQ começar a atuar (Ex: -18.0).

RATIO: Fator de compressão (Ex: 4.0 para redução agressiva, 2.0 para suavidade).

ATK_MS / REL_MS: Tempos de Attack e Release da curva de compressão (em milissegundos).

💡 Dica para Raspberry Pi (Modo Performance)
Para evitar que o sistema operacional reduza o clock da CPU e cause falhas no áudio, configure o Governor para performance extrema antes de rodar o script:

Bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
📝 Licença
Distribuído sob a licença MIT. Veja LICENSE para mais informações
