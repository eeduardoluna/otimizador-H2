# otimizador H2

Sistema de otimização de produção de hidrogênio verde via Aprendizado por Reforço.

O agente aprende a decidir, hora a hora, quanto da energia renovável disponível deve ser direcionada para o eletrolisador (produção de H2) e quanto deve ser vendida para a rede elétrica — maximizando o lucro total do dia.

---

## Como funciona

Um parque de energia renovável (solar + eólica) alimenta um eletrolisador PEM que produz hidrogênio verde. A cada hora, o agente observa:

- Geração solar e eólica atual
- Preço spot da energia
- Nível atual do tanque de H2
- Carga atual do eletrolisador
- Previsão das próximas 6 horas

Com base nisso, decide o percentual de energia destinado à eletrólise (0% a 100%).

O agente foi treinado com o algoritmo **SAC (Soft Actor-Critic)** via Stable-Baselines3, em um ambiente Gymnasium com física realista: curva de eficiência do eletrolisador PEM, restrição de rampa, preço dinâmico do H2 e degradação por partidas excessivas.

---

## Resultados

Comparado a uma regra simples (baseline), o agente obteve **+54% de lucro** no mesmo dia climático, demonstrando capacidade de antecipar variações de preço e geração.

---

## Tecnologias

- **Backend**: Python, FastAPI, Gymnasium, Stable-Baselines3 (SAC)
- **Frontend**: React, Vite, Recharts
- **Dados meteorológicos**: Open-Meteo API (Fortaleza, CE)
- **Modelo**: SAC com replay buffer, maximização de entropia

---

## Instalação

### Pré-requisitos

- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
python main.py
```

O servidor estará disponível em `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

O dashboard estará disponível em `http://localhost:5173`.

---

## Uso

1. Com backend e frontend rodando, acesse `http://localhost:5173`
2. Clique em **Executar Simulação** para rodar uma simulação de 24 horas
3. Os gráficos mostram: fluxo de energia, nível do tanque, preço spot, lucro acumulado e comparativo com o baseline

---

## Estrutura do projeto

```
backend/
├── agent/          # Treino e inferência do agente SAC
├── api/            # Endpoints FastAPI
├── config.py       # Parâmetros físicos e econômicos
├── data/           # Clima (Open-Meteo), preço spot, banco de dados
├── scripts/        # Simulação e baseline
├── simulation/     # Ambiente Gymnasium, modelos solar e eólico
└── main.py         # Servidor FastAPI

frontend/
├── src/
│   ├── components/ # Dashboard, gráficos, log de decisões
│   └── services/   # Chamadas à API
└── index.html
```

---

## Retreinar o modelo

```bash
cd backend
python agent/train.py
```

O melhor modelo é salvo automaticamente em `agent/model/best_model/`.

---

## Limitações conhecidas

- O tanque de H2 é uma abstração — não modela compressão ou armazenamento criogênico
- O eletrolisador não tem estado térmico acumulado — na vida real limita operação contínua no limite
- Modelo treinado com dados simulados; em produção usaria dados históricos reais

---

## Licença

MIT — veja [LICENSE](LICENSE)
