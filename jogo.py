import pygame
import random
import requests
import io
import math

pygame.init()

tela = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Jogo Pedal Espacial")

fonte = pygame.font.SysFont(None, 30)
fonte_titulo = pygame.font.SysFont("arialblack", 55)
clock = pygame.time.Clock()

#===========Estados do Jogo===================
MENU = "MENU"
CONFIGURACAO = "CONFIGURACAO"
JOGO = "JOGO"
FIM = "FIM"

estado = MENU

#===========Configurações=====================
vel_min = 1.5
vel_ideal_min = 2.0 
vel_ideal_max = 3.5
vel_max = 5
config_opcao = 0
usar_obstaculos = True

#================Planetas (Função de Carga) =====================
def carregar_imagem_url(url):
    resposta = requests.get(url)
    resposta.raise_for_status() # identifica erro de link
    imagem_bytes = io.BytesIO(resposta.content)
    return pygame.image.load(imagem_bytes).convert_alpha()

#==============Eventos de obstaculos======================
# Variáveis de controle do tempo
tempo_ultimo_evento = pygame.time.get_ticks()
evento_ativo = False
tempo_inicio_evento = 0
tipo_evento_atual = None # Pode ser "asteroide", "tempestade" ou "gravidade"
duracao_evento = 10000   # 10 segundos em milissegundos
# Controle de animação/efeito visual
shake_tela = 0
flash_impacto = 0
# Lista para o efeito visual das partículas do asteroide
particulas_asteroide = []

#===================Fases=============================
fases = [
    {"nome": "Mercúrio", "distancia": 600},
    {"nome": "Vênus", "distancia": 120},
    {"nome": "Marte", "distancia": 300},
    {"nome": "Saturno", "distancia": 1000}
]

fase_atual = 0
distancia_total = fases[fase_atual]["distancia"]
distancia_restante = distancia_total

# ============Jogo============================
# Controles do multiplicador de bônus
tempo_na_zona_ideal = 0  # Armazena quantos milissegundos contínuos o jogador está na zona verde
multiplicador = 1        # Começa em 1x e vira 2x após 30 segundos

# Controle de pausa dentro da partida
jogo_pausado = False

velocidade = 0
progresso = 0 #porcentagem da distancia percorrida
pontuacao = 0

tempo_inicio = pygame.time.get_ticks()
tempo_pontos = pygame.time.get_ticks()
ultimo_tempo = pygame.time.get_ticks()

nave_x_inicial = 120
nave_x_final = 520
nave_x = nave_x_inicial
nave_y = 300

#flutuação da nave
nave_y_base = 300
nave_y = nave_y_base
vel_nave_y = 0
tempo_mudar_movimento = pygame.time.get_ticks()

planeta_x = 650
planeta_y = 300

#================Barras=======================
barra_x = 150
barra_y = 550
barra_largura = 500
barra_altura = 20

barra_prog_x = 250
barra_prog_y = 100
barra_prog_largura = 500
barra_prog_altura = 20

#================Estrelas=====================
estrelas = []
for i in range(200):
    x = random.randint(0, 800)
    y = random.randint(0, 600)
    camada = random.choice([1, 2, 3])

    if camada == 1:
        vel_estrela = 0.3
        tamanho = 1
    elif camada == 2:
        vel_estrela = 0.7
        tamanho = 2
    else:
        vel_estrela = 1.5
        tamanho = 3

    estrelas.append([x, y, vel_estrela, tamanho])
    
#===============Linhas de Velocidade============
linhas_velocidade = []
for i in range(40):
    linhas_velocidade.append([
        random.randint(0, 800),
        random.randint(0, 600),
        random.randint(10, 30)
    ])

#================Imagens dos Planetas=====================
mercurio_img = pygame.transform.scale(carregar_imagem_url("https://raw.githubusercontent.com/rafaelafgomes/Jogo_Cicloergometro/main/imagens/mercurio.png"),(220,220))
venus_img = pygame.transform.scale(carregar_imagem_url("https://raw.githubusercontent.com/rafaelafgomes/Jogo_Cicloergometro/main/imagens/venus.png"),(240,240))
marte_img = pygame.transform.scale(carregar_imagem_url("https://raw.githubusercontent.com/rafaelafgomes/Jogo_Cicloergometro/main/imagens/marte.png"),(230,230))
saturno_img = pygame.transform.scale(carregar_imagem_url("https://raw.githubusercontent.com/rafaelafgomes/Jogo_Cicloergometro/main/imagens/saturno.png"),(320,220))

imagens_planetas = {
    "Mercúrio": mercurio_img,
    "Vênus": venus_img,
    "Marte": marte_img,
    "Saturno": saturno_img
}
    
#===============Nave============================
nave_img = pygame.transform.scale(carregar_imagem_url("https://raw.githubusercontent.com/rafaelafgomes/Jogo_Cicloergometro/main/imagens/nave.png"), (80,50))

#==============Botões======================
def desenhar_botao(texto, x, y, w, h, selecionado=False):
    # Se o botão estiver selecionado (útil para teclado/configurações), muda a cor da borda ou do fundo
    cor_fundo = cor_fundo = (40, 50, 75) if not selecionado else (60, 80, 120)
    cor_borda = (0, 255, 255) if selecionado else (100, 100, 100)
    
    # Desenha o retângulo do fundo
    pygame.draw.rect(tela, cor_fundo, (x, y, w, h), border_radius=8) # border_radius deixa os cantos arredondados
    pygame.draw.rect(tela, cor_borda, (x, y, w, h), 2, border_radius=8) # Borda
    # Renderiza o texto
    texto_surf = fonte.render(texto, True, (255, 255, 255))
    # Centraliza o texto PERFEITAMENTE dentro das coordenadas do botão
    texto_rect = texto_surf.get_rect(center=(x + w // 2, y + h // 2))
    tela.blit(texto_surf, texto_rect)

def clicou(x,y,w,h):
    mx, my = pygame.mouse.get_pos()
    return x <= mx <= x+w and y <= my <= y+h and pygame.mouse.get_pressed()[0]





#===============================================
#==============Loop Principal===================    
rodando = True

while rodando:
    clock.tick(60)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
            
    teclas = pygame.key.get_pressed()
    
    # ================== Desenho do fundo unificado ==================
    # 1. Fundo gradiente espacial
    for y in range(600):
        cor = int(10 + (y / 600) * 35)
        pygame.draw.line(tela, (5, 5, cor), (0, y), (800, y))
        
    # 2. Desenha as estrelas no menu
    vel_menu = 0.2 if estado != JOGO else velocidade
    for estrela in estrelas:
        estrela[0] -= vel_menu * estrela[2]
        if estrela[0] < 0:
            estrela[0] = 800
            estrela[1] = random.randint(0, 600)
        brilho = random.randint(150, 225)
        pygame.draw.circle(tela, (brilho, brilho, brilho), (int(estrela[0]), int(estrela[1])), estrela[3])
    
    #=================Menu===========================
    if estado == MENU:
        # Título centralizado
        #efeito de sombra para o titulo (nome do jogo)
        titulo_sombra = fonte_titulo.render("Pedal Espacial", True, (50, 55, 65))
        sombra_rect = titulo_sombra.get_rect(center=(403, 103))
        tela.blit(titulo_sombra, sombra_rect)
        
        #Desenha o título principal por cima
        titulo_surf = fonte_titulo.render("Pedal Espacial", True, (0,255,255))
        titulo_rect = titulo_surf.get_rect(center=(400, 100))
        tela.blit(titulo_surf, titulo_rect)
        
        # Detecta hover do mouse para acender o botão
        mx, my = pygame.mouse.get_pos()
        sel_iniciar = (300 <= mx <= 520 and 200 <= my <= 250)
        sel_config  = (300 <= mx <= 520 and 280 <= my <= 330)
        sel_sair    = (300 <= mx <= 520 and 360 <= my <= 410)
        
        # Desenha botões com textos perfeitamente alinhados
        desenhar_botao("INICIAR", 300, 200, 220, 50, selecionado=sel_iniciar)
        desenhar_botao("CONFIGURAÇÕES", 300, 280, 220, 50, selecionado=sel_config)
        desenhar_botao("SAIR", 300, 360, 220, 50, selecionado=sel_sair)
        
        #Se apertar ESC no Menu Principal, fecha o jogo
        if teclas[pygame.K_ESCAPE]:
            rodando = False
        
        if clicou(300,200,220,50):
            progresso = 0
            velocidade = 0
            pontuacao = 0
            
            evento_ativo = False
            tipo_evento_atual = None
            tempo_ultimo_evento = pygame.time.get_ticks()
            particulas_asteroide = []
            
            distancia_total = fases[fase_atual]["distancia"]
            distancia_restante = distancia_total
            
            tempo_inicio = pygame.time.get_ticks()
            ultimo_tempo = pygame.time.get_ticks()
            
            estado = JOGO
            pygame.time.delay(150)
            
        if clicou(300,280,220,50):
            estado = CONFIGURACAO
            pygame.time.delay(150)
            
        if clicou(300,360,220,50):
            rodando = False
            
    #================Configuração======================
    elif estado == CONFIGURACAO:
        titulo_surf = fonte.render("CONFIGURAÇÕES DO EXERCÍCIO", True, (255,255,0))
        titulo_rect = titulo_surf.get_rect(center=(400, 60))
        tela.blit(titulo_surf, titulo_rect)
        
        opcoes = [
            {"id": 0, "nome": "Velocidade Mínima", "valor": f"{vel_min:.1f}"},
            {"id": 1, "nome": "Velocidade Ideal Mínima", "valor": f"{vel_ideal_min:.1f}"},
            {"id": 2, "nome": "Velocidade Ideal Máxima", "valor": f"{vel_ideal_max:.1f}"},
            {"id": 3, "nome": "Velocidade Máxima", "valor": f"{vel_max:.1f}"},
            {"id": 4, "nome": "Missão de Destino", "valor": f"{fases[fase_atual]['nome']}"},
            {"id": 5, "nome": "Obstáculos no Percurso", "valor": "Ligado" if usar_obstaculos else "Desligado"}
        ]
        
        mx, my = pygame.mouse.get_pos()
        clique_mouse = pygame.mouse.get_pressed()[0]
        
       # Variáveis para controlar cliques únicos do mouse (evita disparar o valor)
        ajuste_valor = 0 # -1 para diminuir, 1 para aumentar
        opcao_clicada = -1

        for i, opcao in enumerate(opcoes):
            y_pos = 140 + i * 60
            
            # Define se a linha está selecionada pelo teclado
            cor_texto = (0, 255, 255) if i == config_opcao else (255, 255, 255)
            
            # Desenha um fundo sutil para a linha se o mouse estiver sobre ela (Hover)
            if 150 <= mx <= 770 and y_pos <= my <= y_pos + 45:
                pygame.draw.rect(tela, (30, 40, 65), (150, y_pos, 610, 45), border_radius=6)
                if clique_mouse and estado == CONFIGURACAO:
                    config_opcao = i # Muda o foco do teclado para onde o mouse clicou

            # Renderiza o nome da opção
            nome_surf = fonte.render(opcao["nome"], True, cor_texto)
            tela.blit(nome_surf, (170, y_pos + 10))
            
            # Desenha os botões de [-] e [+] para o mouse, ajuste dinamico para o planeta
            if opcao["id"] == 4 or opcao["id"] == 5:  # Se for a linha da Missão
                bx_menos, by_menos = 500, y_pos + 5  # Afasta o [-] para a esquerda
                bx_mais, by_mais = 710, y_pos + 5    # Afasta o [+] para a direita
                largura_texto_ajuste = 290           # Espaço interno maior para o nome
            else:  # Se forem as opções com números
                bx_menos, by_menos = 540, y_pos + 5
                bx_mais, by_mais = 660, y_pos + 5
                largura_texto_ajuste = 120

            b_largura, b_altura = 40, 35
            
            # Detecção de hover nos botões de ajuste
            hover_menos = (bx_menos <= mx <= bx_menos + b_largura and by_menos <= my <= by_menos + b_altura)
            hover_mais = (bx_mais <= mx <= bx_mais + b_largura and by_mais <= my <= by_mais + b_altura)
            
           # Desenha os botões nas posições calculadas
            desenhar_botao("-", bx_menos, by_menos, b_largura, b_altura, selecionado=hover_menos)
            desenhar_botao("+", bx_mais, by_mais, b_largura, b_altura, selecionado=hover_mais)
            
            # Encontra o meio exato entre o fim do botão [-] e o começo do botão [+]
            centro_x = (bx_menos + b_largura + bx_mais) // 2
            
            valor_surf = fonte.render(opcao["valor"], True, (255, 255, 255))
            valor_rect = valor_surf.get_rect(center=(centro_x, y_pos + 22))
            tela.blit(valor_surf, valor_rect)
            
            # Captura o clique do mouse nos botões de ajuste
            if clique_mouse:
                if hover_menos:
                    ajuste_valor = -1
                    opcao_clicada = i
                elif hover_mais:
                    ajuste_valor = 1
                    opcao_clicada = i

        # Executa a lógica de alteração (Teclado ou cliques no Botão do Mouse)
        if ajuste_valor != 0:
            config_opcao = opcao_clicada # Sincroniza o índice
            
        # Aplica as mudanças (funciona para os dois métodos)
        if teclas[pygame.K_RIGHT] or (ajuste_valor == 1):
            if config_opcao == 0: vel_min += 0.1
            elif config_opcao == 1: vel_ideal_min += 0.1
            elif config_opcao == 2: vel_ideal_max += 0.1
            elif config_opcao == 3: vel_max += 0.1
            elif config_opcao == 4: fase_atual = (fase_atual + 1) % len(fases)
            elif config_opcao == 5: usar_obstaculos = not usar_obstaculos # <--- Inverte Liga/Desliga
            pygame.time.delay(150)
            
        if teclas[pygame.K_LEFT] or (ajuste_valor == -1):
            if config_opcao == 0: vel_min -= 0.1
            elif config_opcao == 1: vel_ideal_min -= 0.1
            elif config_opcao == 2: vel_ideal_max -= 0.1
            elif config_opcao == 3: vel_max -= 0.1
            elif config_opcao == 4: fase_atual = (fase_atual - 1) % len(fases)
            elif config_opcao == 5: usar_obstaculos = not usar_obstaculos # <--- Inverte Liga/Desliga
            pygame.time.delay(150)

        # Movimentação pelas opções via teclado
        if teclas[pygame.K_UP]:
            config_opcao = (config_opcao - 1) % len(opcoes)
            pygame.time.delay(150)
        if teclas[pygame.K_DOWN]:
            config_opcao = (config_opcao + 1) % len(opcoes)
            pygame.time.delay(150)  
            
        if teclas[pygame.K_ESCAPE]:
            estado = MENU
            pygame.time.delay(200)
            
        # Validações de segurança dos limites
        vel_min = max(0, vel_min)
        vel_ideal_min = max(vel_min, vel_ideal_min)
        vel_ideal_max = max(vel_ideal_min, vel_ideal_max)
        vel_max = max(vel_ideal_max, vel_max)       
        
        # Botão Voltar
        sel_voltar = (300 <= mx <= 500 and 520 <= my <= 570)
        desenhar_botao("VOLTAR", 300, 520, 200, 50, selecionado=sel_voltar)
        
        if (sel_voltar and clique_mouse):
            estado = MENU
            pygame.time.delay(200)
    
    #====================Jogo============================
    elif estado == JOGO:
        teclas = pygame.key.get_pressed()
        tempo_atual = pygame.time.get_ticks()
        mx, my = pygame.mouse.get_pos()
        clique_mouse = pygame.mouse.get_pressed()[0]

        # Atalho no teclado: Apertar ESC pausa ou despausa o jogo
        if teclas[pygame.K_ESCAPE]:
            jogo_pausado = not juego_pausado
            pygame.time.delay(200)
         
        
        if not jogo_pausado:
            # controle (simulação pedal)
            if teclas[pygame.K_UP]:
                velocidade += 0.2
            if teclas[pygame.K_DOWN]:
                velocidade -= 0.2


            # muda o comportamento só de vez em quando
            if tempo_atual - tempo_mudar_movimento > random.randint(1200, 2500):
                vel_nave_y = random.uniform(-0.25, 0.25)
                tempo_mudar_movimento = tempo_atual
            # aplica movimento vertical na nave
            nave_y += vel_nave_y

            # limita o quanto sobe/desce a nave
            if nave_y < nave_y_base - 8:
                nave_y = nave_y_base - 8
                vel_nave_y *= -1

            if nave_y > nave_y_base + 8:
                nave_y = nave_y_base + 8
                vel_nave_y *= -1
            
            # Atrito natural para a velocidade decair se parar de pedalar
            velocidade *= 0.98
            velocidade = max(0, min(velocidade, vel_max))
        
            # ======= Lógica de limites dinamicos =======
            #status dinamico: Mantém o limite padrão configurado
            limite_ideal_min_atual = vel_ideal_min
            #Se o progresso passar de 70% (reta final), a velocidade baixa vira ideal
            if progresso > 0.7:
                limite_ideal_min_atual = 0  # Expandindo a zona verde, desaceleração
            # Definição do Status baseado nos limites atuais
            if velocidade < limite_ideal_min_atual:
                status = "Lento"
                cor_status = (255, 0, 0)
            elif limite_ideal_min_atual <= velocidade <= vel_ideal_max:
                status = "Ideal"
                cor_status = (0, 255, 0)
            else:
                status = "Rápido"
                cor_status = (255, 0, 0)
            
            # ======= Sistema de pontuação e bonus =======
            delta_tempo = (tempo_atual - ultimo_tempo) / 1000
            ultimo_tempo = tempo_atual
            
            if status == "Ideal":
                # Acumula o tempo contínuo na zona verde (converte delta_tempo para milissegundos)
                tempo_na_zona_ideal += delta_tempo * 1000
                
                # Se mantiver por 30 segundos contínuos, ativa o multiplicador 2x 
                if tempo_na_zona_ideal >= 30000:
                    multiplicador = 2
                else:
                    multiplicador = 1
            else:
                # Se sair da zona ideal (Lento ou Rápido), reseta o contador e o bônus [cite: 48, 50]
                tempo_na_zona_ideal = 0
                multiplicador = 1
            # Concede a pontuação a cada 1 segundo (usando o seu tempo_pontos original)
            if tempo_atual - tempo_pontos >= 1000:
                if status == "Ideal":
                    # Multiplica os 20 pontos base pelo multiplicador ativo (20 ou 40 pontos) 
                    pontuacao += 10 * multiplicador
                tempo_pontos = tempo_atual
            
            # ======= Cálculo de avanço da distancia =======
            # variável para controlar a velocidade real de avanço da nave (SÓ AVANÇA NA ZONA IDEAL)
                velocidade_avanco = velocidade if status == "Ideal" else 0
       
            
            # ======= Sistema de eventos e obstaculos =======
            if usar_obstaculos:
                # 1. Disparar novos eventos na jornada (apenas se progresso < 55% e duram 10s)
                if not evento_ativo and progresso < 0.55:
                    intervalo_aleatorio = random.randint(30000, 40000) # Entre 30 e 40 segundos
                    if tempo_atual - tempo_ultimo_evento > intervalo_aleatorio:
                        evento_ativo = True
                        tempo_inicio_evento = tempo_atual
                        # Sorteia entre Asteroide ou Tempestade Espacial
                        tipo_evento_atual = random.choice(["asteroide", "tempestade"])
                        
                # 2. Ativação automática e obrigatória da Gravidade no final, chegada ao planeta
                if progresso >= 0.7 and tipo_evento_atual != "gravidade" and not evento_ativo:
                    evento_ativo = True
                    tempo_inicio_evento = tempo_atual
                    tipo_evento_atual = "gravidade"
                
                # 3. Execução das regras com o evento rodando                
                if evento_ativo:
                    # Verifica se o evento de 10 segundos acabou
                    if tempo_atual - tempo_inicio_evento > duracao_evento: 
                        #o evento acabou
                        evento_ativo = False
                        tipo_evento_atual = None
                        tempo_ultimo_evento = tempo_atual
                    else:
                        # Regra de penalidade durante o evento (asteroide e tempestades)
                        if tipo_evento_atual in ["asteroide", "tempestade"]:
                            if status != "Ideal":
                                # SÓ aplica o dano se o flash_impacto já tiver zerado (evita aplicar o dano em sequência por frame)
                                if flash_impacto == 0:
                                    # Pontuação cai pela metade no momento do impacto
                                    pontuacao = int(pontuacao / 2) # Converte para inteiro para não ficar número quebrado
                                    # Ativa os efeitos visuais e serve como tempo de imunidade
                                    flash_impacto = 30 # Aumentamos o tempo do flash para dar um "respiro" ao jogador
                                    shake_tela = 15    # Chacoalha a nave com um pouco mais de força
                                # Enquanto o jogador estiver fora do ritmo, a nave continua travada no espaço
                                velocidade_avanco = 0 
                        # Se estiver rápido ao chegar no planeta, quase não avança no espaço (Sem conflito no ponteiro)
                        elif tipo_evento_atual == "gravidade":
                            if status == "Rápido":
                                shake_tela = 5
                                velocidade_avanco = 0.05
            
            else:
                # Se os obstáculos estiverem DESLIGADOS, garante que nenhum evento rode
                evento_ativo = False
                tipo_evento_atual = None
            
            # ============== Atualiza a distância ================
            # impede valor negativo
            distancia_restante -= velocidade_avanco * delta_tempo
            distancia_restante = max(0, distancia_restante)
            # porcentagem concluída
            progresso = 1 - (distancia_restante / distancia_total)
            # move planeta visualmente
            nave_x = nave_x_inicial + (progresso * (nave_x_final - nave_x_inicial))
            
            #============ movimento do cenário de fundo ==================
            # estrelas e linhas se movem normalmente se não estiver pausado
            for estrela in estrelas:
                estrela[0] -= velocidade * estrela[2]
                if estrela[0] < 0:
                    estrela[0] = 800
                    estrela[1] = random.randint(0, 600)

            # linhas velocidade
            if velocidade > vel_ideal_max * 0.8:
                for linha in linhas_velocidade:
                    linha[0] -= velocidade * 5
                    if linha[0] < 0:
                        linha[0] = 800
                        linha[1] = random.randint(0,600)
        
        # ================= Lógica com o jogo pausado =================
        else:
            ultimo_tempo = tempo_atual
            velocidade = 0 # Para a nave visualmente
            status = "Pausado"
            cor_status = (255, 255, 0)

        # ================================== Renderização gráfica (HUD E elementos) =================
        #desenha estrelas
        for estrela in estrelas:
            brilho = random.randint(150, 225)
            pygame.draw.circle(tela, (brilho, brilho, brilho), (int(estrela[0]), int(estrela[1])), estrela[3])
        
        #desenha linhas de velocidade
        if not jogo_pausado and velocidade > vel_ideal_max * 0.8:
            for linha in linhas_velocidade:
                pygame.draw.line(tela,(255,255,255),(linha[0],linha[1]),(linha[0]+linha[2],linha[1]),2)
            
            
        # ======= Desenho do planeta  e efeito de aproximação dinâmica =======
        nome_planeta = fases[fase_atual]["nome"]
        img_original = imagens_planetas[nome_planeta]
        # O planeta começa com 10% do tamanho e cresce até 100% baseado no progresso
        fator_escala = 0.1 + (progresso * 0.9)
         # Calcula a nova largura e altura dinamicamente
        nova_largura = int(img_original.get_width() * fator_escala)
        nova_altura = int(img_original.get_height() * fator_escala)
        # Redimensiona a imagem do planeta em tempo real (garantindo tamanho mínimo de 1x1)
        img_dinamica = pygame.transform.scale(img_original, (max(1, nova_largura), max(1, nova_altura)))
        
        # Se o jogo não estiver pausado, calcula o balanço do planeta usando o tempo atual do Pygame
        if not jogo_pausado:
            # Multiplicamos o tempo por 0.002 para o balanço ser bem LENTO
            # Multiplicamos o resultado final por 4 para ele subir e descer no máximo 4 pixels (bem sutil)
            balanco_planeta_y = math.sin(tempo_atual * 0.002) * 4
        else:
            balanco_planeta_y = 0

        # Desenha o planeta centralizado na coordenada dele + o balanço sutil no eixo Y
        tela.blit(img_dinamica, (planeta_x - nova_largura // 2, (planeta_y + balanco_planeta_y) - nova_altura // 2))
        
        # ============== Sistema de tremor por causa do obstáculo =========================
        # Aplica o tremor na nave se houver colisão ou se estiver no campo gravitacional ruidoso
        deslocamento_shake = 0
        if shake_tela > 0:
            deslocamento_shake = random.randint(-shake_tela, shake_tela)
            shake_tela -= 1 # Reduz o tremor gradualmente
            
        #=============== Visualizaçã física dos obstaculos na tela =========================
        # Se for um Asteroide e o jogador errar a velocidade, desenha o obstáculo bloqueando a nave!
        if evento_ativo and tipo_evento_atual == "asteroide":
            # Se o jogo não estiver pausado, alimenta e move as partículas
            if not jogo_pausado:
                # Cria novas partículas vindo da direita continuamente
                if len(particulas_asteroide) < 25:
                    particulas_asteroide.append([820,            # X inicial (fora da tela na direita)
                        random.randint(180, 480),                # Y aleatório na faixa da nave
                        random.uniform(6, 14),                   # Velocidade horizontal do fragmento
                        random.randint(2, 6),                    # Tamanho/Diâmetro do ponto
                        random.choice([(255,80,0), (220,110,20), (130,130,130)]) # Cores quentes e cinza metálico
                    ])

                # Atualiza a posição de cada partícula
                for p in particulas_asteroide:
                    p[0] -= p[2] # Move para a esquerda baseado na velocidade própria dela

                # Remove as partículas que já saíram da tela pela esquerda
                particulas_asteroide = [p for p in particulas_asteroide if p[0] > -10]

            # DESENHO DAS PARTÍCULAS NA TELA (Roda mesmo pausado para manter o visual estático)
            for p in particulas_asteroide:
                # Desenha um efeito sutil de rastro (uma linha horizontal atrás do ponto)
                pygame.draw.line(tela, p[4], (int(p[0]), int(p[1])), (int(p[0] + p[2]*1.5), int(p[1])), 1)
                # Desenha o núcleo do fragmento espacial
                pygame.draw.circle(tela, p[4], (int(p[0]), int(p[1])), p[3])

        # Desenha a nave do jogador
        tela.blit(nave_img, (nave_x, nave_y + deslocamento_shake))
        
        # Efeito visula de flash vermelho na tela em caso de colisão
        if flash_impacto > 0:
            superficie_colisao = pygame.Surface((800, 600), pygame.SRCALPHA)
            superficie_colisao.fill((255, 0, 0, 120)) # Vermelho translúcido
            tela.blit(superficie_colisao, (0, 0))
            flash_impacto -= 1
            
        # Efeito visual de Nebulosa da Tempestade Espacia, escurece a tela colocando uma camada roxa/azul escura transparente
        if evento_ativo and tipo_evento_atual == "tempestade":
            superficie_tempestade = pygame.Surface((800, 600), pygame.SRCALPHA)
            superficie_tempestade.fill((30, 10, 50, 160)) 
            tela.blit(superficie_tempestade, (0, 0))
        
        
        # ======= Cronometro da partida =======
        tempo_seg = (pygame.time.get_ticks() - tempo_inicio)//1000
        minutos = tempo_seg//60
        segundos = tempo_seg%60
        
        # =========== Textos do HUD =============
        tela.blit(fonte.render(f"Velocidade: {velocidade:.2f}", True,(255,255,255)), (20,20))
        tela.blit(fonte.render(f"Tempo: {minutos}:{segundos:02d}", True,(255,255,255)), (20,60))
        tela.blit(fonte.render(f"Status: {status}", True,cor_status), (550,60))
        tela.blit(fonte.render(f"Destino: {nome_planeta}", True,(255,255,255)), (20,100))
        tela.blit(fonte.render(f"Pontos: {pontuacao}", True,(255,255,255)), (550,20))
        
        # Se o bônus estiver ativo, mostra um texto piscando ou destacado em amarelo
        if multiplicador > 1:
            tela.blit(fonte.render("BÔNUS: 2X!", True, (255, 215, 0)), (550, 40))
        else:
            # Mostra o progresso dos segundos restantes para ativar o bônus
            segundos_restantes = max(0, 30 - int(tempo_na_zona_ideal // 1000))
            if status == "Ideal" and segundos_restantes > 0:
                tela.blit(fonte.render(f"Bônus em: {segundos_restantes}s", True, (200, 200, 200)), (550, 40))
        
        # ==========Exibição de alertas textuais na tela, se houver um obstáculo por perto, mostra um alerta grande no centro da tela
        if evento_ativo:
            if tipo_evento_atual == "asteroide":
                texto_ev = "ALERTA: CAMPO DE ASTEROIDES! MANTENHA O RITMO!"
                cor_ev = (255, 100, 0)
            elif tipo_evento_atual == "tempestade":
                texto_ev = "ALERTA: TEMPESTADE ESPACIAL! MANTENHA O RITMO!"
                cor_ev = (200, 0, 255)
            elif tipo_evento_atual == "gravidade":
                if status == "Rápido":
                    texto_ev = "GRAVIDADE DETECTADA! DESACELERE PARA ENTRAR EM ÓRBITA!"
                    cor_ev = (255, 0, 0)
                else:
                    texto_ev = "ENTRANDO EM ÓRBITA COM SUCESSO..."
                    cor_ev = (0, 255, 0)
            surf_ev = fonte.render(texto_ev, True, cor_ev)
            tela.blit(surf_ev, surf_ev.get_rect(center=(400, 150)))

        # ==============Desenhos das barras e botoes e menus ========================
        # barra progresso da missão
        pygame.draw.rect(tela,(100,100,100),(barra_prog_x,barra_prog_y,barra_prog_largura,barra_prog_altura))
        pygame.draw.rect(tela,(0,0,255),(barra_prog_x,barra_prog_y,progresso*barra_prog_largura,barra_prog_altura))
          
        # barra velocidade
        if limite_ideal_min_atual <= vel_min:
            prop_min = 0
            prop_ideal = vel_ideal_max / vel_max
            prop_max = (vel_max - vel_ideal_max) / vel_max
        else:
            prop_min = limite_ideal_min_atual / vel_max
            prop_ideal = (vel_ideal_max - limite_ideal_min_atual) / vel_max
            prop_max = (vel_max - vel_ideal_max) / vel_max
        
        # barra velocidade - largura
        largura_min = barra_largura * prop_min
        largura_ideal = barra_largura * prop_ideal
        largura_max = barra_largura * prop_max
        
        # Desenha a zona Baixa/Lenta (só existirá se largura_min > 0)
        if largura_min > 0:
            pygame.draw.rect(tela, (255, 0, 0), (barra_x, barra_y, largura_min, barra_altura)) 
        pygame.draw.rect(tela, (0, 255, 0), (barra_x + largura_min, barra_y, largura_ideal, barra_altura))
        
        if largura_max > 0:
            pygame.draw.rect(tela, (255, 0, 0), (barra_x + largura_min + largura_ideal, barra_y, largura_max, barra_altura)) 
        
        # Desenha a zona Ideal (Verde) - Ela crescerá para a esquerda na reta final
        pygame.draw.rect(tela, (0, 255, 0), (barra_x + largura_min, barra_y, largura_ideal, barra_altura))
        
        # Desenha a zona Alta/Rápida (Vermelha da direita)
        pygame.draw.rect(tela, (255, 0, 0), (barra_x + largura_min + largura_ideal, barra_y, largura_max, barra_altura))
        
        # Desenha o marcador da velocidade atual e a borda branca
        posicao = (velocidade / vel_max) * barra_largura
        pygame.draw.rect(tela, (255, 255, 255), (barra_x + posicao, barra_y - 5, 5, barra_altura + 10))
        pygame.draw.rect(tela, (255, 255, 255), (barra_x, barra_y, barra_largura, barra_altura), 2)
    
        # Desenha o botão de PAUSA fixo no canto superior direito do HUD para o mouse
        sel_botao_pausa = (700 <= mx <= 780 and 15 <= my <= 45)
        desenhar_botao("PAUSA", 700, 15, 80, 30, selecionado=sel_botao_pausa)

        if sel_botao_pausa and clique_mouse:
            jogo_pausado = True
            pygame.time.delay(200)

        # Menu suspenso de pausa
        if jogo_pausado:
            # Cria um fundo escurecido sutil para destacar a janela de pausa
            superficie_foco = pygame.Surface((800, 600), pygame.SRCALPHA)
            superficie_foco.fill((0, 0, 0, 180)) # Preto com transparência
            tela.blit(superficie_foco, (0, 0))
            
            # Desenha a caixinha do menu de pausa
            pygame.draw.rect(tela, (25, 35, 55), (250, 180, 300, 220), border_radius=12)
            pygame.draw.rect(tela, (0, 255, 255), (250, 180, 300, 220), 2, border_radius=12)
            
            texto_pausa = fonte.render("SESSÃO PAUSADA", True, (255, 255, 0))
            tela.blit(texto_pausa, texto_pausa.get_rect(center=(400, 220)))
            
            # Botões do Menu de Pausa
            sel_continuar = (280 <= mx <= 520 and 260 <= my <= 300)
            sel_sair_partida = (280 <= mx <= 520 and 320 <= my <= 360)
            
            desenhar_botao("CONTINUAR", 280, 260, 240, 40, selecionado=sel_continuar)
            desenhar_botao("ENCERRAR SESSÃO", 280, 320, 240, 40, selecionado=sel_sair_partida)
            
            # Ações dos botões
            if sel_continuar and clique_mouse:
                jogo_pausado = False
                ultimo_tempo = pygame.time.get_ticks() # Sincroniza o relógio
                pygame.time.delay(200)
                
            if sel_sair_partida and clique_mouse:
                jogo_pausado = False
                estado = MENU # Voltar para a tela inicial com segurança
                pygame.time.delay(200)

        # fim, pouso realizado com sucesso
        if progresso >= 1:
            estado = FIM
            
    #=========================Fim============================
    elif estado == FIM:
        titulo_surf = fonte.render("MISSÃO CONCLUÍDA", True, (255,255,0))
        titulo_rect = titulo_surf.get_rect(center=(400, 200))
        tela.blit(titulo_surf, titulo_rect)
        
        mx, my = pygame.mouse.get_pos()
        sel_reiniciar = (250 <= mx <= 550 and 300 <= my <= 350)
        sel_menu_fim  = (250 <= mx <= 550 and 380 <= my <= 430)
        
        desenhar_botao("REINICIAR", 250, 300, 300, 50, selecionado=sel_reiniciar)
        desenhar_botao("MENU", 250, 380, 300, 50, selecionado=sel_menu_fim)
        
        if clicou(250,300,300,50): #botão reiniciar
            progresso = 0
            velocidade = 0
            pontuacao = 0
            
            evento_ativo = False
            tipo_evento_atual = None
            tempo_ultimo_evento = pygame.time.get_ticks()
            particulas_asteroide = []
            
            distancia_total = fases[fase_atual]["distancia"]
            distancia_restante = distancia_total
            tempo_inicio = pygame.time.get_ticks()
            ultimo_tempo = pygame.time.get_ticks()
            nave_x = nave_x_inicial
            estado = JOGO
            pygame.time.delay(200)

        if clicou(250,380,300,50): #botão menu
            estado = MENU
            pygame.time.delay(200)

    pygame.display.update()

pygame.quit()