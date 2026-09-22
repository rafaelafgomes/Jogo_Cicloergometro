import pygame
import random
import math
import serial
import serial.tools.list_ports  # encontra a porta do ESP32 automaticamente

pygame.init()

# =========================================================================
# ================== TELA VIRTUAL (fixa) x TELA REAL (adaptativa) ========
# =========================================================================
# jogo desenhado numa superfície virtual de 800x600
# superficie escalada para o tamanho real do monitor a cada frame, proporção 4:3
largura_virtual, altura_virtual = 800, 600

_info_monitor = pygame.display.Info()
tela_real = pygame.display.set_mode(
    (_info_monitor.current_w, _info_monitor.current_h), pygame.FULLSCREEN
)
pygame.display.set_caption("Jogo Pedal Espacial")

# 'tela' continua sendo a superfície usada por TODAS as funções de desenho existentes
tela = pygame.Surface((largura_virtual, altura_virtual))

fonte = pygame.font.SysFont(None, 30)
fonte_titulo = pygame.font.SysFont("arialblack", 55)
fonte_pequena = pygame.font.SysFont(None, 20)

clock = pygame.time.Clock()

# =========================================================================
# ============================ ESTADOS DO JOGO ===========================
# =========================================================================
MENU = "MENU"
CONFIGURACAO = "CONFIGURACAO"
JOGO = "JOGO"
FIM = "FIM"

estado = MENU
rodando = True

# =========================================================================
# ============================ CONFIGURAÇÕES ==============================
# =========================================================================
rpm_min = 10.0        # 10 RPM (Abaixo disso é Muito Lento)
rpm_ideal_min = 50.0  # 50 RPM (Início da zona verde)
rpm_ideal_max = 100.0  # 100 RPM (Fim da zona verde)
rpm_max = 140.0        # 140.0 RPM 
config_opcao = 0
usar_obstaculos = True

# =========================================================================
# ======================== EVENTOS / OBSTÁCULOS ===========================
# =========================================================================
tempo_ultimo_evento = pygame.time.get_ticks()
evento_ativo = False
tempo_inicio_evento = 0
tipo_evento_atual = None  # "asteroide", "tempestade" ou "gravidade"
duracao_evento = 10000    # 10 segundos em milissegundos

shake_tela = 0
flash_impacto = 0
particulas_asteroide = []

# =========================================================================
# ================================ FASES ===================================
# =========================================================================
fases = [
    {"nome": "Mercúrio", "distancia": 30}, #era 600
    {"nome": "Vênus", "distancia":60}, #era 120
    {"nome": "Marte", "distancia": 90}, #era 300
    {"nome": "Saturno", "distancia": 120}, #era 1000
]

fase_atual = 0
distancia_total = fases[fase_atual]["distancia"]
distancia_restante = distancia_total

# =========================================================================
# =============================== JOGO =====================================
# =========================================================================
tempo_na_zona_ideal = 0  # ms contínuos na zona verde
multiplicador = 1        # 1x normal, 2x após 30s contínuos na zona ideal

jogo_pausado = False

velocidade = 0
velocidade_kmh = 0
progresso = 0  # porcentagem da distância percorrida
pontuacao = 0

tempo_inicio = pygame.time.get_ticks()
tempo_pontos = pygame.time.get_ticks()
ultimo_tempo = pygame.time.get_ticks()

tempo_final = 0
tempo_pausado = 0
inicio_pausa = 0

nave_x_inicial = 120
nave_x_final = 520
nave_x = nave_x_inicial

nave_y_base = 300
nave_y = nave_y_base
vel_nave_y = 0
tempo_mudar_movimento = pygame.time.get_ticks()

planeta_y_base = 300
planeta_x = 600
planeta_y = planeta_y_base

animacao_chegada = False
informacao_aberta = False

intervalo_proximo_evento = 0

# =========================================================================
# ================================ BARRAS =================================
# =========================================================================
barra_x = 150
barra_y = 550
barra_largura = 500
barra_altura = 20

barra_prog_x = 250
barra_prog_y = 100
barra_prog_largura = 500
barra_prog_altura = 20

# =========================================================================
# ============================ ESP32 (bike) =================================
# =========================================================================
esp32 = None
rpm_atual_bike = 0.0
direcao_atual_bike = "PARADO"

# Preenchidos no main() antes do loop começar
estrelas = []
linhas_velocidade = []
imagens_planetas = {}
nave_img = None

circunferencia_roda = 0.54
rpm_max_hardware = 160.0 # teto real do cicloergômetro/sensor

#controle pelo teclado
rpm_teclado = 0.0
direcao_teclado = "PARADO"
aceleracao_teclado = 45.0
desaceleracao_teclado = 35.0

# =========================================================================
# =========================================================================
# ================================ FUNÇÕES =================================
# =========================================================================
# =========================================================================

# ------------------------ Ajustes de resolução de tela ---------------------
def _calcular_escala_tela():
    largura_real, altura_real = tela_real.get_size()
    escala = min(largura_real / largura_virtual, altura_real / altura_virtual)
    largura_escalada = int(largura_virtual * escala)
    altura_escalada = int(altura_virtual * escala)
    offset_x = (largura_real - largura_escalada) // 2
    offset_y = (altura_real - altura_escalada) // 2
    return escala, offset_x, offset_y, largura_escalada, altura_escalada

def atualizar_tela_real():
    #Escala a tela virtual (800x600) para a tela real e mostra na tela, mantendo a proporção
    tela_real.fill((0, 0, 0))
    tela_escalada = pygame.transform.smoothscale(tela, (largura_tela_escalada, altura_tela_escalada))
    tela_real.blit(tela_escalada, (offset_x_tela, offset_y_tela))
    pygame.display.update()

def _mouse_get_pos_virtual():
    mx_real, my_real = _mouse_get_pos_original()
    mx_virtual = (mx_real - offset_x_tela) / escala_tela
    my_virtual = (my_real - offset_y_tela) / escala_tela
    return int(mx_virtual), int(my_virtual)
    
# Inicialização que depende das funções
escala_tela, offset_x_tela, offset_y_tela, largura_tela_escalada, altura_tela_escalada = _calcular_escala_tela()

_mouse_get_pos_original = pygame.mouse.get_pos

pygame.mouse.get_pos = _mouse_get_pos_virtual

# ------------------------- Criação de elementos visuais -------------------
def criar_estrelas(quantidade=200):
    #Cria a lista de estrelas do fundo, com 3 camadas de profundidade (paralaxe)
    lista = []
    for _ in range(quantidade):
        x = random.randint(0, 800)
        y = random.randint(0, 600)
        camada = random.choice([1, 2, 3])

        if camada == 1:
            vel_estrela, tamanho = 0.3, 1
        elif camada == 2:
            vel_estrela, tamanho = 0.7, 2
        else:
            vel_estrela, tamanho = 1.5, 3

        lista.append([x, y, vel_estrela, tamanho])
    return lista


def criar_linhas_velocidade(quantidade=40):
    #Cria as linhas usadas no efeito visual de alta velocidade
    lista = []
    for _ in range(quantidade):
        lista.append([random.randint(0, 800), random.randint(0, 600), random.randint(10, 30)])
    return lista


def carregar_imagens():
    #Carrega e redimensiona as imagens dos planetas e da nave.
    #Encerra o jogo com uma mensagem clara se algum arquivo estiver faltando.
    try:
        mercurio_img = pygame.transform.scale(pygame.image.load("imagens/mercurio.png").convert_alpha(), (220, 220))
        venus_img = pygame.transform.scale(pygame.image.load("imagens/venus.png").convert_alpha(), (240, 240))
        marte_img = pygame.transform.scale(pygame.image.load("imagens/marte.png").convert_alpha(), (230, 230))
        saturno_img = pygame.transform.scale(pygame.image.load("imagens/saturno.png").convert_alpha(), (320, 220))
        img_nave = pygame.transform.scale(pygame.image.load("imagens/nave.png").convert_alpha(), (80, 50))
    except pygame.error as e:
        print(f"\n[ERRO] Não foi possível carregar as imagens locais! Garanta que os arquivos .png estão na mesma pasta. {e}")
        pygame.quit()
        exit()

    imagens = {
        "Mercúrio": mercurio_img,
        "Vênus": venus_img,
        "Marte": marte_img,
        "Saturno": saturno_img,
    }
    return imagens, img_nave

#---------------------------------- Detecção ESP 32 -----------------------------------------------------------------
def detectar_esp32():
    #Procura uma porta serial compatível e tenta conectar ao ESP32.
    #Retorna o objeto Serial conectado, ou None (o jogo roda em modo de simulação por teclado).
    
    for p in serial.tools.list_ports.comports():
        
        descricao = (p.description or "").upper()
        fabricante = (p.manufacturer or "").upper()

        print("PORTA:", p.device)
        print("DESCRIÇÃO:", p.description)
        print("FABRICANTE:", p.manufacturer)
        print("-------------------------")
        
        # Procura especificamente características do ESP32
        if "USB JTAG" in descricao or "ESP32" in descricao:
            try:
                conexao = serial.Serial(p.device, 115200, timeout=0.01)
                print(f"[SUCESSO] Conectado ao ESP32 na porta {p.device}")
                return conexao
           
            except Exception as e:
                print(f"[AVISO] Porta {p.device} encontrada, mas falhou ao abrir: {e}")

    print("[AVISO] Nenhum ESP32 detectado. O jogo rodará em modo de simulação (Teclado).")
    return None

def ler_esp32():
    #Lê uma linha da serial do ESP32 (se houver dado disponível) e atualiza a RPM/direção lidas.
    global rpm_atual_bike, direcao_atual_bike
    if esp32 and esp32.in_waiting > 0:
        try:
            linha = esp32.readline().decode('utf-8').strip()
            if "RPM:" in linha and "," in linha:
                partes = linha.split(",")
                texto_rpm = partes[0].replace("RPM:", "")
                rpm_atual_bike = float(texto_rpm)
                direcao_atual_bike = partes[1]
        except Exception:
            pass

def limpar_leitura_esp32():
    #Descarta dados antigos da bicicleta e zera a leitura atual.
    global rpm_atual_bike, direcao_atual_bike

    rpm_atual_bike = 0.0
    direcao_atual_bike = "PARADO"

    if esp32:
        try:
            esp32.reset_input_buffer()
        except Exception:
            pass

# ------------------------------- UI genérica -------------------------------
def desenhar_botao(texto, x, y, w, h, selecionado=False):
    #Desenha um botão retangular com texto centralizado, com destaque quando 'selecionado'.
    cor_fundo = (60, 80, 120) if selecionado else (40, 50, 75)
    cor_borda = (0, 255, 255) if selecionado else (100, 100, 100)

    pygame.draw.rect(tela, cor_fundo, (x, y, w, h), border_radius=8)
    pygame.draw.rect(tela, cor_borda, (x, y, w, h), 2, border_radius=8)

    texto_surf = fonte.render(texto, True, (255, 255, 255))
    texto_rect = texto_surf.get_rect(center=(x + w // 2, y + h // 2))
    tela.blit(texto_surf, texto_rect)


def clicou(x, y, w, h):
    #Retorna True se o mouse estiver sobre a área (x, y, w, h) e o botão esquerdo estiver pressionado.
    mx, my = pygame.mouse.get_pos()
    return x <= mx <= x + w and y <= my <= y + h and pygame.mouse.get_pressed()[0]


# ---------------------------- Cálculos de treino ----------------------------
def calcular_rpm_suave(rpm_hardware, rpm_antigo):
    #Filtra variações bruscas da leitura, criando uma transição macia (suavização exponencial).
    rpm_alvo = max(0.0, min(rpm_hardware, rpm_max_hardware))
    return (rpm_antigo * 0.7) + (rpm_alvo * 0.3)


def obter_status_treino(rpm_atual, limite_min):
    #Classifica a RPM atual em 'Lento', 'Ideal' ou 'Rápido', comparando com os limites configurados
    if rpm_atual < limite_min:
        return "Lento", (255, 0, 0)
    elif limite_min <= rpm_atual <= rpm_ideal_max:
        return "Ideal", (0, 255, 0)
    else:
        return "Rápido", (255, 0, 0)

def rpm_velocidadekm(circunferencia_roda, velocidade):
    return (velocidade * circunferencia_roda * 60) / 1000
    

# --------------------------- Controle de missão -----------------------------
def resetar_missao():
    #Reinicia todas as variáveis de uma tentativa de missão.
    #Usado tanto ao clicar em INICIAR no menu quanto em REINICIAR na tela de fim (antes esse bloco estava duplicado nos dois lugares)
    global progresso, velocidade, pontuacao
    global evento_ativo, tipo_evento_atual, tempo_ultimo_evento, particulas_asteroide
    global distancia_total, distancia_restante
    global tempo_inicio, ultimo_tempo, nave_x, tempo_final
    global tempo_pausado, inicio_pausa
    global tempo_na_zona_ideal, multiplicador, animacao_chegada

    progresso = 0
    velocidade = 0
    pontuacao = 0

    # Zera qualquer leitura antiga da bicicleta
    limpar_leitura_esp32()   
    
    evento_ativo = False
    tipo_evento_atual = None
    tempo_ultimo_evento = pygame.time.get_ticks()
    particulas_asteroide = []

    distancia_total = fases[fase_atual]["distancia"]
    distancia_restante = distancia_total

    tempo_inicio = pygame.time.get_ticks()
    ultimo_tempo = pygame.time.get_ticks()
    tempo_final = 0
    
    tempo_pausado = 0
    inicio_pausa = 0
    
    nave_x = nave_x_inicial
    
    tempo_na_zona_ideal = 0
    multiplicador = 1

    animacao_chegada = False

# --------------------------------- Fundo ------------------------------------
def desenhar_fundo():
    #Desenha o gradiente espacial e move/desenha as estrelas do fundo (usado em todas as telas).
    for y in range(600):
        cor = int(10 + (y / 600) * 35)
        pygame.draw.line(tela, (5, 5, cor), (0, y), (800, y))

    if estado != JOGO:
        vel_menu = 0.2
    elif jogo_pausado:
        vel_menu = 0
    elif animacao_chegada:
        vel_menu = 0  # a animação controla o fundo
    else:
        vel_menu = velocidade / 15.0
        
    for estrela in estrelas:
        estrela[0] -= vel_menu * estrela[2]
        if estrela[0] < 0:
            estrela[0] = 800
            estrela[1] = random.randint(0, 600)
        brilho = random.randint(150, 225)
        pygame.draw.circle(tela, (brilho, brilho, brilho), (int(estrela[0]), int(estrela[1])), estrela[3])
        
#------------------------------------ Animação chegada ----------------------------------
def animar_chegada():
    global nave_x, animacao_chegada, estado

    # Movimento da nave para a direita
    nave_x += 6

    # Movimento do fundo
    for estrela in estrelas:
        estrela[0] -= 3 * estrela[2]

        if estrela[0] < 0:
            estrela[0] = 800
            estrela[1] = random.randint(0, 600)

    # Se a nave saiu da tela
    if nave_x > 800:
        animacao_chegada = False
        estado = FIM
        
#----------------------------------- Aviso de pedalada para trás -------------------------------------        
def desenhar_aviso_pedal_tras():
    # Exibe um aviso quando o usuário estiver pedalando para trás
    titulo = fonte.render("PEDALANDO PARA TRÁS", True, (255, 80, 80))
    mensagem = fonte.render("Pedale para frente para continuar", True, (255, 255, 255))
    # Caixa de aviso
    largura = 430
    altura = 90
    x = (largura_virtual - largura) // 2 
    y = 100
    
    pygame.draw.rect(tela, (25, 35, 55), (x, y, largura, altura), border_radius = 10)
    pygame.draw.rect(tela, (0, 255, 255), (x, y, largura, altura), 2, border_radius = 10)
    
    tela.blit(titulo, (largura_virtual // 2 - titulo.get_width() // 2, y + 15))
    tela.blit(mensagem, (largura_virtual // 2 - mensagem.get_width() // 2, y + 50))
    
# ------------------------------------------- Sistema de obstáculos --------------------------------------
def iniciar_evento(tipo_evento):
    # Inicia o obstaculo e registra o momento do inicio_pausa
    global evento_ativo, tempo_inicio_evento, tipo_evento_atual
    evento_ativo = True
    tempo_inicio_evento = pygame.time.get_ticks()
    tipo_evento_atual = tipo_evento
    
def verificar_inicio_evento(tempo_atual):
    # Verifica se está na hora de iniciar o evento
    global intervalo_proximo_evento
    # Se tem evento ativo e o progresso é maior que 55%, não inicia
    if evento_ativo:
        return
    if progresso >= 0.55:
        return
    if intervalo_proximo_evento == 0:
        # escolhe entre: 30.000 ms e 40.000 ms
        intervalo_proximo_evento = random.randint(30000, 40000)
    
    if tempo_atual - tempo_ultimo_evento > intervalo_proximo_evento:
        # Quanto tempo passou desde o último evento? Se passou mais que o intervalo, começa outro evento
        tipo = random.choice(["asteroide","tempestade"])
        iniciar_evento(tipo)
        intervalo_proximo_evento = 0
        
def verificar_inicio_gravidade():
    #inicia gravidade aos 70%
    if evento_ativo:
        return
    if progresso >= 0.7:
        iniciar_evento("gravidade")

def verificar_fim_evento(tempo_atual):
    # verifica se o evento atual acabou
    global evento_ativo, tipo_evento_atual, tempo_ultimo_evento
    
    if not evento_ativo:
        return
    
    if tempo_atual - tempo_inicio_evento > duracao_evento:
        # Quanto tempo passou desde que o evento começou? Se passou mais que duração do evento, desativa evento e limpa evento
        evento_ativo = False
        tipo_evento_atual = None
        tempo_ultimo_evento = tempo_atual


def aplicar_efeito_evento(status):
    # Efeitos de acordo com a velocidade do usuário
    global pontuacao, flash_impacto, shake_tela, velocidade_avanco
    
    if not evento_ativo:
        return

    if tipo_evento_atual in ("asteroide", "tempestade"):
        if status != "Ideal":
            # Obstáculo penaliza o jogador se ele não estiver na velocidade ideal.
            if flash_impacto == 0:
                # Tempo de proteção após o impacto, para não perder ponto a cada frame
                pontuacao = int(pontuacao / 2)
                # variaveis para efeitos visuais
                flash_impacto = 30
                shake_tela = 15
            velocidade_avanco = 0
    elif tipo_evento_atual == "gravidade":
        # A gravidade só prejudica quem está pedalando rápido demais.
        if status == "Rápido":
            shake_tela = 5
            velocidade_avanco = 0.05
    
#=======================================================================================
# Menu
#=======================================================================================
def tela_menu(teclas):
    #Desenha e processa a tela de menu inicial (Iniciar / Configurações / Sair).
    global estado, rodando

    titulo_sombra = fonte_titulo.render("Pedal Espacial", True, (50, 55, 65))
    tela.blit(titulo_sombra, titulo_sombra.get_rect(center=(403, 103)))

    titulo_surf = fonte_titulo.render("Pedal Espacial", True, (0, 255, 255))
    tela.blit(titulo_surf, titulo_surf.get_rect(center=(400, 100)))

    mx, my = pygame.mouse.get_pos()
    sel_iniciar = (300 <= mx <= 520 and 200 <= my <= 250)
    sel_config = (300 <= mx <= 520 and 280 <= my <= 330)
    sel_sair = (300 <= mx <= 520 and 360 <= my <= 410)

    desenhar_botao("INICIAR", 300, 200, 220, 50, selecionado=sel_iniciar)
    desenhar_botao("CONFIGURAÇÕES", 300, 280, 220, 50, selecionado=sel_config)
    desenhar_botao("SAIR", 300, 360, 220, 50, selecionado=sel_sair)

    if teclas[pygame.K_ESCAPE]:
        rodando = False

    if clicou(300, 200, 220, 50):
        resetar_missao()
        estado = JOGO
        pygame.time.delay(150)

    if clicou(300, 280, 220, 50):
        estado = CONFIGURACAO
        pygame.time.delay(150)

    if clicou(300, 360, 220, 50):
        rodando = False

#=======================================================================================
# Configuração
#=======================================================================================
def tela_configuracao(teclas):
    #Desenha e processa a tela de configuração dos limites de RPM, missão e obstáculos
    global estado, config_opcao, rpm_min, rpm_ideal_min, rpm_ideal_max, rpm_max
    global fase_atual, usar_obstaculos, informacao_aberta

    #============================ Titulo ==================================
    titulo_surf = fonte.render("CONFIGURAÇÕES DO EXERCÍCIO", True, (255, 255, 0))
    tela.blit(titulo_surf, titulo_surf.get_rect(center=(400, 60)))

    #================================== Opções de configurações ==================================
    opcoes = [
        {"id": 0, "nome": "RPM Mínimo", "valor": f"{rpm_min:.0f}"},
        {"id": 1, "nome": "RPM Ideal Mínimo", "valor": f"{rpm_ideal_min:.0f}"},
        {"id": 2, "nome": "RPM Ideal Máximo", "valor": f"{rpm_ideal_max:.0f}"},
        {"id": 3, "nome": "RPM Máximo", "valor": f"{rpm_max:.0f}"},
        {"id": 4, "nome": "Missão de Destino", "valor": f"{fases[fase_atual]['nome']}"},
        {"id": 5, "nome": "Obstáculos no Percurso", "valor": "Ligado" if usar_obstaculos else "Desligado"},
    ]

    mx, my = pygame.mouse.get_pos()
    clique_mouse = pygame.mouse.get_pressed()[0]

    ajuste_valor = 0  # -1 para diminuir, 1 para aumentar
    opcao_clicada = -1

    #================================== Desenha as opções ==================================
    for i, opcao in enumerate(opcoes):
        # Espaçamento das opções
        y_pos = 85 + i * 48
        cor_texto = (0, 255, 255) if i == config_opcao else (255, 255, 255)

        # Área da opção
        if 100 <= mx <= 700 and y_pos <= my <= y_pos + 40:
            pygame.draw.rect(tela, (30, 40, 65), (100, y_pos, 660, 40), border_radius=6)
            if clique_mouse:
                config_opcao = i

        # Nome da configuração
        nome_surf = fonte.render(opcao["nome"], True, cor_texto)
        tela.blit(nome_surf, (120, y_pos + 8))
        
        #================================== Posição dos botões ==================================
        centro_controles = 550

        if opcao["id"] in (4, 5):
            distancia_botoes = 105
        else:
            distancia_botoes = 75

        bx_menos = centro_controles - distancia_botoes
        bx_mais = centro_controles + distancia_botoes

        by_menos = y_pos + 3
        by_mais = y_pos + 3

        b_largura, b_altura = 40, 34
        
        # Verifica mouse sobre -  e +
        hover_menos = (bx_menos <= mx <= bx_menos + b_largura and by_menos <= my <= by_menos + b_altura)
        hover_mais = (bx_mais <= mx <= bx_mais + b_largura and by_mais <= my <= by_mais + b_altura)

        # Desenha os botões
        desenhar_botao("-", bx_menos, by_menos, b_largura, b_altura, selecionado=hover_menos)
        desenhar_botao("+", bx_mais, by_mais, b_largura, b_altura, selecionado=hover_mais)

        #================================== Valor ==================================
        centro_x = (bx_menos + b_largura + bx_mais) // 2
        valor_surf = fonte.render(opcao["valor"], True, (255, 255, 255))
        tela.blit(valor_surf, valor_surf.get_rect(center=(centro_x, y_pos + 20)))

        #================================== Clique nos botões ==================================
        if clique_mouse:
            if hover_menos:
                ajuste_valor, opcao_clicada = -1, i
            elif hover_mais:
                ajuste_valor, opcao_clicada = 1, i

    #================================== Controle pelo teclado ==================================
    # Aumentar
    if teclas[pygame.K_RIGHT] or (ajuste_valor == 1):
        if config_opcao == 0: rpm_min += 5
        elif config_opcao == 1: rpm_ideal_min += 5
        elif config_opcao == 2: rpm_ideal_max += 5
        elif config_opcao == 3: rpm_max += 5
        elif config_opcao == 4: fase_atual = (fase_atual + 1) % len(fases)
        elif config_opcao == 5: usar_obstaculos = not usar_obstaculos
        pygame.time.delay(150)

    # Diminuir
    if teclas[pygame.K_LEFT] or (ajuste_valor == -1):
        if config_opcao == 0: rpm_min -= 5
        elif config_opcao == 1: rpm_ideal_min -= 5
        elif config_opcao == 2: rpm_ideal_max -= 5
        elif config_opcao == 3: rpm_max -= 5
        elif config_opcao == 4: fase_atual = (fase_atual - 1) % len(fases)
        elif config_opcao == 5: usar_obstaculos = not usar_obstaculos
        pygame.time.delay(150)

    # Subir opção
    if teclas[pygame.K_UP]:
        config_opcao = (config_opcao - 1) % len(opcoes)
        pygame.time.delay(150)
    
    # Descer opção
    if teclas[pygame.K_DOWN]:
        config_opcao = (config_opcao + 1) % len(opcoes)
        pygame.time.delay(150)

    # ESC para voltar
    if teclas[pygame.K_ESCAPE]:
        estado = MENU
        pygame.time.delay(200)

    # =================== Validações de segurança dos limites ==============================
    # Impede configuração inconsistente
    rpm_min = max(0, min(rpm_min, rpm_max_hardware))
    rpm_ideal_min = max(rpm_min, min(rpm_ideal_min, rpm_max_hardware))
    rpm_ideal_max = max(rpm_ideal_min, min(rpm_ideal_max, rpm_max_hardware))
    rpm_max = max(rpm_ideal_max, min(rpm_max, rpm_max_hardware))
    
    # ==================== Informação da missão ========================================
    distancia = fases[fase_atual]["distancia"]
    nome_planeta = fases[fase_atual]["nome"]

    pygame.draw.line(tela, (80, 80, 100), (120, 380), (780, 380), 1)

    titulo_missao = fonte.render("Informações da missão:", True, (0, 255, 255))
    tela.blit(titulo_missao, titulo_missao.get_rect(center=(400, 397)))

    texto_missao = (f"Destino: {nome_planeta}    |    "f"Distância da missão: {distancia} m")
    missao_surf = fonte.render(texto_missao, True, (255, 255, 255))
    tela.blit(missao_surf, missao_surf.get_rect(center=(400, 422)))
    
    # ========================== Botão voltar ================================
    sel_voltar = (300 <= mx <= 500 and 520 <= my <= 570)
    desenhar_botao("VOLTAR", 300, 520, 200, 50, selecionado=sel_voltar)

    if sel_voltar and clique_mouse:
        estado = MENU
        pygame.time.delay(200)

    # ===================== Menu suspenso - Informação sobre RPM ====================================
    # Botão de informações
    sel_botao_informacao = (655 <= mx <= 655 + 130 and 12 <= my <= 12 + 35)
    desenhar_botao("Informação", 655, 12, 130, 35, selecionado=sel_botao_informacao)
    
    # Abre a janela ao clicar
    if sel_botao_informacao and clique_mouse:
        informacao_aberta = True
        pygame.time.delay(150)
    
    if informacao_aberta:
        # Menu suspenso de informação
        # Fundo escuro sobre a tela
        superficie_foco = pygame.Surface((800, 600), pygame.SRCALPHA)
        superficie_foco.fill((0, 0, 0, 180))
        tela.blit(superficie_foco, (0, 0))

        # Janela de informações
        pygame.draw.rect(tela, (25, 35, 55), (100, 70, 600, 460), border_radius=12)
        pygame.draw.rect(tela, (0, 255, 255), (100, 70, 600, 460), 2, border_radius=12)

        # Titulo
        titulo_info = fonte.render("Informações do Jogo Pedal Espacial", True, (0, 255, 255))
        tela.blit(titulo_info, titulo_info.get_rect(center=(400, 100)))
        
        # Seção RPM
        titulo_rpm = fonte.render("Como interpretar os RPM", True, (255, 255, 0))
        tela.blit(titulo_rpm, (140, 140))
        
        explicacoes_rpm = [
            "RPM = rotações por minuto da pedalada.",
            "Abaixo do RPM Mínimo: ritmo abaixo do esperado.",
            "Faixa Ideal: entre o RPM Ideal Mínimo e o RPM Ideal Máximo.",
            "Acima do RPM Máximo: ritmo acima do limite configurado."
        ]

        y_texto = 170

        for texto in explicacoes_rpm:
            texto_surf = fonte_pequena.render( texto, True, (230, 230, 230))
            tela.blit(texto_surf, (140, y_texto))
            y_texto += 25
        
        # Seção como jogar
        titulo_jogo = fonte.render("Como jogar", True, (255, 255, 0))
        tela.blit(titulo_jogo, (140, 285))
        
        explicacoes_jogo = [
            "Mantenha a pedalada na faixa ideal para movimentar a nave e ganhar pontos.",
            "Ao permanecer 20 segundos na faixa ideal, você recebe um bônus de pontuação.",
            "A nave avança em direção ao planeta escolhido.",
            "Obstáculos podem aparecer durante o percurso.", 
            "Mantenha a pedalada na faixa ideal para evitar penalizações.",
            "As penalizações por obstáculos dimuiem os pontos pela metade.",
            "Ao se aproximar do destino, reduza gradualmente a pedalada.",
            "A gravidade só prejudica quem está pedalando rápido demais."
        ]

        y_texto = 315

        for texto in explicacoes_jogo:
            texto_surf = fonte_pequena.render( texto, True, (230, 230, 230))
            tela.blit(texto_surf, (140, y_texto))
            y_texto += 24

        # Botão comtinuar
        sel_continuar = (280 <= mx <= 520 and 480 <= my <= 525)
        desenhar_botao("CONTINUAR", 280, 480, 240, 45, selecionado=sel_continuar)

        if sel_continuar and clique_mouse:
            informacao_aberta = False
            pygame.time.delay(200)

#=======================================================================================
# Jogo
#=======================================================================================
def tela_jogo(teclas):
    #Desenha e processa a fase JOGO: leitura da bike/teclado, física da nave, obstáculos, HUD e pausa.
    global estado, jogo_pausado
    global velocidade, velocidade_kmh, progresso, distancia_restante, nave_x, nave_y, vel_nave_y
    global tempo_mudar_movimento, tempo_na_zona_ideal, multiplicador
    global tempo_pontos, pontuacao, ultimo_tempo, tempo_final
    global evento_ativo, tipo_evento_atual, tempo_inicio_evento, tempo_ultimo_evento
    global flash_impacto, shake_tela, particulas_asteroide
    global animacao_chegada, tempo_pausado, inicio_pausa, direcao_atual_bike, rpm_entrada

    tempo_atual = pygame.time.get_ticks()
    mx, my = pygame.mouse.get_pos()
    clique_mouse = pygame.mouse.get_pressed()[0]

    # Atalho no teclado: ESC pausa ou despausa o jogo
    if teclas[pygame.K_ESCAPE]:
        jogo_pausado = not jogo_pausado
        if jogo_pausado:
            inicio_pausa = pygame.time.get_ticks()
        else:
            tempo_pausado += pygame.time.get_ticks() - inicio_pausa
            ultimo_tempo = pygame.time.get_ticks()
            limpar_leitura_esp32()
        pygame.time.delay(200)


    if not jogo_pausado and not animacao_chegada:
        rpm_entrada = 0.0
        esp32 = detectar_esp32()
        if esp32 is None:
            # Simulação pelo teclado 
            if teclas[pygame.K_UP]:
                velocidade += 2
                direcao_atual_bike = "FRENTE"
                
                if velocidade > rpm_max_hardware:
                    velocidade = rpm_max_hardware
                
            elif teclas[pygame.K_DOWN]:
                direcao_atual_bike = "TRAS"
                velocidade = 0.0
             
            else:
                direcao_atual_bike = "PARADO"
                velocidade *= 0.98
            
        else:
            ler_esp32()
            # controle de atualização da velocidade pela bike
            if direcao_atual_bike == "TRAS":
                rpm_entrada = 0.0
            else:
                rpm_entrada = rpm_atual_bike
                
        
            velocidade = calcular_rpm_suave(rpm_entrada, velocidade)
        
        velocidade_kmh = rpm_velocidadekm(circunferencia_roda, velocidade)

        # Controle dinâmico da zona verde (reta final expande a zona ideal)
        limite_ideal_min_atual = rpm_ideal_min
        if progresso > 0.7:
            limite_ideal_min_atual = 0

        status, cor_status = obter_status_treino(velocidade, limite_ideal_min_atual)

        # muda o comportamento vertical da nave só de vez em quando
        if tempo_atual - tempo_mudar_movimento > random.randint(1200, 2500):
            vel_nave_y = random.uniform(-0.25, 0.25)
            tempo_mudar_movimento = tempo_atual
        nave_y += vel_nave_y
        if nave_y < nave_y_base - 8:
            nave_y = nave_y_base - 8
            vel_nave_y *= -1
        if nave_y > nave_y_base + 8:
            nave_y = nave_y_base + 8
            vel_nave_y *= -1

        # Atrito natural: velocidade decai se parar de pedalar <<<<< essa parte está fazendo a velocidade travar
        velocidade = max(0, min(velocidade, rpm_max_hardware))

        # ======= Sistema de pontuação e bônus =======
        delta_tempo = (tempo_atual - ultimo_tempo) / 1000
        ultimo_tempo = tempo_atual

        if status == "Ideal":
            tempo_na_zona_ideal += delta_tempo * 1000
            multiplicador = 2 if tempo_na_zona_ideal >= 30000 else 1
        else:
            tempo_na_zona_ideal = 0
            multiplicador = 1

        if tempo_atual - tempo_pontos >= 1000:
            if status == "Ideal":
                pontuacao += 10 * multiplicador
            tempo_pontos = tempo_atual

        # ======= Cálculo de avanço da distância (só avança na zona ideal) =======
        velocidade_avanco = (velocidade / 60.0) * circunferencia_roda if status == "Ideal" else 0

        # ===================== Sistema de eventos e obstáculos =====================================
        # Quando um evento aparece, qual evento será, quanto tempo ele dura e o que acontece com a nave/pontuação durante o evento
        if usar_obstaculos:
            verificar_inicio_evento(tempo_atual)
            verificar_inicio_gravidade()
            verificar_fim_evento(tempo_atual)
            aplicar_efeito_evento(status)
        else:
            evento_ativo = False
            tipo_evento_atual = None

        # ============== Atualiza a distância =========================
        distancia_restante -= velocidade_avanco * delta_tempo
        distancia_restante = max(0, distancia_restante)
        progresso = 1 - (distancia_restante / distancia_total)
        nave_x = nave_x_inicial + (progresso * (nave_x_final - nave_x_inicial))

        # ============ movimento do cenário de fundo ==================
        if (velocidade / 15.0) > rpm_ideal_max * 0.8:
            for linha in linhas_velocidade:
                linha[0] -= (velocidade / 15.0) * 5
                if linha[0] < 0:
                    linha[0] = 800
                    linha[1] = random.randint(0, 600)

    else:
        ultimo_tempo = tempo_atual
        status = "Pausado"
        cor_status = (255, 255, 0)
        
    #=================================== Animação de chegada ================================
    if animacao_chegada:
        animar_chegada()

    # ================================== Renderização gráfica (HUD) =================
    for estrela in estrelas:
        brilho = random.randint(150, 225)
        pygame.draw.circle(tela, (brilho, brilho, brilho), (int(estrela[0]), int(estrela[1])), estrela[3])

    if not jogo_pausado and (velocidade / 15.0) > rpm_ideal_max * 0.8:
        for linha in linhas_velocidade:
            pygame.draw.line(tela, (255, 255, 255), (linha[0], linha[1]), (linha[0] + linha[2], linha[1]), 2)

    # ======= Desenho do planeta com efeito de aproximação dinâmica =================
    nome_planeta = fases[fase_atual]["nome"]
    
    if progresso >= 0.7: 
        img_original = imagens_planetas[nome_planeta]
        
        if nome_planeta == "Saturno":
            fator_planeta = 3.6
        else:
            fator_planeta = 3.0
        
        # Progresso do planeta: 0 quando chega em 70%, 1 quando chega em 100%
        progresso_planeta = (progresso - 0.7) / 0.3
        progresso_planeta = max(0, min(1, progresso_planeta))

        # Crescimento do planeta somente entre 70% e 100%
        fator_escala = (0.01 + (progresso_planeta * 2.95))*fator_planeta

        nova_largura = int(img_original.get_width() * fator_escala)
        nova_altura = int(img_original.get_height() * fator_escala)
        
        img_dinamica = pygame.transform.smoothscale(img_original, (max(1, nova_largura), max(1, nova_altura)))
        
        # movimento horizontal direita proporcional ao crescimento
        deslocamento_planeta_x = (fator_escala -(0.01 * fator_planeta)) * 80
        posicao_planeta_x = planeta_x + deslocamento_planeta_x
        
        # Pequena oscilação vertical
        balanco_planeta_y = math.sin(tempo_atual * 0.002) * 4 if not jogo_pausado else 0

        # planeta
        tela.blit(img_dinamica, (posicao_planeta_x - nova_largura // 2, (planeta_y + balanco_planeta_y) - nova_altura // 2))

    # ============== Sistema de tremor por causa do obstáculo =========================
    deslocamento_shake = 0
    if shake_tela > 0:
        deslocamento_shake = random.randint(-shake_tela, shake_tela)
        shake_tela -= 1
    
    # =============== Partículas do obstáculo asteroide =========================
    if evento_ativo and tipo_evento_atual == "asteroide":
        if not jogo_pausado:
            if len(particulas_asteroide) < 25:
                particulas_asteroide.append([
                    820,
                    random.randint(180, 480),
                    random.uniform(6, 14),
                    random.randint(2, 6),
                    random.choice([(255, 80, 0), (220, 110, 20), (130, 130, 130)]),
                ])
            for p in particulas_asteroide:
                p[0] -= p[2]
            particulas_asteroide = [p for p in particulas_asteroide if p[0] > -10]

        for p in particulas_asteroide:
            pygame.draw.line(tela, p[4], (int(p[0]), int(p[1])), (int(p[0] + p[2] * 1.5), int(p[1])), 1)
            pygame.draw.circle(tela, p[4], (int(p[0]), int(p[1])), p[3])

    # ==================== Desenho da nave =======================================
    tela.blit(nave_img, (nave_x, nave_y + deslocamento_shake))

    # =======================Flash de impacto ===================================
    if flash_impacto > 0:
        superficie_colisao = pygame.Surface((800, 600), pygame.SRCALPHA)
        superficie_colisao.fill((255, 0, 0, 120))
        tela.blit(superficie_colisao, (0, 0))
        flash_impacto -= 1

    if evento_ativo and tipo_evento_atual == "tempestade":
        superficie_tempestade = pygame.Surface((800, 600), pygame.SRCALPHA)
        superficie_tempestade.fill((30, 10, 50, 160))
        tela.blit(superficie_tempestade, (0, 0))

    # ================================ Cronômetro da partida =============================
    if animacao_chegada:
        tempo_seg = tempo_final
    else:
        if jogo_pausado:
            tempo_decorrido = inicio_pausa - tempo_inicio - tempo_pausado
        else:
            tempo_decorrido = tempo_atual - tempo_inicio - tempo_pausado
        tempo_seg = max(0, tempo_decorrido // 1000)
    
    minutos = tempo_seg // 60
    segundos = tempo_seg % 60

    # ============================================== Textos do HUD =============
    tela.blit(fonte.render(f"Velocidade: {velocidade_kmh:.1f} km/h", True, (255, 255, 255)), (20, 20))
    tela.blit(fonte.render(f"({velocidade:.0f} RPM)", True, (180, 180, 180)), (230, 20))
    tela.blit(fonte.render(f"Tempo: {minutos}:{segundos:02d}", True, (255, 255, 255)), (20, 60))
    tela.blit(fonte.render(f"Status: {status}", True, cor_status), (550, 60))
    tela.blit(fonte.render(f"Destino: {nome_planeta}", True, (255, 255, 255)), (20, 100))
    tela.blit(fonte.render(f"Pontos: {pontuacao}", True, (255, 255, 255)), (550, 20))

    if multiplicador > 1:
        tela.blit(fonte.render("BÔNUS: 2X!", True, (255, 215, 0)), (550, 40))
    else:
        segundos_restantes = max(0, 30 - int(tempo_na_zona_ideal // 1000))
        if status == "Ideal" and segundos_restantes > 0:
            tela.blit(fonte.render(f"Bônus em: {segundos_restantes}s", True, (200, 200, 200)), (550, 40))

    if evento_ativo:
        if tipo_evento_atual == "asteroide":
            texto_ev, cor_ev = "ALERTA: CAMPO DE ASTEROIDES! MANTENHA O RITMO!", (255, 100, 0)
        elif tipo_evento_atual == "tempestade":
            texto_ev, cor_ev = "ALERTA: TEMPESTADE ESPACIAL! MANTENHA O RITMO!", (200, 0, 255)
        elif tipo_evento_atual == "gravidade":
            if status == "Rápido":
                texto_ev, cor_ev = "GRAVIDADE DETECTADA! DESACELERE PARA ENTRAR EM ÓRBITA!", (255, 0, 0)
            else:
                texto_ev, cor_ev = "ENTRANDO EM ÓRBITA COM SUCESSO...", (0, 255, 0)
        surf_ev = fonte.render(texto_ev, True, cor_ev)
        tela.blit(surf_ev, surf_ev.get_rect(center=(400, 150)))

    # ============== Barras (progresso da missão e velocidade) ========================
    pygame.draw.rect(tela, (100, 100, 100), (barra_prog_x, barra_prog_y, barra_prog_largura, barra_prog_altura))
    pygame.draw.rect(tela, (0, 0, 255), (barra_prog_x, barra_prog_y, progresso * barra_prog_largura, barra_prog_altura))

    limite_ideal_min_atual = 0 if progresso > 0.7 else rpm_ideal_min
    if limite_ideal_min_atual <= rpm_min:
        prop_min = 0
        prop_ideal = rpm_ideal_max / rpm_max
        prop_max = (rpm_max - rpm_ideal_max) / rpm_max
    else:
        prop_min = limite_ideal_min_atual / rpm_max
        prop_ideal = (rpm_ideal_max - limite_ideal_min_atual) / rpm_max
        prop_max = (rpm_max - rpm_ideal_max) / rpm_max

    largura_min = barra_largura * prop_min
    largura_ideal = barra_largura * prop_ideal
    largura_max = barra_largura * prop_max

    if largura_min > 0:
        pygame.draw.rect(tela, (255, 0, 0), (barra_x, barra_y, largura_min, barra_altura))
    pygame.draw.rect(tela, (0, 255, 0), (barra_x + largura_min, barra_y, largura_ideal, barra_altura))
    if largura_max > 0:
        pygame.draw.rect(tela, (255, 0, 0), (barra_x + largura_min + largura_ideal, barra_y, largura_max, barra_altura))
    pygame.draw.rect(tela, (255, 255, 255), (barra_x, barra_y, barra_largura, barra_altura), 2)

    posicao = (velocidade / rpm_max) * barra_largura
    pygame.draw.rect(tela, (255, 255, 255), (barra_x + max(0, min(posicao, barra_largura - 5)), barra_y - 5, 5, barra_altura + 10))

    # Botão de pausa
    if not jogo_pausado:
        sel_botao_pausa = (700 <= mx <= 780 and 15 <= my <= 45)
        desenhar_botao("PAUSA", 700, 15, 80, 30, selecionado=sel_botao_pausa)
        if sel_botao_pausa and clique_mouse:
            jogo_pausado = True
            inicio_pausa = pygame.time.get_ticks()
            pygame.time.delay(200)
    
    # Aviso de direção da pedalada
    if direcao_atual_bike == "TRAS":
        desenhar_aviso_pedal_tras()

    # Menu suspenso de pausa
    if jogo_pausado:
        superficie_foco = pygame.Surface((800, 600), pygame.SRCALPHA)
        superficie_foco.fill((0, 0, 0, 180))
        tela.blit(superficie_foco, (0, 0))

        pygame.draw.rect(tela, (25, 35, 55), (250, 180, 300, 220), border_radius=12)
        pygame.draw.rect(tela, (0, 255, 255), (250, 180, 300, 220), 2, border_radius=12)

        texto_pausa = fonte.render("SESSÃO PAUSADA", True, (255, 255, 0))
        tela.blit(texto_pausa, texto_pausa.get_rect(center=(400, 220)))

        sel_continuar = (280 <= mx <= 520 and 260 <= my <= 300)
        sel_sair_partida = (280 <= mx <= 520 and 320 <= my <= 360)

        desenhar_botao("CONTINUAR", 280, 260, 240, 40, selecionado=sel_continuar)
        desenhar_botao("ENCERRAR SESSÃO", 280, 320, 240, 40, selecionado=sel_sair_partida)

        if sel_continuar and clique_mouse:
            limpar_leitura_esp32()
            tempo_pausado += pygame.time.get_ticks() - inicio_pausa
            jogo_pausado = False
            ultimo_tempo = pygame.time.get_ticks()
            pygame.time.delay(200)

        if sel_sair_partida and clique_mouse:
            jogo_pausado = False
            estado = MENU
            pygame.time.delay(200)

    if progresso >= 1 and not animacao_chegada:
        progresso = 1
        distancia_restante = 0
        
        tempo_final = (pygame.time.get_ticks() - tempo_inicio) // 1000 #quando a missão terminar, salva o tempo para tela de resultados
        
        # Inicia a animação de chegada
        animacao_chegada = True

        # Para a velocidade da bike
        velocidade = 0
        velocidade_kmh = 0
#=======================================================================================
# Fim
#=======================================================================================
def tela_fim():
    #Desenha e processa a tela de fim de missão (Reiniciar / Voltar ao Menu)
    global estado
    
    nome_planeta = fases[fase_atual]["nome"]
    minutos = tempo_final // 60
    segundos = tempo_final % 60
    
    #textos
    titulo_sombra_fim = fonte_titulo.render("Missão Concluída", True, (50, 55, 65))
    tela.blit(titulo_sombra_fim, titulo_sombra_fim.get_rect(center=(403, 80)))

    titulo_surf_fim = fonte_titulo.render("Missão Concluída", True, (255, 255, 0))
    tela.blit(titulo_surf_fim, titulo_surf_fim.get_rect(center=(400, 77)))
    
    textos = [
        (fonte, "RESULTADO DA ATIVIDADE", (44, 255, 5), 145),
        (fonte, f"Destino: {nome_planeta}", (255, 255, 255), 220),
        (fonte, f"Tempo de atividade: {minutos}:{segundos:02d}", (255, 255, 255), 260),
        (fonte, f"Distância percorrida: {distancia_total} m", (255, 255, 255), 300),
        (fonte, f"Pontuação: {pontuacao}", (255, 255, 255), 340)
    ]

    for fonte_texto, texto, cor, y in textos:
        superficie = fonte_texto.render(texto, True, cor)
        retangulo = superficie.get_rect(topleft=(250, y))
        tela.blit(superficie, retangulo)

    #botões
    mx, my = pygame.mouse.get_pos()
    sel_reiniciar = (250 <= mx <= 550 and 420 <= my <= 470)
    sel_menu_fim = (250 <= mx <= 550 and 490 <= my <= 540)

    desenhar_botao("REINICIAR", 250, 420, 300, 50, selecionado=sel_reiniciar)
    desenhar_botao("MENU", 250, 490, 300, 50, selecionado=sel_menu_fim)

    #ações dos botões
    if clicou(250, 420, 300, 50):
        resetar_missao()
        estado = JOGO
        pygame.time.delay(200)

    if clicou(250, 490, 300, 50):
        estado = MENU
        pygame.time.delay(200)


# --------------------------------------------------------- Loop principal --------------------------------------------------------
def main():
    global estrelas, linhas_velocidade, imagens_planetas, nave_img, esp32, rodando

    estrelas = criar_estrelas()
    linhas_velocidade = criar_linhas_velocidade()
    imagens_planetas, nave_img = carregar_imagens()
    esp32 = detectar_esp32()

    while rodando:
        clock.tick(60)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

        teclas = pygame.key.get_pressed()

        desenhar_fundo()

        if estado == MENU:
            tela_menu(teclas)
        elif estado == CONFIGURACAO:
            tela_configuracao(teclas)
        elif estado == JOGO:
            tela_jogo(teclas)
        elif estado == FIM:
            tela_fim()

        atualizar_tela_real()

    pygame.quit()


if __name__ == "__main__":
    main()