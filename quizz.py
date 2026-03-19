import os
import json
from datetime import datetime
 
RESULTADOS_FICHEIRO = "resultados.json"
 
def carregar_resultados():
    if not os.path.exists(RESULTADOS_FICHEIRO):
        return {}
    with open(RESULTADOS_FICHEIRO, "r") as f:
        return json.load(f)
 
def guardar_resultados(resultados):
    with open(RESULTADOS_FICHEIRO, "w") as f:
        json.dump(resultados, f, indent=4)
 
def ja_jogou(user_id, resultados):
    return user_id in resultados
 
perguntas = [
    ("Quanto tempo os profissionais passam por ano em reuniões?",
     ["120h", "200h", "392h", "500h"], 3),
    ("Que percentagem das reuniões é considerada improdutiva?",
     ["20%", "40%", "67%", "90%"], 3),
    ("Quantos profissionais têm a caixa de entrada sempre aberta?",
     ["20%", "50%", "80%", "95%"], 3),
    ("O excesso de conectividade provoca:",
     ["Mais criatividade", "Melhor comunicação", "Perda de foco e bem‑estar", "Menos reuniões"], 3),
    ("O Eixo Duplo da Produtividade combina:",
     ["Horas extra + multitasking", "Foco individual + colaboração eficiente", "Velocidade + pressão", "Automação + reuniões"], 2),
    ("Qual NÃO é um dos 5 pilares da gestão de tempo?",
     ["Expandir perceção", "Demarcar limites", "Erradicar esgotamento", "Trabalhar mais horas"], 4),
    ("O método Pomodoro usa ciclos de:",
     ["10/10", "25/5", "40/10", "60/15"], 2),
    ("Eat the Frog significa:",
     ["Fazer a tarefa mais fácil", "Fazer a mais difícil de manhã", "Fazer várias tarefas", "Evitar pausas"], 2),
    ("Pareto 80/20 sugere:",
     ["80 tarefas em 20 min", "Eliminar 80% em 20% do tempo", "Trabalhar 80% do dia", "Fazer 20% primeiro"], 2),
    ("O cérebro faz multitasking?",
     ["Sim", "Não, alterna rapidamente", "Apenas com treino", "Só com música"], 2),
    ("Quantos fazem multitasking em reuniões?",
     ["30%", "50%", "92%", "100%"], 3),
    ("Reuniões mal planeadas:",
     ["São curtas", "Destruem o foco individual", "Têm poucos participantes", "Ajudam a concentração"], 2),
    ("Primeira fase de uma reunião produtiva:",
     ["Durante", "Depois", "Antes", "Avaliação"], 3),
    ("Antes da reunião deve-se:",
     ["Improvisar agenda", "Convidar todos", "Clarificar objetivo", "Começar sem contexto"], 3),
    ("O 'Olhar Digital' implica:",
     ["Olhar para o teclado", "Câmara desligada", "Olhar para a lente", "Evitar olhar"], 3),
    ("O 'Silêncio Tático' significa:",
     ["Falar sempre", "Mute até falar", "Desligar câmara", "Não participar"], 2),
    ("Entrada Antecipada é:",
     ["20 min antes", "5 min antes", "No minuto exato", "Depois do moderador"], 2),
    ("Para reduzir Zoom Fatigue:",
     ["Reuniões longas", "Chamadas seguidas", "Encurtar reuniões e dar pausas", "Câmara sempre ligada"], 3),
    ("Órbita 1 (Videoconferência) é:",
     ["O cérebro", "O palco", "O arquivo", "O gestor"], 2),
    ("Fecho de Sistema inclui:",
     ["Responder emails", "Planear o dia seguinte", "Agendar reuniões", "Fazer multitasking"], 2)
]
 
def jogar_quiz():
    resultados = carregar_resultados()
 
    print("\n=== QUIZ TRABALHO HÍBRIDO ===")
    user_id = input("Insere o teu ID de utilizador: ").strip()
 
    if ja_jogou(user_id, resultados):
        dados = resultados[user_id]
        print("\n⚠ Este utilizador já jogou!")
        print(f"Pontuação: {dados['score']}")
        print(f"Data: {dados['data']} {dados['hora']}")
        return
 
    print("\nVamos começar!\n")
    score = 0
 
    for idx, (pergunta, opcoes, correta) in enumerate(perguntas, start=1):
        print(f"\nPergunta {idx}: {pergunta}")
        for i, opcao in enumerate(opcoes, start=1):
            print(f"{i}) {opcao}")
 
        resposta = input("Resposta: ")
 
        if resposta.isdigit() and int(resposta) == correta:
            print("✔ Correto!")
            score += 1
        else:
            print("❌ Incorreto.")
 
    if score == 20:
        medalha = "🥇 Ouro"
    elif score >= 15:
        medalha = "🥈 Prata"
    elif score >= 10:
        medalha = "🥉 Bronze"
    else:
        medalha = "🎗 Participação"
 
    print("\n=== RESULTADOS ===")
    print(f"Utilizador: {user_id}")
    print(f"Pontuação: {score}/20")
    print(f"Medalha: {medalha}")
 
    resultados[user_id] = {
        "score": score,
        "data": datetime.now().strftime("%d/%m/%Y"),
        "hora": datetime.now().strftime("%H:%M:%S")
    }
    guardar_resultados(resultados)
 
    print("\nResultados guardados com sucesso!")
 
    print("\n=== RANKING DOS COLEGAS ===")
    ranking = sorted(resultados.items(), key=lambda x: x[1]["score"], reverse=True)
 
    for pos, (uid, dados) in enumerate(ranking, start=1):
        print(f"{pos}. {uid} — {dados['score']} pontos ({dados['data']} {dados['hora']})")
 
if __name__ == "__main__":
    jogar_quiz()
