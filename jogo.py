import pygame
import random
import requests
import io

pygame.init()

tela = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Jogo Pedal Espacial")

fonte = pygame.font.SysFont(None, 30)
clock = pygame.time.Clock()

#===========Estados do Jogo===================
MENU = "MENU"
CONFIG = "CONFIGURAÇÕES"
JOGO = "JOGO"
FIM = "FIM"

estado = MENU

#===========Configurações=====================
vel_min = 1.5
vel_ideal_min = 2.0 
vel_ideal_max = 3.5
vel_max = 5
config_opcao = 0

fases = [
    {"nome": "Mercúrio", "duracao": 90},
    {"nome": "Vênus", "duracao": 120},
    {"nome": "Marte", "duracao": 180},
    {"nome": "Saturno", "duracao": 240}
]

fase_atual = 0
duracao_missao = fases[fase_atual]["duracao"]

# ============Jogo============================
velocidade = 0
progresso = 0
pontuacao = 0

tempo_inicio = pygame.time.get_ticks()
tempo_pontos = pygame.time.get_ticks()

nave_x = 200
nave_y = 300

planeta_x = 900
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

#================Planetas=====================
def carregar_imagem_url(url):
    resposta = requests.get(url)
    resposta.raise_for_status() #identifica erro de link
    imagem_bytes = io.BytesIO(resposta.content)
    return pygame.image.load(imagem_bytes).convert_alpha()

mercurio_img = pygame.transform.scale(carregar_imagem_url("https://raw.githubusercontent.com/rafaelafgomes/Jogo_Cicloergometro/main/imagens/mercurio.png"),(80,80))
venus_img = pygame.transform.scale(carregar_imagem_url("https://raw.githubusercontent.com/rafaelafgomes/Jogo_Cicloergometro/main/imagens/venus.png"),(80,80))
marte_img = pygame.transform.scale(carregar_imagem_url("https://raw.githubusercontent.com/rafaelafgomes/Jogo_Cicloergometro/main/imagens/marte.png"),(80,80))
saturno_img = pygame.transform.scale(carregar_imagem_url("https://raw.githubusercontent.com/rafaelafgomes/Jogo_Cicloergometro/main/imagens/saturno.png"),(100,80))

imagens_planetas = {
    "Mercúrio": mercurio_img,
    "Vênus": venus_img,
    "Marte": marte_img,
    "Saturno": saturno_img
}
    
#===============Nave============================
nave_img = pygame.image.load("nave.png").convert_alpha()
nave_img = pygame.transform.scale(nave_img, (80,50))

#==============Botões======================
def desenhar_botao(texto, x, y, w, h):
    pygame.draw.rect(tela, (50,50,50), (x,y,w,h))
    tela.blit(fonte.render(texto, True, (255,255,255)), (x+20, y+10))

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
    
    tela.fill((0,0,0))
    
    #=================Menu===========================
    if estado == MENU:
        tela.blit(fonte.render("Pedal Espacial", True, (255,255,0)), (280,100))
        
        desenhar_botao("INICIAR", 300, 200, 200, 50)
        desenhar_botao("CONFIG", 300, 280, 200, 50)
        desenhar_botao("SAIR", 300, 360, 200, 50)
        
        if clicou(300,200,200,50):
            progresso = 0
            velocidade = 0
            pontuacao = 0
            tempo_inicio = pygame.time.get_ticks()
            estado = JOGO
        if clicou(300,280,200,50):
            estado = CONFIG
        if clicou(300,360,200,50):
            rodando = False
            
    #================Configuração======================
    elif estado == CONFIG:
        tela.blit(fonte.render("CONFIGURAÇÕES", True, (255,255,0)), (280,100))
        
        opcoes = ["Velocidade Mínima", "Velocidade Ideal Mínima", "Velocidade Ideal Máxima", "Velocidade Máxima", "Missão"]

        # mostrar opções
        for i, opcao in enumerate(opcoes):
            cor = (255,255,0) if i == config_opcao else (255,255,255)

            if opcao == "Velocidade Mínima":
                texto = f"{opcao}: {vel_min:.1f}"
            elif opcao == "Velocidade Ideal Mínima":
                texto = f"{opcao}: {vel_ideal_min:.1f}"
            elif opcao == "Velocidade Ideal Máxima":
                texto = f"{opcao}: {vel_ideal_max:.1f}"
            elif opcao == "Velocidade Máxima":
                texto = f"{opcao}: {vel_max:.1f}"
            elif opcao == "Missão":
                texto = f"{opcao}: {fases[fase_atual]['nome']}"

            tela.blit(fonte.render(texto, True, cor), (200, 200 + i*40))

        desenhar_botao("VOLTAR", 300, 400, 200, 50)
        
        #controles das teclas que escolhe o campo para alterar
        if teclas[pygame.K_UP]:
            config_opcao = (config_opcao - 1) % len(opcoes)
            pygame.time.delay(150)

        if teclas[pygame.K_DOWN]:
            config_opcao = (config_opcao + 1) % len(opcoes)
            pygame.time.delay(150)  
            
        #controle das teclas que altera o valor
        
        if teclas[pygame.K_RIGHT]:
            if config_opcao == 0:
                vel_min += 0.1
            elif config_opcao == 1:
                vel_ideal_min += 0.1
            elif config_opcao == 2:
                vel_ideal_max += 0.1
            elif config_opcao == 3:
                vel_max += 0.1
            elif config_opcao == 4:
                fase_atual = (fase_atual + 1) % len(fases)
            pygame.time.delay(150)
            
        if teclas[pygame.K_LEFT]:
            if config_opcao == 0:
                vel_min -= 0.1
            elif config_opcao == 1:
                vel_ideal_min -= 0.1
            elif config_opcao == 2:
                vel_ideal_max -= 0.1
            elif config_opcao == 3:
                vel_max -= 0.1
            elif config_opcao == 4:
                fase_atual = (fase_atual - 1) % len(fases)
            pygame.time.delay(150)
            
        # evitar valores inválidos
        vel_min = max(0, vel_min)
        vel_ideal_min = max(vel_min, vel_ideal_min)
        vel_ideal_max = max(vel_ideal_min, vel_ideal_max)
        vel_max = max(vel_ideal_max, vel_max)       
        
        if clicou(300,400,200,50):
            estado = MENU
            pygame.time.delay(200)
    
    #====================Jogo============================
    elif estado == JOGO:
    
        duracao_missao = fases[fase_atual]["duracao"]
        teclas = pygame.key.get_pressed()

        # controle (simulação pedal)
        if teclas[pygame.K_UP]:
            velocidade += 0.2
        if teclas[pygame.K_DOWN]:
            velocidade -= 0.2

        velocidade *= 0.98
        
        velocidade = max(0, min(velocidade, vel_max))
        
        # status
        if velocidade < vel_min:
            status = "Lento"
            cor_status = (255,0,0)
        elif vel_ideal_min <= velocidade <= vel_ideal_max:
            status = "Ideal"
            cor_status = (0,255,0)
        else:
            status = "Rápido"
            cor_status = (255,0,0)
        
        # pontuação
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - tempo_pontos >= 1000:
            if vel_ideal_min <= velocidade <= vel_ideal_max:
                pontuacao += 20
            tempo_pontos = tempo_atual
        
        # progresso
        vel_media_ideal = (vel_ideal_min + vel_ideal_max) / 2
        tempo_passado = (pygame.time.get_ticks() - tempo_inicio) / 1000
        progresso = tempo_passado / duracao_missao
        progresso = min(progresso, 1)
        planeta_x = 800 - (progresso * 600)
        
        # fundo gradiente
        for y in range(600):
            cor = int(10 + (y/600)*40)
            pygame.draw.line(tela, (0,0,cor),(0,y),(800,y))
        
        # estrelas
        for estrela in estrelas:
            estrela[0] -= velocidade * estrela[2]
            if estrela[0] < 0:
                estrela[0] = 800
                estrela[1] = random.randint(0, 600)
            brilho = random.randint(150, 225)
            pygame.draw.circle(tela, (brilho, brilho, brilho), (int(estrela[0]), int(estrela[1])), estrela[3])
        
        # linhas velocidade
        if velocidade > vel_ideal_max * 0.8:
            for linha in linhas_velocidade:
                linha[0] -= velocidade * 5
                if linha[0] < 0:
                    linha[0] = 800
                    linha[1] = random.randint(0,600)

                pygame.draw.line(tela,(255,255,255),(linha[0],linha[1]),(linha[0]+linha[2],linha[1]),2)
        
        # nave
        if velocidade > vel_ideal_max:
            tamanho = random.randint(15,25)
            pygame.draw.polygon(tela, (255, random.randint(100,200), 0), [
                (nave_x, nave_y + 15),
                (nave_x - 20, nave_y + 10),
                (nave_x - 20, nave_y + 20)
            ])
        tela.blit(nave_img, (nave_x, nave_y))
        
        #planeta
        nome_planeta = fases[fase_atual]["nome"]
        img = imagens_planetas[nome_planeta]
        if nome_planeta == "Saturno":
            tela.blit(img, (planeta_x - 50, planeta_y - 40))
        else:
            tela.blit(img, (planeta_x - 40, planeta_y - 40))
        
        # tempo
        tempo_seg = (pygame.time.get_ticks() - tempo_inicio)//1000
        minutos = tempo_seg//60
        segundos = tempo_seg%60
        
        # HUD
        tela.blit(fonte.render(f"Velocidade: {velocidade:.2f}", True,(255,255,255)), (20,20))
        tela.blit(fonte.render(f"Tempo: {minutos}:{segundos:02d}", True,(255,255,255)), (20,60))
        tela.blit(fonte.render(f"Status: {status}", True,cor_status), (550,60))
        tela.blit(fonte.render(f"Destino: {nome_planeta}", True,(255,255,255)), (20,100))

        tela.blit(fonte.render(f"Pontos: {pontuacao}", True,(255,255,255)), (550,20))

        # barra progresso
        pygame.draw.rect(tela,(100,100,100),(barra_prog_x,barra_prog_y,barra_prog_largura,barra_prog_altura))
        pygame.draw.rect(tela,(0,0,255),(barra_prog_x,barra_prog_y,progresso*barra_prog_largura,barra_prog_altura))

        # barra velocidade - proporção
        prop_min = vel_ideal_min / vel_max
        prop_ideal = (vel_ideal_max - vel_ideal_min) / vel_max
        prop_max = (vel_max - vel_ideal_max) / vel_max
        
        # barra velocidade - largura
        largura_min = barra_largura * prop_min
        largura_ideal = barra_largura * prop_ideal
        largura_max = barra_largura * prop_max
        
        # barra velocidade - desenho
        pygame.draw.rect(tela,(255,0,0),(barra_x,barra_y,largura_min,barra_altura))
        pygame.draw.rect(tela,(0,255,0),(barra_x + largura_min,barra_y,largura_ideal,barra_altura))
        pygame.draw.rect(tela,(255,0,0),(barra_x + largura_min + largura_ideal,barra_y,largura_max,barra_altura))
        posicao = (velocidade / vel_max) * barra_largura
        pygame.draw.rect(tela, (255,255,255), (barra_x + posicao, barra_y - 5, 5, barra_altura + 10))
        pygame.draw.rect(tela, (255,255,255), (barra_x, barra_y, barra_largura, barra_altura), 2)
    
        # aviso
        if progresso > 0.9:
            tela.blit(fonte.render("Diminua a velocidade!", True,(255,255,0)), (250,200))

        if progresso >= 1:
            estado = FIM
            
    #=========================Fim============================
    elif estado == FIM:
        tela.blit(fonte.render("MISSÃO CONCLUIDA", True, (255,255,0)), (250,200))
        
        desenhar_botao("REINICIAR", 250, 300, 300, 50)
        desenhar_botao("MENU", 250, 380, 300, 50)
        
        if clicou(250,300,300,50): #botão reiniciar
            progresso = 0
            velocidade = 0
            pontuacao = 0
            tempo_inicio = pygame.time.get_ticks()
            estado = JOGO
            pygame.time.delay(200)

        if clicou(250,380,300,50): #botão menu
            estado = MENU
            pygame.time.delay(200)

    pygame.display.update()

pygame.quit()