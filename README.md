# Torneio – Amigos do Tennis

App Streamlit para gerenciar um mini-campeonato de tênis entre 10 participantes.

## Como rodar localmente

1. Clone:
   ```
   git clone https://github.com/SEU_USUARIO/amigos-tennis.git
   cd amigos-tennis
   ```
2. (Opcional) Crie e ative venv:
   ```
   python3 -m venv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate   # Windows
   ```
3. Instale dependências:
   ```
   pip install -r requirements.txt
   ```
4. Execute:
   ```
   streamlit run app.py
   ```
   Acesse em http://localhost:8501

## Deploy no Streamlit Community Cloud

1. Faça push no GitHub.  
2. Em https://streamlit.io/cloud → **New app** → selecione este repositório e o `app.py`.  
3. Clique em **Deploy**.

## Estrutura
```
.
├─ app.py
├─ requirements.txt
├─ README.md
└─ .gitignore
```
